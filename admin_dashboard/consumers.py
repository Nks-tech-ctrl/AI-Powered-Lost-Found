import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class LiveUpdatesConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer providing real-time events to authenticated clients.
    - Each user joins their private user group (user_{id})
    - Authorized staff members additionally join the admin_updates group
    - Anonymous connections are rejected
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.info("Rejecting unauthenticated WebSocket connection attempt.")
            await self.close(code=4001)
            return

        self.user_group = f"user_{user.id}"
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        self.is_staff = user.is_staff or user.is_superuser
        if self.is_staff:
            await self.channel_layer.group_add("admin_updates", self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected for user {user.username} (ID: {user.id})")

        # Send initial confirmation
        await self.send_json({
            'type': 'connected',
            'message': 'Connected to FindBack real-time event stream.',
            'user_id': user.id,
            'is_staff': self.is_staff,
        })

    async def disconnect(self, close_code):
        user = self.scope.get('user')
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if getattr(self, 'is_staff', False):
            await self.channel_layer.group_discard("admin_updates", self.channel_name)
        logger.info(f"WebSocket disconnected with code {close_code}")

    async def receive_json(self, content):
        """Handles inbound client messages, such as heartbeat ping."""
        msg_type = content.get('type')
        if msg_type == 'ping':
            await self.send_json({'type': 'pong'})

    async def user_event(self, event):
        """Dispatches an event specifically addressed to this user."""
        await self.send_json({
            'type': event.get('event_type', 'update'),
            'data': event.get('data', {}),
            'timestamp': event.get('timestamp'),
        })

    async def admin_event(self, event):
        """Dispatches an administrative broadcast event."""
        if getattr(self, 'is_staff', False):
            await self.send_json({
                'type': event.get('event_type', 'admin_update'),
                'data': event.get('data', {}),
                'timestamp': event.get('timestamp'),
            })
