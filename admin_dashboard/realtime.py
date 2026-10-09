import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def _send_user_event_now(user_id, event_type, data):
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        group_name = f"user_{user_id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'user_event',
                'event_type': event_type,
                'data': data or {},
                'timestamp': timezone.now().isoformat(),
            }
        )
    except Exception as e:
        logger.warning(f"Failed to publish user event to {user_id}: {e}")


def _send_admin_event_now(event_type, data):
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            "admin_updates",
            {
                'type': 'admin_event',
                'event_type': event_type,
                'data': data or {},
                'timestamp': timezone.now().isoformat(),
            }
        )
    except Exception as e:
        logger.warning(f"Failed to publish admin broadcast: {e}")


def publish_user_event(user_id, event_type, data=None):
    """
    Safely publishes an event to a specific user's WebSocket group.
    Executes on_commit if inside a database transaction to prevent dirty events.
    """
    if not user_id:
        return
    try:
        connection = transaction.get_connection()
        if connection.in_atomic_block:
            transaction.on_commit(lambda: _send_user_event_now(user_id, event_type, data))
        else:
            _send_user_event_now(user_id, event_type, data)
    except Exception:
        _send_user_event_now(user_id, event_type, data)


def publish_admin_event(event_type, data=None):
    """
    Safely publishes an event to the staff/admin WebSocket group.
    Executes on_commit if inside a database transaction.
    """
    try:
        connection = transaction.get_connection()
        if connection.in_atomic_block:
            transaction.on_commit(lambda: _send_admin_event_now(event_type, data))
        else:
            _send_admin_event_now(event_type, data)
    except Exception:
        _send_admin_event_now(event_type, data)
