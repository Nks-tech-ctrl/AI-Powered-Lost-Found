import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from items.models import Item
from claims.models import Claim
from notifications.models import Notification
from notifications.services import create_notification
from .models import AuditLog, EmailDelivery
from .audit import record_audit_log
from .email_service import send_event_email
from .realtime import publish_user_event, publish_admin_event
from .permissions import admin_required, admin_permission_required, has_admin_permission
from .forms import UserStatusForm, ItemModerationForm, AdminClaimInterventionForm


@admin_required
def overview(request):
    """
    Main Administrator Dashboard Overview.
    Displays live aggregated statistics, counts, pending moderation queues,
    email metrics, and recent administrative actions with date filters.
    """
    filter_date = request.GET.get('date_range', 'all').strip().lower()
    now = timezone.now()
    date_threshold = None

    if filter_date == 'today':
        date_threshold = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_date == '7days':
        date_threshold = now - timedelta(days=7)
    elif filter_date == '30days':
        date_threshold = now - timedelta(days=30)

    # Base queries
    users_qs = User.objects.all()
    items_qs = Item.objects.all()
    claims_qs = Claim.objects.all()
    emails_qs = EmailDelivery.objects.all()

    if date_threshold:
        users_qs = users_qs.filter(date_joined__gte=date_threshold)
        items_qs = items_qs.filter(created_at__gte=date_threshold)
        claims_qs = claims_qs.filter(created_at__gte=date_threshold)
        emails_qs = emails_qs.filter(created_at__gte=date_threshold)

    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()

    # Report metrics
    total_lost = items_qs.filter(item_type=Item.ItemType.LOST).count()
    total_found = items_qs.filter(item_type=Item.ItemType.FOUND).count()
    active_items = items_qs.filter(status=Item.ItemStatus.ACTIVE).count()
    matched_items = items_qs.filter(status=Item.ItemStatus.MATCHED).count()
    claimed_items = items_qs.filter(status=Item.ItemStatus.CLAIMED).count()
    returned_items = items_qs.filter(status=Item.ItemStatus.RETURNED).count()
    closed_items = items_qs.filter(status=Item.ItemStatus.CLOSED).count()

    # Claims metrics
    pending_claims = claims_qs.filter(status=Claim.Status.PENDING).count()
    approved_claims = claims_qs.filter(status=Claim.Status.APPROVED).count()
    rejected_claims = claims_qs.filter(status=Claim.Status.REJECTED).count()

    # Moderation queue
    pending_moderation_items = Item.objects.filter(
        Q(moderation_status__in=[Item.ModerationStatus.FLAGGED, Item.ModerationStatus.PENDING_REVIEW]) |
        Q(is_hidden=True)
    ).count()

    # Email delivery statistics
    emails_total = emails_qs.count()
    emails_sent = emails_qs.filter(status=EmailDelivery.DeliveryStatus.SENT).count()
    emails_failed = emails_qs.filter(status=EmailDelivery.DeliveryStatus.FAILED).count()

    # Recent activity feeds
    recent_audits = AuditLog.objects.select_related('actor')[:8]
    recent_items = Item.objects.select_related('user')[:5]
    recent_claims = Claim.objects.select_related('item', 'claimant')[:5]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'total_lost': total_lost,
        'total_found': total_found,
        'active_items': active_items,
        'matched_items': matched_items,
        'claimed_items': claimed_items,
        'returned_items': returned_items,
        'closed_items': closed_items,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'rejected_claims': rejected_claims,
        'pending_moderation_items': pending_moderation_items,
        'emails_total': emails_total,
        'emails_sent': emails_sent,
        'emails_failed': emails_failed,
        'recent_audits': recent_audits,
        'recent_items': recent_items,
        'recent_claims': recent_claims,
        'filter_date': filter_date,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@admin_required
def users_list(request):
    """
    Search and filter registered users.
    """
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip().lower()
    status_filter = request.GET.get('status', '').strip().lower()

    users = User.objects.select_related('profile').order_by('-date_joined')

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'regular':
        users = users.filter(is_staff=False)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'query_string': params.urlencode(),
    }
    return render(request, 'admin_dashboard/users.html', context)


@admin_required
def user_detail(request, pk):
    """
    Detailed profile, item reports, submitted claims, and audit history for a user.
    Enforces safe deactivation/activation with mandatory reason.
    """
    target_user = get_object_or_404(User.objects.select_related('profile'), pk=pk)

    user_items = Item.objects.filter(user=target_user).order_by('-created_at')[:10]
    user_claims = Claim.objects.filter(claimant=target_user).select_related('item').order_by('-created_at')[:10]
    user_audits = AuditLog.objects.filter(
        target_model__iexact='user',
        target_object_id=str(target_user.pk)
    ).select_related('actor')[:10]

    form = UserStatusForm()

    if request.method == 'POST' and 'toggle_status' in request.POST:
        if not has_admin_permission(request.user, 'manage_users'):
            raise HttpResponseForbidden("You do not have permission to manage user accounts.")

        form = UserStatusForm(request.POST)
        if form.is_valid():
            if target_user == request.user:
                messages.error(request, "Security violation: Administrators cannot deactivate their own accounts.")
                return redirect('admin_dashboard:user-detail', pk=pk)

            reason = form.cleaned_data['reason']
            previous_state = {'is_active': target_user.is_active}
            new_is_active = not target_user.is_active

            with transaction.atomic():
                target_user.is_active = new_is_active
                target_user.save(update_fields=['is_active'])

                action_type = AuditLog.ActionType.USER_ACTIVATED if new_is_active else AuditLog.ActionType.USER_DEACTIVATED
                record_audit_log(
                    actor=request.user,
                    action_type=action_type,
                    target=target_user,
                    reason=reason,
                    previous_state=previous_state,
                    new_state={'is_active': new_is_active},
                    request=request
                )

                # Send in-app notification & security email
                notif_msg = f"Your account status has been updated to {'Active' if new_is_active else 'Suspended'}. Reason: {reason}"
                create_notification(
                    recipient=target_user,
                    notification_type=Notification.NotificationType.ACCOUNT_STATUS_CHANGED,
                    title="Account Status Update",
                    message=notif_msg
                )

                # Broadcast real-time event to user
                publish_user_event(target_user.id, 'account_status', {
                    'is_active': new_is_active,
                    'message': notif_msg
                })

            status_text = "activated" if new_is_active else "deactivated"
            messages.success(request, f"User {target_user.username} was successfully {status_text}.")
            return redirect('admin_dashboard:user-detail', pk=pk)

    context = {
        'target_user': target_user,
        'user_items': user_items,
        'user_claims': user_claims,
        'user_audits': user_audits,
        'form': form,
    }
    return render(request, 'admin_dashboard/user-detail.html', context)


@admin_required
def items_list(request):
    """
    Search, filter, and inspect all reported items across the platform.
    """
    query = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', '').strip().upper()
    status_filter = request.GET.get('status', '').strip().upper()
    mod_filter = request.GET.get('moderation', '').strip().upper()
    hidden_filter = request.GET.get('hidden', '').strip().lower()

    items = Item.objects.select_related('user').order_by('-created_at')

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(id__iexact=query)
        )

    if type_filter in [Item.ItemType.LOST, Item.ItemType.FOUND]:
        items = items.filter(item_type=type_filter)

    if status_filter in [c[0] for c in Item.ItemStatus.choices]:
        items = items.filter(status=status_filter)

    if mod_filter in [c[0] for c in Item.ModerationStatus.choices]:
        items = items.filter(moderation_status=mod_filter)

    if hidden_filter == 'true':
        items = items.filter(is_hidden=True)
    elif hidden_filter == 'false':
        items = items.filter(is_hidden=False)

    paginator = Paginator(items, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'query': query,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'mod_filter': mod_filter,
        'hidden_filter': hidden_filter,
        'query_string': params.urlencode(),
        'item_types': Item.ItemType.choices,
        'item_statuses': Item.ItemStatus.choices,
        'mod_statuses': Item.ModerationStatus.choices,
    }
    return render(request, 'admin_dashboard/items.html', context)


@admin_required
def item_detail(request, pk):
    """
    Detailed inspection of an item report, claims submitted on it, and moderation controls.
    """
    item = get_object_or_404(Item.objects.select_related('user'), pk=pk)
    claims = Claim.objects.filter(item=item).select_related('claimant').order_by('-created_at')
    audits = AuditLog.objects.filter(
        target_model__iexact='item',
        target_object_id=str(item.pk)
    ).select_related('actor')[:10]

    form = ItemModerationForm(initial={
        'moderation_status': item.moderation_status,
        'is_hidden': item.is_hidden,
        'moderation_notes': item.moderation_notes,
    })

    if request.method == 'POST' and 'update_moderation' in request.POST:
        if not has_admin_permission(request.user, 'moderate_items'):
            raise HttpResponseForbidden("You do not have permission to moderate item reports.")

        form = ItemModerationForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['moderation_status']
            new_hidden = form.cleaned_data['is_hidden']
            reason = form.cleaned_data['reason']
            notes = form.cleaned_data['moderation_notes']

            prev_state = {
                'moderation_status': item.moderation_status,
                'is_hidden': item.is_hidden,
            }

            with transaction.atomic():
                item.moderation_status = new_status
                item.is_hidden = new_hidden
                item.moderation_notes = notes
                item.moderated_by = request.user
                item.moderated_at = timezone.now()
                item.save(update_fields=['moderation_status', 'is_hidden', 'moderation_notes', 'moderated_by', 'moderated_at'])

                record_audit_log(
                    actor=request.user,
                    action_type=AuditLog.ActionType.ITEM_MODERATED,
                    target=item,
                    reason=reason,
                    previous_state=prev_state,
                    new_state={'moderation_status': new_status, 'is_hidden': new_hidden},
                    request=request
                )

                # If visibility changed or item was rejected/flagged, notify report owner
                if prev_state['is_hidden'] != new_hidden or new_status in [Item.ModerationStatus.FLAGGED, Item.ModerationStatus.REJECTED]:
                    notif_msg = f"Your report '{item.title}' was reviewed by platform moderation. Status: {item.get_moderation_status_display()}. Note: {reason}"
                    create_notification(
                        recipient=item.user,
                        notification_type=Notification.NotificationType.MODERATION_ACTION,
                        title="Report Moderation Notice",
                        message=notif_msg,
                        item=item
                    )
                    publish_user_event(item.user.id, 'report_updated', {
                        'item_id': item.id,
                        'is_hidden': new_hidden,
                        'moderation_status': new_status,
                    })

            messages.success(request, f"Item report #{item.id} moderation details updated successfully.")
            return redirect('admin_dashboard:item-detail', pk=pk)

    context = {
        'item': item,
        'claims': claims,
        'audits': audits,
        'form': form,
    }
    return render(request, 'admin_dashboard/item-detail.html', context)


@admin_required
def moderation_queue(request):
    """
    Dedicated view for reports that require urgent administrative moderation.
    """
    items = Item.objects.filter(
        Q(moderation_status__in=[Item.ModerationStatus.FLAGGED, Item.ModerationStatus.PENDING_REVIEW]) |
        Q(is_hidden=True)
    ).select_related('user').order_by('-updated_at')

    paginator = Paginator(items, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_dashboard/moderation.html', {'page_obj': page_obj})


@admin_required
def claims_list(request):
    """
    Overview of community claims with status and keyword filters.
    """
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().upper()

    claims = Claim.objects.select_related('item', 'claimant', 'reviewed_by').order_by('-created_at')

    if query:
        claims = claims.filter(
            Q(claimant__username__icontains=query) |
            Q(item__title__icontains=query) |
            Q(reason__icontains=query) |
            Q(id__iexact=query)
        )

    if status_filter in [c[0] for c in Claim.Status.choices]:
        claims = claims.filter(status=status_filter)

    paginator = Paginator(claims, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'query_string': params.urlencode(),
        'claim_statuses': Claim.Status.choices,
    }
    return render(request, 'admin_dashboard/claims.html', context)


@admin_required
def claim_detail(request, pk):
    """
    Inspect claim, review proof, and perform administrative intervention if necessary.
    """
    claim = get_object_or_404(Claim.objects.select_related('item', 'claimant', 'reviewed_by', 'item__user'), pk=pk)
    item = claim.item
    audits = AuditLog.objects.filter(
        target_model__iexact='claim',
        target_object_id=str(claim.pk)
    ).select_related('actor')[:10]

    form = AdminClaimInterventionForm()

    if request.method == 'POST' and 'claim_intervention' in request.POST:
        if not has_admin_permission(request.user, 'manage_claims'):
            raise HttpResponseForbidden("You do not have permission to execute claim interventions.")

        form = AdminClaimInterventionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            reason = form.cleaned_data['reason']

            if claim.status != Claim.Status.PENDING:
                messages.error(request, f"Intervention denied: Claim is already in status {claim.get_status_display()}.")
                return redirect('admin_dashboard:claim-detail', pk=pk)

            with transaction.atomic():
                prev_claim_status = claim.status
                prev_item_status = item.status

                if action == 'APPROVE':
                    claim.status = Claim.Status.APPROVED
                    claim.reviewed_by = request.user
                    claim.reviewed_at = timezone.now()
                    claim.reviewer_note = f"[Admin Intervention] {reason}"
                    claim.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_note'])

                    # Mark item CLAIMED
                    item.status = Item.ItemStatus.CLAIMED
                    item.save(update_fields=['status'])

                    # Auto-reject other pending claims on this item
                    superseded_claims = Claim.objects.filter(
                        item=item,
                        status=Claim.Status.PENDING
                    ).exclude(pk=claim.pk)

                    superseded_count = 0
                    for sup_claim in superseded_claims:
                        sup_claim.status = Claim.Status.REJECTED
                        sup_claim.reviewed_by = request.user
                        sup_claim.reviewed_at = timezone.now()
                        sup_claim.reviewer_note = "Another claim on this item was verified and approved by administration."
                        sup_claim.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_note'])

                        create_notification(
                            recipient=sup_claim.claimant,
                            notification_type=Notification.NotificationType.CLAIM_SUPERSEDED,
                            title="Notice Regarding Your Claim",
                            message=f"Another ownership claim for '{item.title}' has been approved.",
                            item=item,
                            claim=sup_claim
                        )
                        publish_user_event(sup_claim.claimant.id, 'claim_status', {
                            'claim_id': sup_claim.id,
                            'status': 'REJECTED',
                            'item_id': item.id,
                        })
                        superseded_count += 1

                    # Notify approved claimant
                    create_notification(
                        recipient=claim.claimant,
                        notification_type=Notification.NotificationType.CLAIM_APPROVED,
                        title="Your Claim Has Been Approved by Administration",
                        message=f"Your claim for '{item.title}' was approved by platform administration.",
                        item=item,
                        claim=claim
                    )
                    publish_user_event(claim.claimant.id, 'claim_status', {
                        'claim_id': claim.id,
                        'status': 'APPROVED',
                        'item_id': item.id,
                    })

                    # Notify item reporter
                    create_notification(
                        recipient=item.user,
                        notification_type=Notification.NotificationType.ITEM_STATUS_CHANGED,
                        title="Item Claimed by Admin Intervention",
                        message=f"A claim for your found item '{item.title}' was approved by administration.",
                        item=item,
                        claim=claim
                    )

                    record_audit_log(
                        actor=request.user,
                        action_type=AuditLog.ActionType.CLAIM_APPROVED_ADMIN,
                        target=claim,
                        reason=reason,
                        previous_state={'claim_status': prev_claim_status, 'item_status': prev_item_status},
                        new_state={'claim_status': 'APPROVED', 'item_status': 'CLAIMED', 'superseded_count': superseded_count},
                        request=request
                    )
                    messages.success(request, f"Claim #{claim.id} approved by admin intervention. Item status updated to Claimed.")

                elif action == 'REJECT':
                    claim.status = Claim.Status.REJECTED
                    claim.reviewed_by = request.user
                    claim.reviewed_at = timezone.now()
                    claim.reviewer_note = f"[Admin Intervention] {reason}"
                    claim.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reviewer_note'])

                    # Notify claimant
                    create_notification(
                        recipient=claim.claimant,
                        notification_type=Notification.NotificationType.CLAIM_REJECTED,
                        title="Ownership Claim Update",
                        message=f"Your claim for '{item.title}' was reviewed and rejected by administration. Note: {reason}",
                        item=item,
                        claim=claim
                    )
                    publish_user_event(claim.claimant.id, 'claim_status', {
                        'claim_id': claim.id,
                        'status': 'REJECTED',
                        'item_id': item.id,
                    })

                    record_audit_log(
                        actor=request.user,
                        action_type=AuditLog.ActionType.CLAIM_REJECTED_ADMIN,
                        target=claim,
                        reason=reason,
                        previous_state={'claim_status': prev_claim_status},
                        new_state={'claim_status': 'REJECTED'},
                        request=request
                    )
                    messages.success(request, f"Claim #{claim.id} rejected by admin intervention.")

            return redirect('admin_dashboard:claim-detail', pk=pk)

    context = {
        'claim': claim,
        'item': item,
        'audits': audits,
        'form': form,
    }
    return render(request, 'admin_dashboard/claim-detail.html', context)


@admin_required
def notifications_overview(request):
    """
    Administrative overview of notifications across the system.
    """
    type_filter = request.GET.get('type', '').strip()
    notifications = Notification.objects.select_related('recipient', 'item').order_by('-created_at')

    if type_filter:
        notifications = notifications.filter(notification_type=type_filter)

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'notification_types': Notification.NotificationType.choices,
        'query_string': params.urlencode(),
    }
    return render(request, 'admin_dashboard/notifications.html', context)


@admin_required
def email_deliveries_list(request):
    """
    Audit and monitor email notification deliveries, status, and retry failed emails.
    """
    status_filter = request.GET.get('status', '').strip().upper()
    query = request.GET.get('q', '').strip()

    deliveries = EmailDelivery.objects.select_related('recipient_user').order_by('-created_at')

    if status_filter in [s[0] for s in EmailDelivery.DeliveryStatus.choices]:
        deliveries = deliveries.filter(status=status_filter)

    if query:
        deliveries = deliveries.filter(
            Q(recipient_email__icontains=query) |
            Q(subject__icontains=query) |
            Q(error_message__icontains=query)
        )

    # Retry single email action
    if request.method == 'POST' and 'retry_email_id' in request.POST:
        if not has_admin_permission(request.user, 'view_email_logs'):
            raise HttpResponseForbidden("Missing permission to retry email deliveries.")

        delivery_id = request.POST.get('retry_email_id')
        delivery_to_retry = get_object_or_404(EmailDelivery, pk=delivery_id)

        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            from .email_service import TEMPLATE_MAPPING

            tpl = TEMPLATE_MAPPING.get(delivery_to_retry.event_type, 'emails/notification.html')
            context = {
                'user': delivery_to_retry.recipient_user,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
                'event_type': delivery_to_retry.event_type,
            }
            html_content = render_to_string(tpl, context)
            plain_content = strip_tags(html_content)

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'FindBack <noreply@findback.local>')
            msg = EmailMultiAlternatives(
                subject=delivery_to_retry.subject,
                body=plain_content,
                from_email=from_email,
                to=[delivery_to_retry.recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            delivery_to_retry.status = EmailDelivery.DeliveryStatus.SENT
            delivery_to_retry.sent_at = timezone.now()
            delivery_to_retry.attempts += 1
            delivery_to_retry.error_message = ""
            delivery_to_retry.save(update_fields=['status', 'sent_at', 'attempts', 'error_message'])
            messages.success(request, f"Email delivery #{delivery_to_retry.id} retried and dispatched successfully.")
        except Exception as e:
            delivery_to_retry.attempts += 1
            delivery_to_retry.error_message = str(e)[:1000]
            delivery_to_retry.save(update_fields=['attempts', 'error_message'])
            messages.error(request, f"Retry failed: {e}")

        return redirect('admin_dashboard:email-deliveries-list')

    paginator = Paginator(deliveries, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'query': query,
        'statuses': EmailDelivery.DeliveryStatus.choices,
        'query_string': params.urlencode(),
    }
    return render(request, 'admin_dashboard/email-deliveries.html', context)


@admin_required
def audit_logs_list(request):
    """
    Searchable, filterable audit log ledger for all sensitive administrative actions.
    """
    action_filter = request.GET.get('action', '').strip().upper()
    query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.select_related('actor').order_by('-timestamp')

    if action_filter in [a[0] for a in AuditLog.ActionType.choices]:
        logs = logs.filter(action_type=action_filter)

    if query:
        logs = logs.filter(
            Q(actor__username__icontains=query) |
            Q(target_model__icontains=query) |
            Q(target_object_id__icontains=query) |
            Q(target_repr__icontains=query) |
            Q(reason__icontains=query)
        )

    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    params = request.GET.copy()
    if 'page' in params:
        del params['page']

    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'query': query,
        'actions': AuditLog.ActionType.choices,
        'query_string': params.urlencode(),
    }
    return render(request, 'admin_dashboard/audit-logs.html', context)


@admin_required
def settings_view(request):
    """
    Platform configurations, system metrics, and diagnostic information.
    """
    channel_layer_name = settings.CHANNEL_LAYERS.get('default', {}).get('BACKEND', 'Not Configured')

    diagnostics = {
        'django_version': settings.LANGUAGE_CODE,
        'debug_mode': settings.DEBUG,
        'email_backend': settings.EMAIL_BACKEND,
        'channel_layer': channel_layer_name,
        'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'FindBack <noreply@findback.local>'),
        'total_items': Item.objects.count(),
        'total_claims': Claim.objects.count(),
        'total_users': User.objects.count(),
        'server_time': timezone.now(),
    }
    return render(request, 'admin_dashboard/settings.html', {'diagnostics': diagnostics})


def poll_updates_api(request):
    """
    Asynchronous JSON polling endpoint for clients when WebSocket is disconnected.
    Returns current user notification count, unread flags, and basic platform state.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=401)

    unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).count()
    claims_to_review = Claim.objects.filter(item__user=request.user, status=Claim.Status.PENDING).count()
    my_pending_claims = Claim.objects.filter(claimant=request.user, status=Claim.Status.PENDING).count()

    response_data = {
        'authenticated': True,
        'user_id': request.user.id,
        'unread_notifications': unread_notifications,
        'claims_to_review': claims_to_review,
        'my_pending_claims': my_pending_claims,
        'timestamp': timezone.now().isoformat(),
    }

    if request.user.is_staff or request.user.is_superuser:
        response_data['admin'] = {
            'pending_moderation': Item.objects.filter(
                Q(moderation_status__in=[Item.ModerationStatus.FLAGGED, Item.ModerationStatus.PENDING_REVIEW]) |
                Q(is_hidden=True)
            ).count(),
            'failed_emails': EmailDelivery.objects.filter(status=EmailDelivery.DeliveryStatus.FAILED).count(),
            'pending_claims': Claim.objects.filter(status=Claim.Status.PENDING).count(),
        }

    return JsonResponse(response_data)
