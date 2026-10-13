from django.shortcuts import render
from items.models import Item


def home(request):
    recent_items = Item.objects.filter(
        status=Item.ItemStatus.ACTIVE,
        is_hidden=False,
        moderation_status=Item.ModerationStatus.APPROVED
    ).order_by('-created_at')[:6]
    lost_count = Item.objects.filter(
        item_type=Item.ItemType.LOST,
        status=Item.ItemStatus.ACTIVE,
        is_hidden=False,
        moderation_status=Item.ModerationStatus.APPROVED
    ).count()
    found_count = Item.objects.filter(
        item_type=Item.ItemType.FOUND,
        status=Item.ItemStatus.ACTIVE,
        is_hidden=False,
        moderation_status=Item.ModerationStatus.APPROVED
    ).count()
    context = {
        'recent_items': recent_items,
        'lost_count': lost_count,
        'found_count': found_count,
        'categories': Item.ItemCategory.choices,
    }
    return render(request, 'core/index.html', context)


# ==============================================================================
# Custom Error Page Handlers
# ==============================================================================

def custom_404_view(request, exception=None):
    """
    Renders modern, branded 404 Page Not Found error page.
    """
    context = {
        'error_code': '404',
        'error_title': 'Report or Page Not Found',
        'error_message': 'The report, item, or page you are looking for is no longer available. It may have been resolved, deleted, or the address is mistyped.',
        'exception': str(exception) if exception else None,
    }
    return render(request, '404.html', context, status=404)


def custom_500_view(request):
    """
    Renders resilient 500 Internal Server Error page without assuming working context processors.
    """
    context = {
        'error_code': '500',
        'error_title': 'Unexpected Server Error',
        'error_message': 'Our system encountered an unexpected condition while processing your request. Our automated monitors have logged this incident.',
    }
    return render(request, '500.html', context, status=500)


def custom_403_view(request, exception=None):
    """
    Renders 403 Permission Denied / Forbidden error page.
    """
    context = {
        'error_code': '403',
        'error_title': 'Access Restricted',
        'error_message': 'You do not have authorization to view, modify, or delete this resource.',
        'exception': str(exception) if exception else None,
    }
    return render(request, '403.html', context, status=403)


def custom_400_view(request, exception=None):
    """
    Renders 400 Bad Request error page.
    """
    context = {
        'error_code': '400',
        'error_title': 'Bad Request',
        'error_message': 'The server could not understand or validate your request parameters.',
        'exception': str(exception) if exception else None,
    }
    return render(request, '400.html', context, status=400)


# Development previews
def preview_404(request):
    return custom_404_view(request)

def preview_500(request):
    return custom_500_view(request)

def preview_403(request):
    return custom_403_view(request)

def preview_400(request):
    return custom_400_view(request)
