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
# Cloud Sync Signals - Broadcast config changes to local backends
# ============================================================================

def broadcast_tenant_update(tenant_id, event_type, data):
    """
    Helper function to broadcast tenant-specific updates.

    Args:
        tenant_id: Tenant UUID
        event_type: Event type (agent_updated, tool_updated, etc.)
        data: Serialized model data
    """
    try:
        sync_channel_name = f'sync_{tenant_id}'

        async_to_sync(channel_layer.group_send)(
            sync_channel_name,
            {
                'type': event_type,
                event_type.replace('_updated', ''): data  # agent_updated -> agent: data
            }
        )

        logger.info(f"Broadcasted {event_type} to tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Error broadcasting tenant update: {e}")


@receiver(post_save, sender='agents.Agent')
def broadcast_agent_update(sender, instance, created, **kwargs):
    """Broadcast agent config update to local backends"""
    from apps.agents.serializers import AgentSerializer

    # Get tenant ID
    tenant = instance.get_tenant() if hasattr(instance, 'get_tenant') else None
    if not tenant:
        return

    serializer = AgentSerializer(instance)
    broadcast_tenant_update(
        tenant_id=str(tenant.id),
        event_type='agent_updated',
        data=serializer.data
    )


@receiver(post_save, sender='tools.Tool')
def broadcast_tool_update(sender, instance, created, **kwargs):
    """Broadcast tool update to local backends"""
    from apps.tools.serializers import ToolSerializer

    tenant = instance.get_tenant() if hasattr(instance, 'get_tenant') else None
    if not tenant:
        return

    serializer = ToolSerializer(instance)
    broadcast_tenant_update(
        tenant_id=str(tenant.id),
        event_type='tool_updated',
        data=serializer.data
    )


@receiver(post_save, sender='mcp.MCPServer')
def broadcast_mcp_update(sender, instance, created, **kwargs):
    """Broadcast MCP server update to local backends"""
    from apps.mcp.serializers import MCPServerSerializer

    tenant = instance.get_tenant() if hasattr(instance, 'get_tenant') else None
    if not tenant:
        return

    serializer = MCPServerSerializer(instance)
    broadcast_tenant_update(
        tenant_id=str(tenant.id),
        event_type='mcp_updated',
        data=serializer.data
    )


@receiver(post_save, sender='groups.Group')
def broadcast_group_update(sender, instance, created, **kwargs):
    """Broadcast group update to local backends"""
    from apps.groups.serializers import GroupSerializer

    tenant = instance.get_tenant() if hasattr(instance, 'get_tenant') else None
    if not tenant:
        return

    serializer = GroupSerializer(instance)
    broadcast_tenant_update(
        tenant_id=str(tenant.id),
        event_type='group_updated',
        data=serializer.data
    )
