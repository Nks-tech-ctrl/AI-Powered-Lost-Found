from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Notification


@login_required
def notifications_list(request):
    """
    Renders the notifications center for the authenticated user.
    Displays title, message, timestamp, read status, and links to related items/claims.
    Supports filtering by read/unread status and pagination.
    """
    filter_status = request.GET.get('status', 'all').lower().strip()
    user_notifications = Notification.objects.filter(recipient=request.user).select_related('item', 'claim')

    if filter_status == 'unread':
        notifications_qs = user_notifications.filter(is_read=False)
    elif filter_status == 'read':
        notifications_qs = user_notifications.filter(is_read=True)
    else:
        notifications_qs = user_notifications
        filter_status = 'all'

    total_count = user_notifications.count()
    unread_count = user_notifications.filter(is_read=False).count()
    read_count = user_notifications.filter(is_read=True).count()

    paginator = Paginator(notifications_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'filter_status': filter_status,
        'total_count': total_count,
        'unread_count': unread_count,
        'read_count': read_count,
    }
    return render(request, 'notifications/notifications.html', context)


@login_required
def mark_as_read(request, pk):
    """
    Marks a single notification belonging to the current user as read.
    Requires POST method.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('notifications')

    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.mark_as_read()
    messages.success(request, "Notification marked as read.")

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('notifications')


@login_required
def mark_all_read(request):
    """
    Marks all unread notifications of the current user as read.
    Requires POST method.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('notifications')

    now = timezone.now()
    updated_count = request.user.notifications.filter(is_read=False).update(
        is_read=True,
        read_at=now
    )
    if updated_count > 0:
        messages.success(request, f"Marked {updated_count} notification(s) as read.")
    else:
        messages.info(request, "No unread notifications to mark.")

    return redirect('notifications')


@login_required
def delete_notification(request, pk):
    """
    Deletes a single notification belonging to the current user.
    Requires POST method.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('notifications')

    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.delete()
    messages.success(request, "Notification deleted.")

    return redirect('notifications')
