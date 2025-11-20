from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import connection
from apps.tenants.models import Tenant
from .models import Message
from .serializers import MessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message CRUD operations.

    SECURITY: Messages are tenant-isolated. Explicit filtering prevents cross-tenant access.

    WebSocket Broadcasting:
    - Creates broadcast new messages to group channel
    - Updates broadcast message updates
    - Deletes broadcast message deletions
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'sender_type', 'sender_id']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """Filter messages by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Message.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Message.objects.none()

        return Message.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """
        Auto-set tenant and execution context on create.

        Execution Context Tracking:
        - Extracts execution context from request (via middleware)
        - Stores in message metadata for analytics and debugging
        - Includes device_id for WebSocket routing
        - Tracks initiator user and execution chain
        """
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)

        # Extract execution context from request (set by ExecutionContextMiddleware)
        execution_context = getattr(self.request, 'execution_context', None)

        # Merge execution context into metadata
        metadata = serializer.validated_data.get('metadata', {})

        if execution_context:
            # Add execution tracking metadata
            metadata.update({
                'device_id': execution_context.get('device_id'),
                'execution_id': execution_context.get('execution_id'),
                'initiator_user_id': execution_context.get('initiator_user_id'),
                'initiator_device_id': execution_context.get('initiator_device_id'),
                'call_depth': execution_context.get('call_depth', 0)
            })

            logger.debug(
                f"Message created with execution context: "
                f"exec_id={execution_context.get('execution_id', 'N/A')[:8]}..., "
                f"device_id={execution_context.get('device_id', 'N/A')[:8]}..."
            )

        # Save message with tenant and updated metadata
        message = serializer.save(tenant=tenant, metadata=metadata)

        # Broadcast to WebSocket (group channel for real-time updates)
        self._broadcast_message_created(message)

    def perform_update(self, serializer):
        """Broadcast message update to WebSocket"""
        message = serializer.save()
        self._broadcast_message_updated(message)

    def perform_destroy(self, instance):
        """Broadcast message deletion to WebSocket"""
        message_id = str(instance.id)
        group_id = str(instance.group)
        instance.delete()
        self._broadcast_message_deleted(message_id, group_id)

    # ============================================================================
    # WebSocket Broadcasting Methods
    # ============================================================================

    def _broadcast_message_created(self, message):
        """
        Broadcast new message to all users in the group via WebSocket.

        Architecture:
        - Local backend creates message → Cloud API stores → Broadcast to ALL users
        - All users in group receive real-time update (tenant-filtered)
        - Device routing happens at WebSocket consumer level
        """
        channel_layer = get_channel_layer()
        room_group_name = f'messages_{message.group}'

        # Serialize message for WebSocket
        message_data = MessageSerializer(message).data

        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'message_created',
                    'message': message_data
                }
            )
            logger.debug(f"Broadcast message_created to {room_group_name}")
        except Exception as e:
            logger.error(f"Failed to broadcast message_created: {e}")

    def _broadcast_message_updated(self, message):
        """Broadcast message update to group"""
        channel_layer = get_channel_layer()
        room_group_name = f'messages_{message.group}'

        message_data = MessageSerializer(message).data

        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'message_updated',
                    'message': message_data
                }
            )
            logger.debug(f"Broadcast message_updated to {room_group_name}")
        except Exception as e:
            logger.error(f"Failed to broadcast message_updated: {e}")

    def _broadcast_message_deleted(self, message_id, group_id):
        """Broadcast message deletion to group"""
        channel_layer = get_channel_layer()
        room_group_name = f'messages_{group_id}'

        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id
                }
            )
            logger.debug(f"Broadcast message_deleted to {room_group_name}")
        except Exception as e:
            logger.error(f"Failed to broadcast message_deleted: {e}")
