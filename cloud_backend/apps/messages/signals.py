"""
Django Signals for Real-Time WebSocket Broadcasting

Automatically broadcasts WebSocket events when models are created/updated/deleted.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .models import Message
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=Message)
def broadcast_message_saved(sender, instance, created, **kwargs):
    """
    Broadcast WebSocket event when message is created or updated.

    Sends to group channel: messages_{group_id}
    """
    try:
        # Serialize message data
        serializer = MessageSerializer(instance)
        message_data = serializer.data

        # Determine event type
        event_type = 'message_created' if created else 'message_updated'

        # Broadcast to group channel
        room_group_name = f'messages_{instance.group_id}'

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': event_type,
                'message': message_data
            }
        )

        logger.info(f"Broadcasted {event_type} for message {instance.id} to group {instance.group_id}")

    except Exception as e:
        logger.error(f"Error broadcasting message event: {e}")


@receiver(post_delete, sender=Message)
def broadcast_message_deleted(sender, instance, **kwargs):
    """
    Broadcast WebSocket event when message is deleted.
    """
    try:
        room_group_name = f'messages_{instance.group_id}'

        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'message_deleted',
                'message_id': str(instance.id)
            }
        )

        logger.info(f"Broadcasted message_deleted for message {instance.id}")

    except Exception as e:
        logger.error(f"Error broadcasting message deletion: {e}")


# ============================================================================
# REMOVED: Cloud Sync Signals
# ============================================================================
#
# NOTE: Agent, Tool, MCP, Group, TenantSettings, and Document signal handlers
# are now centralized in apps/core/signals.py to avoid duplicate broadcasts.
#
# This file now only handles Message-specific signals.
#
# See: /cloud_backend/apps/core/signals.py for:
#   - Agent create/update/delete broadcasts
#   - Tool create/update/delete broadcasts
#   - MCPServer create/update/delete broadcasts
#   - Group create/update/delete broadcasts (to group members)
#   - TenantSettings create/update/delete broadcasts
#   - Document create/update/delete broadcasts (to group members)
#
# All broadcasts use proper tenant scoping via instance.tenant (ForeignKey field)
# ============================================================================
