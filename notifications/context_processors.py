from .models import Notification


def notifications_context(request):
    """
    Context processor providing unread notifications count and recent notifications
    to all templates for authenticated users. Returns 0 for anonymous users.
    """
    if request.user.is_authenticated:
        user_notifications = Notification.objects.filter(recipient=request.user)
        unread_count = user_notifications.filter(is_read=False).count()
        latest_notifications = user_notifications.order_by('-created_at')[:3]
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': latest_notifications,
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
