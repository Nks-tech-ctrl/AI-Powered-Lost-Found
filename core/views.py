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
