import logging
from django.contrib.auth.models import User
from django.db import transaction
from .models import Notification

logger = logging.getLogger(__name__)


def _dispatch_side_effects(recipient, notification, notification_type, title, message, item, claim):
    """
    Asynchronously or on-commit dispatches WebSocket events and email delivery.
    """
    try:
        from admin_dashboard.realtime import publish_user_event
        from admin_dashboard.models import EmailDelivery
        from admin_dashboard.email_service import send_event_email

        # 1. Real-time WebSocket event
        unread_count = Notification.objects.filter(recipient=recipient, is_read=False).count()
        event_data = {
            'notification_id': notification.id,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'unread_count': unread_count,
            'item_id': item.id if item else None,
            'claim_id': claim.id if claim else None,
        }
        publish_user_event(recipient.id, 'notification', event_data)

        # 2. Email dispatch mapping
        email_map = {
            Notification.NotificationType.CLAIM_SUBMITTED: EmailDelivery.EventType.CLAIM_SUBMITTED,
            Notification.NotificationType.CLAIM_APPROVED: EmailDelivery.EventType.CLAIM_APPROVED,
            Notification.NotificationType.CLAIM_REJECTED: EmailDelivery.EventType.CLAIM_REJECTED,
            Notification.NotificationType.CLAIM_CANCELLED: EmailDelivery.EventType.CLAIM_CANCELLED,
            Notification.NotificationType.CLAIM_SUPERSEDED: EmailDelivery.EventType.CLAIM_SUPERSEDED,
            Notification.NotificationType.ITEM_STATUS_CHANGED: EmailDelivery.EventType.REPORT_STATUS_CHANGED,
            Notification.NotificationType.MODERATION_ACTION: EmailDelivery.EventType.REPORT_MODERATED,
            Notification.NotificationType.ACCOUNT_STATUS_CHANGED: EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED,
        }
        email_event = email_map.get(notification_type, EmailDelivery.EventType.GENERAL_NOTIFICATION)

        context = {
            'item': item,
            'claim': claim,
            'title': title,
            'message': message,
        }
        send_event_email(
            recipient_user=recipient,
            event_type=email_event,
            context=context,
            subject=f"[FindBack] {title}",
            notification=notification
        )
    except Exception as e:
        logger.warning(f"Failed to dispatch notification side-effects for user {recipient.pk}: {e}")


def create_notification(recipient, notification_type, title, message, item=None, claim=None):
    """
    Creates a database-backed notification for the recipient, publishes a real-time
    WebSocket event, and triggers an email notification to the recipient.
    
    Args:
        recipient (User): The user receiving the notification.
        notification_type (str): Type from Notification.NotificationType.
        title (str): Brief title for the notification.
        message (str): Detailed descriptive message (without private sensitive details).
        item (Item, optional): Associated lost/found item.
        claim (Claim, optional): Associated claim.
        
    Returns:
        Notification: The created Notification object, or None if creation failed.
    """
    if not recipient or not isinstance(recipient, User):
        logger.warning("Attempted to create notification without a valid recipient User.")
        return None

    try:
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title[:200],
            message=message[:2000],
            item=item,
            claim=claim,
        )

        _dispatch_side_effects(recipient, notification, notification_type, title, message, item, claim)

        return notification
    except Exception as e:
        logger.error(f"Failed to create notification for user {recipient.pk}: {e}")
        return None
