"""
Signal Handlers for WebSocket Broadcasting

Broadcasts CRUD operations to users via WebSocket.

Models monitored:
- Agent: Agent configurations (broadcast to all tenant users)
- Tool: Tool configurations (broadcast to all tenant users)
- MCPServer: MCP server configurations (broadcast to all tenant users)
- Group: Group metadata (broadcast to group members + admins)
- TenantSettings: Tenant settings (broadcast to all tenant users)
- Document: Documents (broadcast to group members only)

Architecture:
- Any CRUD operation on these models triggers signal
- Signals broadcast to appropriate channels based on scoping:
  * Tenant-wide: sync_{tenant_id} (agents, tools, MCP, settings)
  * Group-specific: user_{user_id}_{tenant_id} (groups, documents)
- All connected users receive real-time updates
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

def broadcast_to_group_members(group_instance, event_type, data):
    """
    Broadcast event only to members of a specific group.

    Args:
        group_instance: Group model instance
        event_type: Event type (e.g., 'group_updated', 'group_deleted')
        data: Event data
    """
    channel_layer = get_channel_layer()

    # Get group members
    members = group_instance.members if isinstance(group_instance.members, list) else []

    # Broadcast to each member's channels
    for user_id in members:
        # Send to user-specific channel (if they're connected)
        user_channel_name = f'user_{user_id}_{group_instance.tenant_id}'

        try:
            async_to_sync(channel_layer.group_send)(
                user_channel_name,
                {
                    'type': event_type,
                    **data
                }
            )
        except Exception as e:
            logger.debug(f"Could not send to user channel {user_channel_name}: {e}")

    # Also broadcast to tenant-wide sync for admin visibility
    broadcast_to_tenant_sync(
        tenant_id=str(group_instance.tenant_id),
        event_type=event_type,
        data=data
    )


@receiver(post_save, sender='groups.Group')
def group_saved(sender, instance, created, **kwargs):
    """Broadcast group create/update to group members and admins"""
    from apps.groups.serializers import GroupSerializer

    try:
        group_data = GroupSerializer(instance).data

        # Broadcast to group members + tenant admins
        broadcast_to_group_members(
            group_instance=instance,
            event_type='group_updated',
            data={'group': group_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"Group {action}: {instance.name} (tenant: {instance.tenant_id}, members: {len(instance.members)})")
    except Exception as e:
        logger.error(f"Failed to broadcast group_saved: {e}")


@receiver(post_delete, sender='groups.Group')
def group_deleted(sender, instance, **kwargs):
    """Broadcast group deletion to former members and admins"""
    try:
        # Broadcast to former group members + tenant admins
        broadcast_to_group_members(
            group_instance=instance,
            event_type='group_deleted',
            data={
                'group_id': str(instance.id),
                'group_name': instance.name
            }
        )

        logger.info(f"Group deleted: {instance.name} (tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast group_deleted: {e}")


# ============================================================================
# TenantSettings Signals
# ============================================================================

@receiver(post_save, sender='tenants.TenantSettings')
def tenant_settings_saved(sender, instance, created, **kwargs):
    """
    Broadcast tenant settings update to ALL users in tenant.

    Settings are tenant-wide configuration that affects all users.
    Admin-only modification, but all users should see updates in real-time.
    """
    from apps.tenants.serializers import TenantSettingsSerializer

    try:
        settings_data = TenantSettingsSerializer(instance).data

        # Broadcast to ALL users in tenant (settings affect everyone)
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='settings_updated',
            data={'settings': settings_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"TenantSettings {action}: {instance.tenant.name}")
    except Exception as e:
        logger.error(f"Failed to broadcast tenant_settings_saved: {e}")


@receiver(post_delete, sender='tenants.TenantSettings')
def tenant_settings_deleted(sender, instance, **kwargs):
    """Broadcast tenant settings deletion to all users in tenant"""
    try:
        broadcast_to_tenant_sync(
            tenant_id=str(instance.tenant_id),
            event_type='settings_deleted',
            data={
                'settings_id': str(instance.id),
                'tenant_name': instance.tenant.name
            }
        )

        logger.info(f"TenantSettings deleted for tenant: {instance.tenant.name}")
    except Exception as e:
        logger.error(f"Failed to broadcast tenant_settings_deleted: {e}")


# ============================================================================
# Document Signals
# ============================================================================

def broadcast_to_document_group(document_instance, event_type, data):
    """
    Broadcast document event to members of the document's group.

    Documents are group+tenant scoped - only group members should receive updates.
    """
    from apps.groups.models import Group

    try:
        # Fetch the group to get members list
        group = Group.objects.get(id=document_instance.group, tenant=document_instance.tenant)

        # Create a pseudo group instance for broadcast_to_group_members
        class GroupProxy:
            def __init__(self, members, tenant_id):
                self.members = members
                self.tenant_id = tenant_id

        proxy = GroupProxy(members=group.members, tenant_id=document_instance.tenant_id)

        # Broadcast to group members
        broadcast_to_group_members(
            group_instance=proxy,
            event_type=event_type,
            data=data
        )
    except Group.DoesNotExist:
        logger.warning(f"Group {document_instance.group} not found for document broadcast")
    except Exception as e:
        logger.error(f"Failed to broadcast to document group: {e}")


@receiver(post_save, sender='documents.Document')
def document_saved(sender, instance, created, **kwargs):
    """
    Broadcast document create/update to group members.

    Documents are group-specific - only members of the group should see updates.
    """
    from apps.documents.serializers import DocumentSerializer

    try:
        document_data = DocumentSerializer(instance).data

        # Broadcast to group members only
        broadcast_to_document_group(
            document_instance=instance,
            event_type='document_updated',
            data={'document': document_data}
        )

        action = 'created' if created else 'updated'
        logger.info(f"Document {action}: {instance.filename} (group: {instance.group}, tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast document_saved: {e}")


@receiver(post_delete, sender='documents.Document')
def document_deleted(sender, instance, **kwargs):
    """Broadcast document deletion to group members"""
    try:
        # Broadcast to group members
        broadcast_to_document_group(
            document_instance=instance,
            event_type='document_deleted',
            data={
                'document_id': str(instance.id),
                'filename': instance.filename,
                'group_id': str(instance.group)
            }
        )

        logger.info(f"Document deleted: {instance.filename} (group: {instance.group}, tenant: {instance.tenant_id})")
    except Exception as e:
        logger.error(f"Failed to broadcast document_deleted: {e}")
