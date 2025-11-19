"""
Cloud Sync Handler

Handles real-time configuration updates from cloud backend via WebSocket.

When cloud admin updates agents/tools/MCP/groups, this handler receives
WebSocket events and updates the local cache immediately.

This enables:
- Zero-delay config sync (no polling)
- Always up-to-date agent configurations
- Real-time tool code updates
- Automatic MCP server config sync

Author: AgentVerse Team
"""

import logging
from typing import Optional
from .cloud_websocket import SyncEvent, CloudWebSocketClient
from src.core.cache import CloudDataCache

logger = logging.getLogger(__name__)


class CloudSyncHandler:
    """
    Handles WebSocket sync events from cloud and updates local cache.

    Receives events for:
    - agent_updated: Agent config changed
    - tool_updated: Tool code changed
    - mcp_updated: MCP server config changed
    - group_updated: Group membership changed

    Example:
        handler = CloudSyncHandler(cache=cloud_cache)
        ws_client.on_sync(handler.handle_sync_event)
    """

    def __init__(self, cache: CloudDataCache):
        """
        Initialize sync handler.

        Args:
            cache: Cloud data cache instance to update
        """
        self.cache = cache
        logger.info("Cloud sync handler initialized")

    async def handle_sync_event(self, event: SyncEvent):
        """
        Handle incoming sync event from WebSocket.

        Updates local cache based on event type.

        Args:
            event: Sync event from cloud WebSocket
        """
        try:
            logger.info(f"📥 Processing sync event: {event.type}")

            if event.type == 'agent_updated':
                await self._handle_agent_update(event)

            elif event.type == 'tool_updated':
                await self._handle_tool_update(event)

            elif event.type == 'mcp_updated':
                await self._handle_mcp_update(event)

            elif event.type == 'group_updated':
                await self._handle_group_update(event)

            else:
                logger.warning(f"Unknown sync event type: {event.type}")

        except Exception as e:
            logger.error(f"Error handling sync event {event.type}: {e}")

    async def _handle_agent_update(self, event: SyncEvent):
        """
        Handle agent config update.

        Updates agent in local cache with new configuration.
        """
        agent_data = event.data

        if not agent_data or 'id' not in agent_data:
            logger.error("Invalid agent data in sync event")
            return

        agent_id = agent_data['id']
        agent_name = agent_data.get('name', 'Unknown')

        logger.info(f"Updating agent cache: {agent_name} ({agent_id})")

        try:
            # Update agent in cache
            await self.cache._cache_agent(agent_data)

            logger.info(f"✅ Agent cache updated: {agent_name}")

        except Exception as e:
            logger.error(f"Failed to update agent cache: {e}")

    async def _handle_tool_update(self, event: SyncEvent):
        """
        Handle tool code update.

        Updates tool in local cache with new code.
        """
        tool_data = event.data

        if not tool_data or 'id' not in tool_data:
            logger.error("Invalid tool data in sync event")
            return

        tool_id = tool_data['id']
        tool_name = tool_data.get('name', 'Unknown')

        logger.info(f"Updating tool cache: {tool_name} ({tool_id})")

        try:
            # Update tool in cache
            await self.cache._cache_tool(tool_data)

            logger.info(f"✅ Tool cache updated: {tool_name}")

        except Exception as e:
            logger.error(f"Failed to update tool cache: {e}")

    async def _handle_mcp_update(self, event: SyncEvent):
        """
        Handle MCP server config update.

        Updates MCP server in local cache with new configuration.
        """
        mcp_data = event.data

        if not mcp_data or 'id' not in mcp_data:
            logger.error("Invalid MCP server data in sync event")
            return

        mcp_id = mcp_data['id']
        mcp_name = mcp_data.get('name', 'Unknown')

        logger.info(f"Updating MCP server cache: {mcp_name} ({mcp_id})")

        try:
            # Update MCP server in cache
            await self.cache._cache_mcp_server(mcp_data)

            logger.info(f"✅ MCP server cache updated: {mcp_name}")

        except Exception as e:
            logger.error(f"Failed to update MCP server cache: {e}")

    async def _handle_group_update(self, event: SyncEvent):
        """
        Handle group membership update.

        Updates group in local cache with new members/agents.
        """
        group_data = event.data

        if not group_data or 'id' not in group_data:
            logger.error("Invalid group data in sync event")
            return

        group_id = group_data['id']
        group_name = group_data.get('name', 'Unknown')

        logger.info(f"Updating group cache: {group_name} ({group_id})")

        try:
            # Update group in cache
            await self.cache._cache_group(group_data)

            logger.info(f"✅ Group cache updated: {group_name}")

        except Exception as e:
            logger.error(f"Failed to update group cache: {e}")


# Global sync handler instance
_sync_handler: Optional[CloudSyncHandler] = None


def initialize_sync_handler(cache: CloudDataCache) -> CloudSyncHandler:
    """
    Initialize global sync handler.

    Args:
        cache: Cloud data cache to update

    Returns:
        Initialized sync handler
    """
    global _sync_handler

    _sync_handler = CloudSyncHandler(cache)
    logger.info("Cloud sync handler initialized globally")

    return _sync_handler


def get_sync_handler() -> Optional[CloudSyncHandler]:
    """
    Get global sync handler instance.

    Returns:
        Sync handler or None if not initialized
    """
    return _sync_handler
