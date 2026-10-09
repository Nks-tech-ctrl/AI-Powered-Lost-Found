import os
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Item
from .forms import ItemForm


@login_required
def dashboard_view(request):
    """
    Renders the authenticated user's personal dashboard with live reports, real counts, and quick actions.
    """
    user_items = Item.objects.filter(user=request.user).order_by('-created_at')
    total_reports = user_items.count()
    lost_reports = user_items.filter(item_type=Item.ItemType.LOST).count()
    found_reports = user_items.filter(item_type=Item.ItemType.FOUND).count()
    active_reports = user_items.filter(status=Item.ItemStatus.ACTIVE).count()
    recent_items = user_items[:5]

    from claims.models import Claim
    my_claims_pending = Claim.objects.filter(claimant=request.user, status=Claim.Status.PENDING).count()
    my_claims_approved = Claim.objects.filter(claimant=request.user, status=Claim.Status.APPROVED).count()
    my_claims_rejected = Claim.objects.filter(claimant=request.user, status=Claim.Status.REJECTED).count()
    my_claims_total = Claim.objects.filter(claimant=request.user).count()

    claims_to_review_pending = Claim.objects.filter(item__user=request.user, status=Claim.Status.PENDING).count()
    claims_to_review_total = Claim.objects.filter(item__user=request.user).count()

    from notifications.models import Notification
    user_notifications = Notification.objects.filter(recipient=request.user)
    unread_notifications_count = user_notifications.filter(is_read=False).count()
    latest_notifications = user_notifications.order_by('-created_at')[:3]

    context = {
        'user_items': user_items,
        'recent_items': recent_items,
        'items': recent_items,  # Backwards compatibility
        'total_reports': total_reports,
        'lost_reports': lost_reports,
        'found_reports': found_reports,
        'active_reports': active_reports,
        # Backwards compatibility keys
        'total_count': total_reports,
        'lost_count': lost_reports,
        'found_count': found_reports,
        'active_count': active_reports,
        # Claims counts
        'my_claims_pending': my_claims_pending,
        'my_claims_approved': my_claims_approved,
        'my_claims_rejected': my_claims_rejected,
        'my_claims_total': my_claims_total,
        'claims_to_review_pending': claims_to_review_pending,
        'claims_to_review_total': claims_to_review_total,
        # Notification counts & records
        'unread_notifications_count': unread_notifications_count,
        'latest_notifications': latest_notifications,
    }
    return render(request, 'items/dashboard.html', context)


dashboard = dashboard_view


@login_required
def my_reports(request):
    """
    Displays all items reported by the logged-in user with type filtering (all, lost, found).
    """
    filter_type = request.GET.get('type', 'all').lower().strip()
    if filter_type not in ['all', 'lost', 'found']:
        filter_type = 'all'

    user_items = Item.objects.filter(user=request.user).order_by('-created_at')

    if filter_type == 'lost':
        items = user_items.filter(item_type=Item.ItemType.LOST)
    elif filter_type == 'found':
        items = user_items.filter(item_type=Item.ItemType.FOUND)
    else:
        items = user_items

    total_count = user_items.count()
    lost_count = user_items.filter(item_type=Item.ItemType.LOST).count()
    found_count = user_items.filter(item_type=Item.ItemType.FOUND).count()

    context = {
        'items': items,
        'filter_type': filter_type,
        'total_count': total_count,
        'lost_count': lost_count,
        'found_count': found_count,
    }
    return render(request, 'items/my-reports.html', context)


@login_required
def item_detail(request, pk=None, id=None):
    """
    Displays the details of a single item report owned by the authenticated user.
    Prevents IDOR by strictly requiring user=request.user.
    """
    pk = pk or id
    item = get_object_or_404(Item, pk=pk, user=request.user)
    return render(request, 'items/item-details.html', {'item': item})


@login_required
def item_edit(request, pk):
    """
    Allows the owner to edit their own item report.
    Item type, status, and owner cannot be altered.
    Safely handles image replacement and removal.
    """
    item = get_object_or_404(Item, pk=pk, user=request.user)
    original_item_type = item.item_type
    original_status = item.status
    old_image = item.image

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        remove_image = request.POST.get('remove_image') == '1'

        if form.is_valid():
            updated_item = form.save(commit=False)

            # Strict server-side security: locked fields cannot be altered
            updated_item.user = request.user
            updated_item.item_type = original_item_type
            updated_item.status = original_status

            # Handle explicit image removal
            if remove_image and not request.FILES.get('image'):
                if old_image:
                    try:
                        old_image.delete(save=False)
                    except Exception:
                        pass
                updated_item.image = None
            elif request.FILES.get('image'):
                # New image uploaded: remove previous image file if it exists and differs
                if old_image and old_image != updated_item.image:
                    try:
                        old_image.delete(save=False)
                    except Exception:
                        pass

            updated_item.save()
            form.save_m2m()

            messages.success(
                request,
                "Your item report has been updated successfully."
            )
            return redirect('item-detail', pk=updated_item.pk)
    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
    }
    return render(request, 'items/item-edit.html', context)


@login_required
def item_delete(request, pk):
    """
    Deletes an item report owned by the authenticated user.
    Requires POST to execute deletion; GET displays confirmation UI.
    Cleans up associated media image safely.
    """
    item = get_object_or_404(Item, pk=pk, user=request.user)

    if request.method == 'POST':
        # Safely clean up associated image file if it exists
        if item.image:
            try:
                item.image.delete(save=False)
            except Exception:
                pass

        item.delete()
        messages.success(request, "Your item report has been deleted.")
        return redirect('my-reports')

    return render(request, 'items/item-delete.html', {'item': item})


@login_required
def report_lost(request):
    """
    Handles submitting a new LOST item report.
    Validates data, assigns current user, sets item_type to LOST and status to ACTIVE.
    """
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.item_type = Item.ItemType.LOST
            item.status = Item.ItemStatus.ACTIVE
            item.save()
            form.save_m2m()
            messages.success(
                request,
                "Your lost item report has been submitted successfully."
            )
            return redirect('dashboard')
    else:
        form = ItemForm()

    return render(
        request,
        'items/report-lost.html',
        {
            'form': form,
            'report_type': 'lost',
        }
    )


@login_required
def report_found(request):
    """
    Handles submitting a new FOUND item report.
    Validates data, assigns current user, sets item_type to FOUND and status to ACTIVE.
    """
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.item_type = Item.ItemType.FOUND
            item.status = Item.ItemStatus.ACTIVE
            item.save()
            form.save_m2m()
            messages.success(
                request,
                "Your found item report has been submitted successfully."
            )
            return redirect('dashboard')
    else:
        form = ItemForm()

    return render(
        request,
        'items/report-found.html',
        {
            'form': form,
            'report_type': 'found',
        }
    )


# Aliases for backwards compatibility with earlier routing
report_lost_view = report_lost
report_found_view = report_found


def search_view(request):
    """
    Public Lost & Found catalog browsing and search.
    Accessible to anonymous and authenticated users.
    Starts with active reports only: Item.objects.filter(status=Item.ItemStatus.ACTIVE).
    Supports:
      - Search query 'q' across title, description, brand, color, location
      - Filters: item_type (All, Lost, Found), category, location, date_from, date_to
      - Sorting: newest, oldest, recently_updated via fixed mapping
      - Pagination: 12 items per page with preserved GET parameters
    """
    items = Item.objects.filter(
        status=Item.ItemStatus.ACTIVE,
        is_hidden=False,
        moderation_status=Item.ModerationStatus.APPROVED
    ).select_related('user')

    # Search query across title, description, brand, color, location
    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(brand__icontains=query) |
            Q(color__icontains=query)
        )

    # Item Type filter (All, Lost, Found)
    item_type = request.GET.get('type', '').strip().upper()
    if item_type in [Item.ItemType.LOST, Item.ItemType.FOUND]:
        items = items.filter(item_type=item_type)
    else:
        item_type = ''

    # Category filter
    category = request.GET.get('category', '').strip()
    if category and category.lower() != 'all':
        matching_cat = None
        for cat_val, cat_label in Item.ItemCategory.choices:
            if category.upper() == cat_val.upper() or category.lower() == cat_label.lower():
                matching_cat = cat_val
                break
        if matching_cat:
            items = items.filter(category=matching_cat)

    # Location filter
    location = request.GET.get('location', '').strip()
    if location:
        items = items.filter(location__icontains=location)

    # Date from filter
    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        try:
            parsed_date_from = datetime.date.fromisoformat(date_from)
            items = items.filter(date_occurred__gte=parsed_date_from)
        except ValueError:
            date_from = ''

    # Date to filter
    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        try:
            parsed_date_to = datetime.date.fromisoformat(date_to)
            items = items.filter(date_occurred__lte=parsed_date_to)
        except ValueError:
            date_to = ''

    # Sorting with fixed mapping (never pass arbitrary user-provided ordering)
    sort_param = request.GET.get('sort', 'newest').strip().lower()
    SORT_MAPPING = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'recently_updated': '-updated_at',
        'recent': '-created_at',
        'name': 'title',
    }
    order_field = SORT_MAPPING.get(sort_param, '-created_at')
    items = items.order_by(order_field)

    total_results = items.count()

    # Pagination: 12 items per page
    paginator = Paginator(items, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Preserve GET parameters for pagination links
    params = request.GET.copy()
    if 'page' in params:
        del params['page']
    query_string = params.urlencode()

    context = {
        'items': page_obj,
        'page_obj': page_obj,
        'query': query,
        'selected_category': category,
        'selected_type': item_type,
        'selected_location': location,
        'date_from': date_from,
        'date_to': date_to,
        'selected_sort': sort_param,
        'total_results': total_results,
        'categories': Item.ItemCategory.choices,
        'query_string': query_string,
    }
    return render(request, 'items/search.html', context)


def item_details_view(request, id=None):
    """
    Compatibility wrapper for item details routing.
    """
    requested_id = id or request.GET.get('id')
    if requested_id:
        try:
            pk = int(requested_id)
            return item_detail(request, pk)
        except (ValueError, TypeError):
            pass
    return redirect('my-reports')


def public_item_detail(request, pk):
    """
    Displays the public details of an item (LOST or FOUND).
    Never exposes identification_details or private personal data.
    Provides ownership claim action for eligible users on FOUND items.
    """
    item = get_object_or_404(Item, pk=pk)
    if item.is_hidden and (not request.user.is_authenticated or (request.user != item.user and not request.user.is_staff)):
        from django.http import Http404
        raise Http404("This item is not available.")

    user_claim = None
    has_pending_claim = False
    has_approved_claim = False
    is_owner = False

    if request.user.is_authenticated:
        from claims.models import Claim
        is_owner = (item.user == request.user)
        user_claim = Claim.objects.filter(item=item, claimant=request.user).first()
        if user_claim:
            has_pending_claim = (user_claim.status == Claim.Status.PENDING)
            has_approved_claim = (user_claim.status == Claim.Status.APPROVED)

    context = {
        'item': item,
        'is_owner': is_owner,
        'user_claim': user_claim,
        'has_pending_claim': has_pending_claim,
        'has_approved_claim': has_approved_claim,
    }
    return render(request, 'items/public-item-detail.html', context)


