"""
Cloud WebSocket Sync Client

Receives real-time configuration updates from cloud backend via WebSocket.

When admins update agent/tool/MCP configs in the cloud backend, this client
receives push notifications and updates the local cache automatically.

Features:
- Auto-connect on startup
- JWT authentication
- Automatic reconnection with exponential backoff
- Event-driven architecture
- Updates local cache on sync events

Author: AgentVerse Team
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


@dataclass
class SyncEvent:
    """
    Cloud sync event from WebSocket.

    Sent when cloud admin updates configs.
    """
    type: str  # 'agent_updated', 'tool_updated', 'mcp_updated', 'group_updated'
    data: Dict[str, Any]  # The updated entity
    timestamp: datetime


class CloudWebSocketClient:
    """
    WebSocket client for receiving real-time sync events from cloud backend.

    Connects to cloud backend WebSocket endpoint:
        ws://localhost:9000/ws/sync/?token=<jwt>

    Events received:
    - agent_updated: Agent config changed
    - tool_updated: Tool code changed
    - mcp_updated: MCP server config changed
    - group_updated: Group membership changed

    Example:
        ws_client = CloudWebSocketClient(
            ws_url="ws://localhost:9000",
            access_token="jwt_token_here"
        )

        # Register handler
        async def handle_agent_update(event: SyncEvent):
            print(f"Agent updated: {event.data}")

        ws_client.on_sync(handle_agent_update)

        # Connect and listen
        await ws_client.connect()
    """

    def __init__(
        self,
        ws_url: str,
        access_token: str,
        auto_reconnect: bool = True,
        reconnect_delay: int = 2,
        max_reconnect_delay: int = 60,
        max_reconnect_attempts: int = 10
    ):
        """
        Initialize WebSocket sync client.

        Args:
            ws_url: WebSocket URL (e.g., "ws://localhost:9000")
            access_token: JWT access token for authentication
            auto_reconnect: Enable automatic reconnection on disconnect
            reconnect_delay: Initial reconnect delay in seconds
            max_reconnect_delay: Maximum reconnect delay in seconds
            max_reconnect_attempts: Maximum reconnection attempts (-1 = infinite)
        """
        self.ws_url = ws_url
        self.access_token = access_token
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self.ws: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_attempts = 0

        # Event handlers
        self._sync_handlers: List[Callable[[SyncEvent], Any]] = []

        # Background tasks
        self._listen_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(f"WebSocket client initialized: {ws_url}")

    def on_sync(self, handler: Callable[[SyncEvent], Any]):
        """
        Register a sync event handler.

        Handler will be called for all sync events (agent/tool/MCP/group updates).

        Args:
            handler: Async function that takes SyncEvent as parameter

        Example:
            async def my_handler(event: SyncEvent):
                if event.type == 'agent_updated':
                    update_agent_cache(event.data)

            ws_client.on_sync(my_handler)
        """
        self._sync_handlers.append(handler)
        logger.info(f"Registered sync handler: {handler.__name__}")

    async def connect(self):
        """
        Connect to cloud WebSocket server.

        Establishes connection and starts listening for sync events.

        SECURITY: Token sent via Authorization header instead of URL query parameter
        to prevent exposure in logs, browser history, and proxy logs.
        """
        try:
            # Build WebSocket URL (NO token in URL for security)
            sync_endpoint = f"{self.ws_url}/ws/sync/"

            logger.info(f"Connecting to cloud WebSocket: {sync_endpoint}")

            # Connect with timeout and Authorization header
            self.ws = await asyncio.wait_for(
                websockets.connect(
                    sync_endpoint,
                    extra_headers={
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    ping_interval=30,  # Send ping every 30s to keep connection alive
                    ping_timeout=10,   # Wait 10s for pong
                ),
                timeout=10
            )

            self.connected = True
            self.reconnect_attempts = 0

            logger.info("✅ Cloud WebSocket connected successfully")

            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen())

        except asyncio.TimeoutError:
            logger.error("❌ WebSocket connection timeout")
            self.connected = False
            if self.auto_reconnect:
                await self._schedule_reconnect()

        except WebSocketException as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self.connected = False
            if self.auto_reconnect:
                await self._schedule_reconnect()

        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to WebSocket: {e}")
            self.connected = False
            if self.auto_reconnect:
                await self._schedule_reconnect()

    async def disconnect(self):
        """
        Disconnect from WebSocket server.

        Cancels all background tasks and closes the connection.
        """
        logger.info("Disconnecting from cloud WebSocket...")

        # Cancel background tasks
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # Close WebSocket connection
        if self.ws and not self.ws.closed:
            await self.ws.close()

        self.connected = False
        logger.info("✅ WebSocket disconnected")

    async def _listen(self):
        """
        Listen for incoming WebSocket messages (sync events).

        Runs in background task, continuously receiving and processing events.
        """
        try:
            logger.info("Started listening for sync events...")

            async for message in self.ws:
                try:
                    # Parse JSON message
                    data = json.loads(message)

                    # Create sync event
                    event = SyncEvent(
                        type=data.get('type'),
                        data=self._extract_event_data(data),
                        timestamp=datetime.utcnow()
                    )

                    logger.info(f"📥 Received sync event: {event.type}")

                    # Notify all handlers
                    await self._notify_handlers(event)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")

                except Exception as e:
                    logger.error(f"Error processing sync event: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed by server")
            self.connected = False
            if self.auto_reconnect:
                await self._schedule_reconnect()

        except Exception as e:
            logger.error(f"Error in WebSocket listen loop: {e}")
            self.connected = False
            if self.auto_reconnect:
                await self._schedule_reconnect()

    def _extract_event_data(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entity data from sync event message"""
        event_type = message.get('type')

        # Map event types to data keys
        data_key_map = {
            'agent_updated': 'agent',
            'tool_updated': 'tool',
            'mcp_updated': 'mcp_server',
            'group_updated': 'group',
        }

        data_key = data_key_map.get(event_type)
        if data_key:
            return message.get(data_key, {})

        return {}

    async def _notify_handlers(self, event: SyncEvent):
        """
        Notify all registered handlers about sync event.

        Handlers are called asynchronously.
        """
        for handler in self._sync_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

            except Exception as e:
                logger.error(f"Error in sync handler {handler.__name__}: {e}")

    async def _schedule_reconnect(self):
        """
        Schedule reconnection attempt with exponential backoff.

        Doubles delay on each attempt up to max_reconnect_delay.
        """
        if self.max_reconnect_attempts != -1:
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached. Giving up.")
                return

        self.reconnect_attempts += 1

        # Calculate delay with exponential backoff
        delay = min(
            self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
            self.max_reconnect_delay
        )

        logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts})...")

        await asyncio.sleep(delay)

        logger.info(f"Reconnection attempt #{self.reconnect_attempts}...")
        await self.connect()

    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected and self.ws and not self.ws.closed


# Global client instance
_cloud_ws_client: Optional[CloudWebSocketClient] = None


def initialize_cloud_websocket(ws_url: str, access_token: str) -> CloudWebSocketClient:
    """
    Initialize global cloud WebSocket client.

    Args:
        ws_url: WebSocket URL (e.g., "ws://localhost:9000")
        access_token: JWT access token

    Returns:
        Initialized WebSocket client instance
    """
    global _cloud_ws_client

    if _cloud_ws_client:
        logger.warning("Cloud WebSocket client already initialized. Replacing...")

    _cloud_ws_client = CloudWebSocketClient(ws_url, access_token)
    logger.info("Cloud WebSocket client initialized globally")

    return _cloud_ws_client


def get_cloud_websocket() -> Optional[CloudWebSocketClient]:
    """
    Get global cloud WebSocket client instance.

    Returns:
        WebSocket client or None if not initialized
    """
    return _cloud_ws_client


async def shutdown_cloud_websocket():
    """Shutdown global WebSocket client"""
    global _cloud_ws_client

    if _cloud_ws_client:
        await _cloud_ws_client.disconnect()
        _cloud_ws_client = None
        logger.info("Cloud WebSocket client shut down")
