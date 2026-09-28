from django.shortcuts import render
from items.models import Item


def home(request):
    recent_items = Item.objects.filter(status=Item.ItemStatus.ACTIVE).order_by('-created_at')[:6]
    lost_count = Item.objects.filter(item_type=Item.ItemType.LOST, status=Item.ItemStatus.ACTIVE).count()
    found_count = Item.objects.filter(item_type=Item.ItemType.FOUND, status=Item.ItemStatus.ACTIVE).count()
    context = {
        'recent_items': recent_items,
        'lost_count': lost_count,
        'found_count': found_count,
    }
    return render(request, 'core/index.html', context)
