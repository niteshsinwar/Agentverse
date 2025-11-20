"""
Signal Handlers for WebSocket Broadcasting

Broadcasts CRUD operations to all users in tenant via WebSocket.

Models monitored:
- Agent: Agent configurations
- Tool: Tool configurations
- MCPServer: MCP server configurations
- Group: Group metadata

Architecture:
- Any CRUD operation on these models triggers signal
- Signal broadcasts to tenant-wide sync channel
- All local backends in tenant receive update
- Local backends update their cache in real-time

Author: AgentVerse Team
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def broadcast_to_tenant_sync(tenant_id, event_type, data):
    """
    Broadcast event to all users in tenant via WebSocket.

    Args:
        tenant_id: Tenant ID
        event_type: Event type (e.g., 'agent_updated', 'tool_updated')
        data: Event data (serialized model)
    """
    if not tenant_id:
        logger.warning(f"Attempted to broadcast {event_type} without tenant_id")
        return

    channel_layer = get_channel_layer()
    sync_channel_name = f'sync_{tenant_id}'

    try:
        async_to_sync(channel_layer.group_send)(
            sync_channel_name,
            {
                'type': event_type,
                **data
            }
        )
        logger.debug(f"Broadcast {event_type} to {sync_channel_name}")
    except Exception as e:
        logger.error(f"Failed to broadcast {event_type}: {e}")


# ============================================================================
# Agent Signals
# ============================================================================

@receiver(post_save, sender='agents.Agent')
def agent_saved(sender, instance, created, **kwargs):
    """Broadcast agent create/update to tenant"""
    from apps.agents.serializers import AgentSerializer

    try:
        # Serialize agent
        agent_data = AgentSerializer(instance).data

        # Broadcast to tenant
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='agent_updated',
            data={'agent': agent_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"Agent {action}: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast agent_saved: {e}")


@receiver(post_delete, sender='agents.Agent')
def agent_deleted(sender, instance, **kwargs):
    """Broadcast agent deletion to tenant"""
    try:
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='agent_deleted',
            data={
                'agent_id': str(instance.id),
                'agent_name': instance.name
            }
        )

        logger.info(f"Agent deleted: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast agent_deleted: {e}")


# ============================================================================
# Tool Signals
# ============================================================================

@receiver(post_save, sender='tools.Tool')
def tool_saved(sender, instance, created, **kwargs):
    """Broadcast tool create/update to tenant"""
    from apps.tools.serializers import ToolSerializer

    try:
        tool_data = ToolSerializer(instance).data

        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='tool_updated',
            data={'tool': tool_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"Tool {action}: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast tool_saved: {e}")


@receiver(post_delete, sender='tools.Tool')
def tool_deleted(sender, instance, **kwargs):
    """Broadcast tool deletion to tenant"""
    try:
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='tool_deleted',
            data={
                'tool_id': str(instance.id),
                'tool_name': instance.name
            }
        )

        logger.info(f"Tool deleted: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast tool_deleted: {e}")


# ============================================================================
# MCP Server Signals
# ============================================================================

@receiver(post_save, sender='mcp.MCPServer')
def mcp_saved(sender, instance, created, **kwargs):
    """Broadcast MCP server create/update to tenant"""
    from apps.mcp.serializers import MCPServerSerializer

    try:
        mcp_data = MCPServerSerializer(instance).data

        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='mcp_updated',
            data={'mcp_server': mcp_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"MCP server {action}: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast mcp_saved: {e}")


@receiver(post_delete, sender='mcp.MCPServer')
def mcp_deleted(sender, instance, **kwargs):
    """Broadcast MCP server deletion to tenant"""
    try:
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='mcp_deleted',
            data={
                'mcp_id': str(instance.id),
                'mcp_name': instance.name
            }
        )

        logger.info(f"MCP server deleted: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast mcp_deleted: {e}")


# ============================================================================
# Group Signals
# ============================================================================

@receiver(post_save, sender='groups.Group')
def group_saved(sender, instance, created, **kwargs):
    """Broadcast group create/update to tenant"""
    from apps.groups.serializers import GroupSerializer

    try:
        group_data = GroupSerializer(instance).data

        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='group_updated',
            data={'group': group_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"Group {action}: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast group_saved: {e}")


@receiver(post_delete, sender='groups.Group')
def group_deleted(sender, instance, **kwargs):
    """Broadcast group deletion to tenant"""
    try:
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='group_deleted',
            data={
                'group_id': str(instance.id),
                'group_name': instance.name
            }
        )

        logger.info(f"Group deleted: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast group_deleted: {e}")
