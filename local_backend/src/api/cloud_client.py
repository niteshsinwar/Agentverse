"""
Cloud API Client - Communicates with Django backend for CRUD operations

This client handles all communication with the cloud backend (Django SaaS):
- Authentication (login, token validation, refresh)
- Fetching tenant data (agents, tools, MCP servers, groups, users)
- CRUD operations for all resources
- Real-time sync notifications

Data Flow:
1. User logs in → Get JWT token
2. Local backend validates token with cloud
3. Fetch all tenant configs (agents, tools, MCP, groups)
4. Cache locally for execution
5. Send results back to cloud

Author: AgentVerse Team
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CloudConfig:
    """Cloud backend configuration"""
    base_url: str  # e.g., "https://agentverse-cloud.onrender.com"
    api_version: str = "v1"
    timeout: int = 30  # seconds
    max_retries: int = 3

    @property
    def api_base_url(self) -> str:
        """Full API base URL"""
        return f"{self.base_url}/api/{self.api_version}"


@dataclass
class AuthToken:
    """JWT authentication token with metadata"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def needs_refresh(self) -> bool:
        """Check if token needs refresh (5 minutes before expiry)"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=5))


class CloudAPIClient:
    """
    Client for communicating with cloud backend (Django SaaS).

    Handles:
    - Authentication (login, token validation, refresh)
    - Fetching tenant data (agents, tools, MCP servers, groups)
    - CRUD operations
    - Automatic token refresh
    - Retry logic with exponential backoff

    Example:
        client = CloudAPIClient(CloudConfig(base_url="https://api.agentverse.com"))

        # Login
        token = await client.login("user@example.com", "password")

        # Fetch all tenant data
        agents = await client.fetch_agents()
        tools = await client.fetch_tools()
        mcp_servers = await client.fetch_mcp_servers()
    """

    def __init__(
        self,
        config: CloudConfig,
        token: Optional[AuthToken] = None,
        device_id: Optional[str] = None
    ):
        """
        Initialize cloud API client.

        Args:
            config: Cloud backend configuration
            token: Optional JWT token (if already authenticated)
            device_id: Device ID for WebSocket routing (CRITICAL)
        """
        self.config = config
        self.token = token
        self.device_id = device_id  # CRITICAL: Required for WebSocket routing
        self._session: Optional[aiohttp.ClientSession] = None
        self._execution_context = None  # Current execution context (if in agent chain)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def set_execution_context(self, execution_context):
        """
        Set current execution context (for agent chains).

        Args:
            execution_context: ExecutionContext instance or None
        """
        self._execution_context = execution_context

    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """
        Get request headers with optional authentication.

        CRITICAL Headers:
        - X-Tenant-ID: Multi-tenancy isolation
        - X-Device-ID: WebSocket routing (REQUIRED for real-time updates)
        - X-Execution-ID: Execution chain tracking
        - X-Initiator-User-ID: User who started the chain
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if include_auth and self.token:
            headers["Authorization"] = f"{self.token.token_type} {self.token.access_token}"

            # CRITICAL: Pass tenant_id for multi-tenancy validation
            if self.token.tenant_id:
                headers["X-Tenant-ID"] = self.token.tenant_id

        # CRITICAL: Pass device_id for WebSocket routing
        # Cloud backend uses this to route messages back to correct device
        if self.device_id:
            headers["X-Device-ID"] = self.device_id

        # Pass execution context headers (if in agent chain)
        if self._execution_context:
            headers["X-Execution-ID"] = self._execution_context.execution_id
            headers["X-Initiator-User-ID"] = self._execution_context.initiator_user_id
            headers["X-Initiator-Device-ID"] = self._execution_context.initiator_device_id
            headers["X-Call-Depth"] = str(self._execution_context.depth)

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        include_auth: bool = True,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and token refresh.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (e.g., "/agents")
            include_auth: Include authorization header
            json_data: Request body (for POST, PUT, PATCH)
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            Response JSON data

        Raises:
            CloudAPIError: If request fails after retries
        """
        # Check if token needs refresh
        if include_auth and self.token and self.token.needs_refresh():
            logger.info("Token needs refresh, refreshing...")
            await self.refresh_token()

        url = f"{self.config.api_base_url}{endpoint}"
        headers = self._get_headers(include_auth=include_auth)
        session = await self._get_session()

        try:
            async with session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params
            ) as response:

                # Handle token expiration
                if response.status == 401 and include_auth:
                    logger.warning("Token expired, attempting refresh...")
                    await self.refresh_token()
                    # Retry request with new token
                    return await self._request(method, endpoint, include_auth, json_data, params, retry_count)

                # Check for success
                if response.status >= 200 and response.status < 300:
                    return await response.json()

                # Handle errors
                error_text = await response.text()
                error_msg = f"Cloud API error: {response.status} - {error_text}"

                # Retry on server errors (5xx) or rate limiting (429)
                if (response.status >= 500 or response.status == 429) and retry_count < self.config.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Request failed with {response.status}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    return await self._request(method, endpoint, include_auth, json_data, params, retry_count + 1)

                raise CloudAPIError(error_msg, status_code=response.status)

        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"

            # Retry on network errors
            if retry_count < self.config.max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Network error, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self._request(method, endpoint, include_auth, json_data, params, retry_count + 1)

            raise CloudAPIError(error_msg)

    # ============================================================================
    # AUTHENTICATION
    # ============================================================================

    async def login(self, email: str, password: str) -> AuthToken:
        """
        Login user and get JWT token.

        Args:
            email: User email
            password: User password

        Returns:
            AuthToken with access_token, refresh_token, and metadata

        Example:
            token = await client.login("user@example.com", "password")
            print(f"Logged in as: {token.user_role}")
        """
        response = await self._request(
            method="POST",
            endpoint="/auth/login",
            include_auth=False,
            json_data={"email": email, "password": password}
        )

        # Parse token response
        self.token = AuthToken(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            token_type=response.get("token_type", "Bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=response.get("expires_in", 3600)),
            tenant_id=response.get("tenant_id"),
            user_id=response.get("user_id"),
            user_role=response.get("user_role")
        )

        logger.info(f"Logged in successfully: tenant={self.token.tenant_id}, user={self.token.user_id}")
        return self.token

    async def validate_token(self) -> Dict[str, Any]:
        """
        Validate current token with cloud backend.

        Returns:
            User info and permissions

        Example:
            user_info = await client.validate_token()
            print(f"Token valid for: {user_info['email']}")
        """
        return await self._request(
            method="POST",
            endpoint="/auth/validate-token"
        )

    async def refresh_token(self) -> AuthToken:
        """
        Refresh JWT token using refresh_token.

        Returns:
            New AuthToken

        Raises:
            CloudAPIError: If refresh fails (user needs to login again)
        """
        if not self.token or not self.token.refresh_token:
            raise CloudAPIError("No refresh token available")

        response = await self._request(
            method="POST",
            endpoint="/auth/refresh",
            include_auth=False,
            json_data={"refresh_token": self.token.refresh_token}
        )

        # Update token
        self.token = AuthToken(
            access_token=response["access_token"],
            refresh_token=response.get("refresh_token", self.token.refresh_token),
            token_type=response.get("token_type", "Bearer"),
            expires_at=datetime.utcnow() + timedelta(seconds=response.get("expires_in", 3600)),
            tenant_id=self.token.tenant_id,
            user_id=self.token.user_id,
            user_role=self.token.user_role
        )

        logger.info("Token refreshed successfully")
        return self.token

    async def logout(self):
        """
        Logout user (invalidate token on server).

        Example:
            await client.logout()
        """
        try:
            await self._request(method="POST", endpoint="/auth/logout")
        finally:
            self.token = None

    # ============================================================================
    # TENANT
    # ============================================================================

    async def fetch_tenant_info(self) -> Dict[str, Any]:
        """
        Fetch current tenant information.

        Returns:
            {
                "id": "tenant-uuid",
                "name": "Acme Corp",
                "license_type": "free",  # or "paid"
                "license_limits": {
                    "max_users": 3,
                    "max_groups": 2,
                    "max_agents": 4,
                    "max_tools": 7,
                    "max_mcp_servers": 3
                },
                "created_at": "2024-01-01T00:00:00Z"
            }
        """
        return await self._request(method="GET", endpoint="/tenants/me")

    # ============================================================================
    # AGENTS
    # ============================================================================

    async def fetch_agents(self) -> List[Dict[str, Any]]:
        """
        Fetch all agents for current tenant.

        Returns:
            List of agent configs:
            [
                {
                    "id": "agent-uuid",
                    "name": "Research Assistant",
                    "llm_provider": "anthropic",
                    "llm_model": "claude-sonnet-4.5",
                    "system_prompt": "You are a research assistant...",
                    "config": {...},
                    "created_by": "user-uuid",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        return await self._request(method="GET", endpoint="/agents")

    async def fetch_agent(self, agent_id: str) -> Dict[str, Any]:
        """Fetch single agent by ID"""
        return await self._request(method="GET", endpoint=f"/agents/{agent_id}")

    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new agent (admin only)"""
        return await self._request(method="POST", endpoint="/agents", json_data=agent_data)

    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent (admin only)"""
        return await self._request(method="PATCH", endpoint=f"/agents/{agent_id}", json_data=agent_data)

    async def delete_agent(self, agent_id: str):
        """Delete agent (admin only)"""
        return await self._request(method="DELETE", endpoint=f"/agents/{agent_id}")

    # ============================================================================
    # TOOLS
    # ============================================================================

    async def fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Fetch all tools for current tenant.

        Returns:
            List of tool configs:
            [
                {
                    "id": "tool-uuid",
                    "name": "web_search",
                    "description": "Search the web",
                    "code": "# Python code...",
                    "dependencies": ["requests", "beautifulsoup4"],
                    "created_by": "user-uuid",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        return await self._request(method="GET", endpoint="/tools")

    async def fetch_tool(self, tool_id: str) -> Dict[str, Any]:
        """Fetch single tool by ID"""
        return await self._request(method="GET", endpoint=f"/tools/{tool_id}")

    async def create_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tool (admin only)"""
        return await self._request(method="POST", endpoint="/tools", json_data=tool_data)

    async def update_tool(self, tool_id: str, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tool (admin only)"""
        return await self._request(method="PATCH", endpoint=f"/tools/{tool_id}", json_data=tool_data)

    async def delete_tool(self, tool_id: str):
        """Delete tool (admin only)"""
        return await self._request(method="DELETE", endpoint=f"/tools/{tool_id}")

    # ============================================================================
    # MCP SERVERS
    # ============================================================================

    async def fetch_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Fetch all MCP servers for current tenant.

        Returns:
            List of MCP server configs:
            [
                {
                    "id": "mcp-uuid",
                    "name": "filesystem",
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
                    "env": {"KEY": "value"},
                    "created_by": "user-uuid",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        return await self._request(method="GET", endpoint="/mcp-servers")

    async def fetch_mcp_server(self, mcp_id: str) -> Dict[str, Any]:
        """Fetch single MCP server by ID"""
        return await self._request(method="GET", endpoint=f"/mcp-servers/{mcp_id}")

    async def create_mcp_server(self, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new MCP server (admin only)"""
        return await self._request(method="POST", endpoint="/mcp-servers", json_data=mcp_data)

    async def update_mcp_server(self, mcp_id: str, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update MCP server (admin only)"""
        return await self._request(method="PATCH", endpoint=f"/mcp-servers/{mcp_id}", json_data=mcp_data)

    async def delete_mcp_server(self, mcp_id: str):
        """Delete MCP server (admin only)"""
        return await self._request(method="DELETE", endpoint=f"/mcp-servers/{mcp_id}")

    # ============================================================================
    # GROUPS
    # ============================================================================

    async def fetch_groups(self) -> List[Dict[str, Any]]:
        """
        Fetch all groups (teams/channels) for current tenant.

        Returns:
            List of groups:
            [
                {
                    "id": "group-uuid",
                    "name": "Engineering Team",
                    "description": "Engineering team channel",
                    "members": ["user-uuid-1", "user-uuid-2"],
                    "assigned_agents": ["agent-uuid-1"],
                    "created_by": "user-uuid",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        return await self._request(method="GET", endpoint="/groups")

    async def fetch_group(self, group_id: str) -> Dict[str, Any]:
        """Fetch single group by ID"""
        return await self._request(method="GET", endpoint=f"/groups/{group_id}")

    async def create_group(self, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new group (admin only)"""
        return await self._request(method="POST", endpoint="/groups", json_data=group_data)

    async def update_group(self, group_id: str, group_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update group (admin only)"""
        return await self._request(method="PATCH", endpoint=f"/groups/{group_id}", json_data=group_data)

    async def delete_group(self, group_id: str):
        """Delete group (admin only)"""
        return await self._request(method="DELETE", endpoint=f"/groups/{group_id}")

    # ============================================================================
    # USERS
    # ============================================================================

    async def fetch_users(self) -> List[Dict[str, Any]]:
        """
        Fetch all users for current tenant (admin only).

        Returns:
            List of users:
            [
                {
                    "id": "user-uuid",
                    "email": "user@example.com",
                    "name": "John Doe",
                    "role": "admin",  # or "normal"
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        """
        return await self._request(method="GET", endpoint="/users")

    async def fetch_user(self, user_id: str) -> Dict[str, Any]:
        """Fetch single user by ID"""
        return await self._request(method="GET", endpoint=f"/users/{user_id}")

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user (admin only)"""
        return await self._request(method="POST", endpoint="/users", json_data=user_data)

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user"""
        return await self._request(method="PATCH", endpoint=f"/users/{user_id}", json_data=user_data)

    async def delete_user(self, user_id: str):
        """Delete user (admin only)"""
        return await self._request(method="DELETE", endpoint=f"/users/{user_id}")

    # ============================================================================
    # MESSAGES
    # ============================================================================

    async def fetch_messages(self, group_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch conversation history for a group.

        Args:
            group_id: Group ID
            limit: Number of messages to fetch
            offset: Pagination offset

        Returns:
            List of messages
        """
        return await self._request(
            method="GET",
            endpoint=f"/groups/{group_id}/messages",
            params={"limit": limit, "offset": offset}
        )

    async def send_message(self, group_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send message to group.

        Args:
            group_id: Group ID
            message_data: {
                "content": "message text",
                "sender_type": "user" or "agent",
                "metadata": {...}
            }
        """
        return await self._request(
            method="POST",
            endpoint=f"/groups/{group_id}/messages",
            json_data=message_data
        )

    # ============================================================================
    # DOCUMENTS
    # ============================================================================

    async def fetch_documents(self, group_id: str) -> List[Dict[str, Any]]:
        """Fetch all documents for a group"""
        return await self._request(method="GET", endpoint=f"/groups/{group_id}/documents")

    async def upload_document(self, group_id: str, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Upload document to group (stored in MinIO/S3).

        Note: This requires multipart/form-data, implemented separately
        """
        # TODO: Implement multipart upload
        raise NotImplementedError("Document upload requires multipart form data")

    # ============================================================================
    # SYNC ALL TENANT DATA
    # ============================================================================

    async def sync_all_tenant_data(self) -> Dict[str, Any]:
        """
        Fetch all tenant data in one call for caching.

        This is called on startup to cache all configs locally.

        Returns:
            {
                "tenant": {...},
                "agents": [...],
                "tools": [...],
                "mcp_servers": [...],
                "groups": [...],
                "users": [...]
            }
        """
        logger.info("Syncing all tenant data from cloud...")

        # Fetch all data in parallel
        tenant_info, agents, tools, mcp_servers, groups, users = await asyncio.gather(
            self.fetch_tenant_info(),
            self.fetch_agents(),
            self.fetch_tools(),
            self.fetch_mcp_servers(),
            self.fetch_groups(),
            self.fetch_users()
        )

        logger.info(
            f"Synced: {len(agents)} agents, {len(tools)} tools, "
            f"{len(mcp_servers)} MCP servers, {len(groups)} groups, {len(users)} users"
        )

        return {
            "tenant": tenant_info,
            "agents": agents,
            "tools": tools,
            "mcp_servers": mcp_servers,
            "groups": groups,
            "users": users
        }


class CloudAPIError(Exception):
    """Cloud API error"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_cloud_client: Optional[CloudAPIClient] = None


def get_cloud_client() -> CloudAPIClient:
    """
    Get singleton cloud API client instance.

    Must be initialized first via initialize_cloud_client().

    Example:
        client = get_cloud_client()
        agents = await client.fetch_agents()
    """
    global _cloud_client
    if _cloud_client is None:
        raise RuntimeError("Cloud client not initialized. Call initialize_cloud_client() first.")
    return _cloud_client


def initialize_cloud_client(
    config: CloudConfig,
    token: Optional[AuthToken] = None,
    device_id: Optional[str] = None
) -> CloudAPIClient:
    """
    Initialize singleton cloud API client.

    Called on startup with config from settings.

    Args:
        config: Cloud backend configuration
        token: Optional JWT token
        device_id: Device ID for WebSocket routing (CRITICAL)

    Example:
        from src.core.device_manager import get_device_manager

        device_id = get_device_manager().get_device_id()
        config = CloudConfig(base_url="https://api.agentverse.com")
        client = initialize_cloud_client(config, device_id=device_id)
    """
    global _cloud_client
    _cloud_client = CloudAPIClient(config, token, device_id)
    logger.info(f"Cloud client initialized: {config.base_url} (device: {device_id[:8]}...)" if device_id else f"Cloud client initialized: {config.base_url}")
    return _cloud_client


async def shutdown_cloud_client():
    """Shutdown cloud API client (close connections)"""
    global _cloud_client
    if _cloud_client:
        await _cloud_client.close()
        _cloud_client = None
        logger.info("Cloud client shut down")
