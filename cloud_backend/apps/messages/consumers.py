"""
WebSocket Consumers for Real-Time Updates
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class MessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messages.

    Subscribes to a group's message channel and broadcasts:
    - New messages
    - Message updates
    - Typing indicators
    - User presence
    """

    async def connect(self):
        """Accept WebSocket connection and join group channel"""
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'messages_{self.group_id}'
        self.user = self.scope.get('user')

        # Authenticate user (from JWT middleware)
        if not self.user or not self.user.is_authenticated:
            logger.warning(f"Unauthenticated WebSocket connection attempt for group {self.group_id}")
            await self.close(code=4001)
            return

        # Check if user has access to this group
        has_access = await self.check_group_access()
        if not has_access:
            logger.warning(f"User {self.user.email} denied access to group {self.group_id}")
            await self.close(code=4003)
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'group_id': self.group_id,
            'user_id': str(self.user.id)
        }))

        # Broadcast user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_presence',
                'action': 'joined',
                'user_id': str(self.user.id),
                'user_name': self.user.name
            }
        )

        logger.info(f"User {self.user.email} connected to group {self.group_id}")

    async def disconnect(self, close_code):
        """Leave room group on disconnect"""
        if hasattr(self, 'room_group_name'):
            # Broadcast user left
            if self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_presence',
                        'action': 'left',
                        'user_id': str(self.user.id),
                        'user_name': self.user.name
                    }
                )

            # Leave group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

        logger.info(f"User disconnected from group {self.group_id} (code: {close_code})")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            # Route to appropriate handler
            if message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)

        # Broadcast typing status to group (except sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'user_name': self.user.name,
                'is_typing': is_typing
            }
        )

    # ============================================================================
    # Event Handlers (called by channel layer)
    # ============================================================================

    async def message_created(self, event):
        """Broadcast when new message is created"""
        await self.send(text_data=json.dumps({
            'type': 'message_created',
            'message': event['message']
        }))

    async def message_updated(self, event):
        """Broadcast when message is updated"""
        await self.send(text_data=json.dumps({
            'type': 'message_updated',
            'message': event['message']
        }))

    async def message_deleted(self, event):
        """Broadcast when message is deleted"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id']
        }))

    async def typing_indicator(self, event):
        """Broadcast typing indicator"""
        # Don't send typing indicator to the user who's typing
        if str(self.user.id) != event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))

    async def user_presence(self, event):
        """Broadcast user presence (joined/left)"""
        # Don't send to the user themselves
        if str(self.user.id) != event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'presence',
                'action': event['action'],
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))

    # ============================================================================
    # Helper Methods
    # ============================================================================

    @database_sync_to_async
    def check_group_access(self):
        """Check if user has access to this group"""
        from apps.groups.models import Group

        try:
            group = Group.objects.get(id=self.group_id)
            # Check if user is a member
            members = group.members if isinstance(group.members, list) else []
            return str(self.user.id) in members or self.user.is_admin()
        except Group.DoesNotExist:
            return False


class CloudSyncConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for cloud → local real-time synchronization.

    Broadcasts:
    - Agent config updates
    - Tool updates
    - MCP server updates
    - Group updates
    """

    async def connect(self):
        """Accept connection for tenant-specific sync channel"""
        self.user = self.scope.get('user')

        # Authenticate
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Subscribe to tenant-specific sync channel
        tenant = await self.get_user_tenant()
        if not tenant:
            await self.close(code=4003)
            return

        self.tenant_id = str(tenant.id) if tenant else 'public'
        self.sync_channel_name = f'sync_{self.tenant_id}'

        # Join sync channel
        await self.channel_layer.group_add(
            self.sync_channel_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            'type': 'sync_connected',
            'tenant_id': self.tenant_id
        }))

        logger.info(f"User {self.user.email} connected to sync channel {self.tenant_id}")

    async def disconnect(self, close_code):
        """Leave sync channel"""
        if hasattr(self, 'sync_channel_name'):
            await self.channel_layer.group_discard(
                self.sync_channel_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming sync requests"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'request_sync':
                # Client requesting full sync
                await self.send(text_data=json.dumps({
                    'type': 'sync_requested',
                    'message': 'Full sync will be performed'
                }))

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in sync message: {text_data}")

    # ============================================================================
    # Sync Event Handlers
    # ============================================================================

    async def agent_updated(self, event):
        """Broadcast agent config update"""
        await self.send(text_data=json.dumps({
            'type': 'agent_updated',
            'agent': event['agent']
        }))

    async def tool_updated(self, event):
        """Broadcast tool update"""
        await self.send(text_data=json.dumps({
            'type': 'tool_updated',
            'tool': event['tool']
        }))

    async def mcp_updated(self, event):
        """Broadcast MCP server update"""
        await self.send(text_data=json.dumps({
            'type': 'mcp_updated',
            'mcp_server': event['mcp_server']
        }))

    async def group_updated(self, event):
        """Broadcast group update"""
        await self.send(text_data=json.dumps({
            'type': 'group_updated',
            'group': event['group']
        }))

    @database_sync_to_async
    def get_user_tenant(self):
        """Get user's tenant"""
        return self.user.tenant if hasattr(self.user, 'tenant') else None
