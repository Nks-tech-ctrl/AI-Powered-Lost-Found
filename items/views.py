from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Item
from .forms import ItemForm


@login_required
def dashboard_view(request):
    """
    Renders the authenticated user's personal dashboard with live reports.
    """
    user_items = request.user.items.all().order_by('-created_at')
    active_count = user_items.filter(status=Item.ItemStatus.ACTIVE).count()
    lost_count = user_items.filter(item_type=Item.ItemType.LOST).count()
    found_count = user_items.filter(item_type=Item.ItemType.FOUND).count()
    recovered_count = user_items.filter(status=Item.ItemStatus.RETURNED).count()

    context = {
        'items': user_items,
        'active_count': active_count,
        'total_count': user_items.count(),
        'lost_count': lost_count,
        'found_count': found_count,
        'recovered_count': recovered_count,
    }
    return render(request, 'items/dashboard.html', context)


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
    Renders the Lost & Found search catalog with filter and query support.
    Queries real items from the database.
    """
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    item_type = request.GET.get('type', '').strip().upper()

    items = Item.objects.select_related('user').all().order_by('-created_at')

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(brand__icontains=query) |
            Q(color__icontains=query)
        )

    if category and category != 'all':
        items = items.filter(category=category)

    if item_type in [Item.ItemType.LOST, Item.ItemType.FOUND]:
        items = items.filter(item_type=item_type)

    context = {
        'items': items,
        'query': query,
        'selected_category': category,
        'selected_type': item_type,
        'total_results': items.count(),
        'categories': Item.ItemCategory.choices,
    }
    return render(request, 'items/search.html', context)


def item_details_view(request, id=None):
    """
    Renders detailed information for a specific item report.
    Retrieves item by ID or falls back to latest item if no ID specified.
    """
    item = None
    requested_id = id or request.GET.get('id')

    if requested_id:
        try:
            item = Item.objects.select_related('user').get(pk=requested_id)
        except (Item.DoesNotExist, ValueError):
            item = None
    else:
        # Fallback only when no specific ID was requested
        if request.user.is_authenticated:
            item = request.user.items.order_by('-created_at').first()
        if not item:
            item = Item.objects.order_by('-created_at').first()

    return render(request, 'items/item-details.html', {
        'item': item,
        'item_id': requested_id or (item.id if item else None),
    })
