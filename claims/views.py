from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.utils import timezone

from items.models import Item
from .models import Claim
from .forms import ClaimForm, RejectClaimForm


@login_required
def my_claims(request):
    """
    Renders the claims submitted by the current authenticated user.
    """
    filter_status = request.GET.get('status', 'all').upper().strip()

    all_user_claims = Claim.objects.filter(claimant=request.user).select_related('item').order_by('-created_at')

    if filter_status in Claim.Status.values:
        claims = all_user_claims.filter(status=filter_status)
    else:
        claims = all_user_claims
        filter_status = 'ALL'

    counts = {
        'all': all_user_claims.count(),
        'pending': all_user_claims.filter(status=Claim.Status.PENDING).count(),
        'approved': all_user_claims.filter(status=Claim.Status.APPROVED).count(),
        'rejected': all_user_claims.filter(status=Claim.Status.REJECTED).count(),
        'cancelled': all_user_claims.filter(status=Claim.Status.CANCELLED).count(),
    }

    context = {
        'claims': claims,
        'filter_status': filter_status,
        'counts': counts,
    }
    return render(request, 'claims/my-claims.html', context)


# Compatibility alias
claims_view = my_claims


@login_required
def submit_claim(request, pk):
    """
    Handles submission of an ownership claim for a public FOUND item.
    Only active FOUND items not reported by the claimant can be claimed.
    Prevents duplicate pending claims.
    """
    item = get_object_or_404(Item, pk=pk)

    # Validation: Must only claim FOUND items
    if item.item_type != Item.ItemType.FOUND:
        messages.error(request, "Ownership claims can only be submitted for found items.")
        return redirect('search')

    # Validation: Must only claim ACTIVE items
    if item.status != Item.ItemStatus.ACTIVE:
        messages.error(request, "This item is no longer active and cannot be claimed.")
        return redirect('search')

    # Validation: Must not claim their own item
    if item.user == request.user:
        messages.error(request, "You cannot submit an ownership claim for an item you reported yourself.")
        return redirect('public-item-detail', pk=item.pk)

    # Validation: Must not create duplicate pending claim
    if Claim.objects.filter(item=item, claimant=request.user, status=Claim.Status.PENDING).exists():
        messages.warning(request, "You already have a pending claim for this item.")
        return redirect('my-claims')

    # Check if already approved
    if Claim.objects.filter(item=item, claimant=request.user, status=Claim.Status.APPROVED).exists():
        messages.info(request, "Your claim for this item has already been approved.")
        return redirect('my-claims')

    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Re-verify item status and absence of duplicate pending claim under lock
                    current_item = Item.objects.select_for_update().get(pk=item.pk)
                    if current_item.status != Item.ItemStatus.ACTIVE or current_item.item_type != Item.ItemType.FOUND:
                        messages.error(request, "This item is no longer active or cannot be claimed.")
                        return redirect('search')

                    if Claim.objects.filter(item=current_item, claimant=request.user, status=Claim.Status.PENDING).exists():
                        messages.warning(request, "You already have a pending claim for this item.")
                        return redirect('my-claims')

                    claim = form.save(commit=False)
                    claim.item = current_item
                    claim.claimant = request.user
                    claim.status = Claim.Status.PENDING
                    claim.save()

                messages.success(request, "Your claim has been submitted and is waiting for verification.")
                return redirect('my-claims')
            except Exception:
                messages.error(request, "Could not submit claim. A pending claim may already exist.")
                return redirect('my-claims')
    else:
        form = ClaimForm()

    context = {
        'item': item,
        'form': form,
    }
    return render(request, 'claims/submit-claim.html', context)


@login_required
def claims_to_review(request):
    """
    Displays claims submitted against items reported by the current user.
    Ordered by pending first, then newest first.
    """
    filter_status = request.GET.get('status', 'all').upper().strip()

    all_claims = Claim.objects.filter(item__user=request.user).select_related('item', 'claimant').order_by(
        models.Case(
            models.When(status=Claim.Status.PENDING, then=0),
            default=1
        ),
        '-created_at'
    )

    if filter_status in Claim.Status.values:
        claims = all_claims.filter(status=filter_status)
    else:
        claims = all_claims
        filter_status = 'ALL'

    counts = {
        'all': all_claims.count(),
        'pending': all_claims.filter(status=Claim.Status.PENDING).count(),
        'approved': all_claims.filter(status=Claim.Status.APPROVED).count(),
        'rejected': all_claims.filter(status=Claim.Status.REJECTED).count(),
    }

    context = {
        'claims': claims,
        'filter_status': filter_status,
        'counts': counts,
    }
    return render(request, 'claims/claims-to-review.html', context)


@login_required
def admin_claims_list(request):
    """
    Staff-only moderation dashboard to review and manage all platform ownership claims.
    Accessible only to staff/superusers directly on the website (without Django /admin/).
    """
    if not request.user.is_staff:
        messages.error(request, "Access restricted to administrators.")
        return redirect('dashboard')

    filter_status = request.GET.get('status', 'all').upper().strip()
    search_query = request.GET.get('q', '').strip()

    all_claims = Claim.objects.select_related('item', 'claimant', 'item__user', 'reviewed_by').order_by(
        models.Case(
            models.When(status=Claim.Status.PENDING, then=0),
            default=1
        ),
        '-created_at'
    )

    if search_query:
        all_claims = all_claims.filter(
            models.Q(item__title__icontains=search_query) |
            models.Q(claimant__username__icontains=search_query) |
            models.Q(claimant__email__icontains=search_query) |
            models.Q(item__user__username__icontains=search_query)
        )

    if filter_status in Claim.Status.values:
        claims = all_claims.filter(status=filter_status)
    else:
        claims = all_claims
        filter_status = 'ALL'

    base_unfiltered = Claim.objects.all()
    counts = {
        'all': base_unfiltered.count(),
        'pending': base_unfiltered.filter(status=Claim.Status.PENDING).count(),
        'approved': base_unfiltered.filter(status=Claim.Status.APPROVED).count(),
        'rejected': base_unfiltered.filter(status=Claim.Status.REJECTED).count(),
        'cancelled': base_unfiltered.filter(status=Claim.Status.CANCELLED).count(),
    }

    context = {
        'claims': claims,
        'filter_status': filter_status,
        'search_query': search_query,
        'counts': counts,
    }
    return render(request, 'claims/admin-claims.html', context)


@login_required
def review_claim(request, pk):
    """
    Allows the reporter of a FOUND item or a site administrator to review an individual claim.
    """
    claim = get_object_or_404(Claim.objects.select_related('item', 'claimant', 'item__user', 'reviewed_by'), pk=pk)

    # Only reporter/owner of the item OR a staff/admin user may access this review page
    if claim.item.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to review this claim.")
        return redirect('claims-to-review')

    reject_form = RejectClaimForm()

    context = {
        'claim': claim,
        'item': claim.item,
        'reject_form': reject_form,
        'is_admin_reviewer': request.user.is_staff and claim.item.user != request.user,
    }
    return render(request, 'claims/review-claim.html', context)


@login_required
def approve_claim(request, pk):
    """
    Approves a pending claim for an active FOUND item.
    Atomically:
    1. Sets claim to APPROVED with reviewer and timestamp
    2. Rejects any other PENDING claims for this item
    3. Changes item status to CLAIMED
    Strictly requires POST and reporter/admin authorization.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('review-claim', pk=pk)

    claim = get_object_or_404(Claim.objects.select_related('item'), pk=pk)

    # Security check: Only the reporter or staff/admin can approve
    if claim.item.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to review this claim.")
        return redirect('claims-to-review')

    # State check: Only PENDING claims can be approved
    if claim.status != Claim.Status.PENDING:
        messages.error(request, "This claim can no longer be processed.")
        return redirect('review-claim', pk=claim.pk)

    # Item check: Only ACTIVE FOUND items can be approved
    if claim.item.item_type != Item.ItemType.FOUND or claim.item.status != Item.ItemStatus.ACTIVE:
        messages.error(request, "This item is not active or cannot be claimed.")
        return redirect('review-claim', pk=claim.pk)

    is_admin = request.user.is_staff and claim.item.user != request.user

    with transaction.atomic():
        item = Item.objects.select_for_update().get(pk=claim.item.pk)
        if item.status != Item.ItemStatus.ACTIVE or item.item_type != Item.ItemType.FOUND:
            messages.error(request, "This item has already been claimed or is no longer active.")
            return redirect('review-claim', pk=claim.pk)

        c = Claim.objects.select_for_update().get(pk=claim.pk)
        if c.status != Claim.Status.PENDING:
            messages.error(request, "This claim can no longer be processed.")
            return redirect('review-claim', pk=claim.pk)

        now = timezone.now()

        # 1. Approve selected claim
        c.status = Claim.Status.APPROVED
        c.reviewed_by = request.user
        c.reviewed_at = now
        c.save()

        # 2. Reject other pending claims for this item
        rejection_note = (
            "Another ownership claim was approved for this item by site administration."
            if is_admin
            else "Another ownership claim was approved for this item."
        )
        Claim.objects.filter(
            item=item,
            status=Claim.Status.PENDING
        ).exclude(pk=c.pk).update(
            status=Claim.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=now,
            reviewer_note=rejection_note
        )

        # 3. Update item status to CLAIMED
        item.status = Item.ItemStatus.CLAIMED
        item.save()

    success_msg = "Claim approved successfully as administrator." if is_admin else "Claim approved successfully."
    messages.success(request, success_msg)
    return redirect('review-claim', pk=claim.pk)


@login_required
def reject_claim(request, pk):
    """
    Rejects a pending claim.
    Item remains ACTIVE.
    Strictly requires POST and reporter/admin authorization.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('review-claim', pk=pk)

    claim = get_object_or_404(Claim.objects.select_related('item'), pk=pk)

    # Security check: Only the reporter or staff/admin can reject
    if claim.item.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to review this claim.")
        return redirect('claims-to-review')

    # State check: Only PENDING claims can be rejected
    if claim.status != Claim.Status.PENDING:
        messages.error(request, "This claim can no longer be processed.")
        return redirect('review-claim', pk=claim.pk)

    is_admin = request.user.is_staff and claim.item.user != request.user
    reviewer_note = request.POST.get('reviewer_note', '').strip()[:2000]

    claim.status = Claim.Status.REJECTED
    claim.reviewed_by = request.user
    claim.reviewed_at = timezone.now()
    claim.reviewer_note = reviewer_note
    claim.save()

    success_msg = "Claim rejected by administrator." if is_admin else "Claim rejected."
    messages.success(request, success_msg)
    return redirect('review-claim', pk=claim.pk)



@login_required
def cancel_claim(request, pk):
    """
    Allows a claimant to cancel their own PENDING claim.
    Approved or rejected claims cannot be cancelled.
    Strictly requires POST and claimant authorization.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('my-claims')

    claim = get_object_or_404(Claim, pk=pk)

    # Security check: User must own the claim
    if claim.claimant != request.user:
        messages.error(request, "You are not allowed to cancel this claim.")
        return redirect('my-claims')

    # State check: Only PENDING claims can be cancelled
    if claim.status != Claim.Status.PENDING:
        messages.error(request, "Only pending claims can be cancelled.")
        return redirect('my-claims')

    claim.status = Claim.Status.CANCELLED
    claim.save()

    messages.success(request, "Your claim has been cancelled.")
    return redirect('my-claims')
