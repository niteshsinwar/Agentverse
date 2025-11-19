"""
Cloud Data Cache - Local caching of cloud configs for offline execution

This module caches all tenant data (agents, tools, MCP servers, groups, users)
locally for execution. This enables:

1. Fast execution without cloud API calls
2. Offline-capable operation
3. CRUD operations use cloud, execution uses cached version

Data Flow:
- On startup: Sync all tenant data from cloud → cache locally
- On CRUD: Update cloud → refresh cache
- On execution: Use cached configs (NO cloud API calls)

Cache Strategy:
- Store in SQLite for persistence (survives restarts)
- In-memory cache for fast access
- TTL-based refresh (default: 5 minutes)
- Manual refresh on CRUD operations

Author: AgentVerse Team
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    cached_at: datetime
    ttl: Optional[int] = None  # seconds

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.ttl:
            return False
        return datetime.utcnow() >= (self.cached_at + timedelta(seconds=self.ttl))


class CloudDataCache:
    """
    Local cache for cloud data (agents, tools, MCP servers, groups, users).

    Stores data in SQLite for persistence and in-memory for fast access.

    Example:
        cache = CloudDataCache(cache_dir="/home/user/.agentverse/cache")
        await cache.initialize()

        # Sync from cloud (on startup)
        await cache.sync_from_cloud(cloud_client)

        # Get cached configs
        agents = await cache.get_agents()
        tools = await cache.get_tools()

        # Refresh cache (after CRUD operations)
        await cache.refresh_agent(agent_id, cloud_client)
    """

    def __init__(self, cache_dir: str, ttl: int = 300):
        """
        Initialize cloud data cache.

        Args:
            cache_dir: Directory to store cache database
            ttl: Time-to-live for cache entries (seconds), default 5 minutes
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "cloud_data.db"
        self.ttl = ttl

        # In-memory cache for fast access
        self._memory_cache: Dict[str, CacheEntry] = {}

        # Connection (will be initialized)
        self._conn: Optional[sqlite3.Connection] = None

    async def initialize(self):
        """
        Initialize cache database and tables.

        Creates tables:
        - tenant: Tenant info
        - agents: Agent configs
        - tools: Tool configs
        - mcp_servers: MCP server configs
        - groups: Group/channel configs
        - users: User configs
        - cache_metadata: Cache metadata (last sync time, etc.)
        """
        logger.info(f"Initializing cloud data cache at {self.db_path}")

        # Create database connection
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row  # Return dicts instead of tuples

        # Create tables
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS tenant (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS mcp_servers (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_agents_cached_at ON agents(cached_at);
            CREATE INDEX IF NOT EXISTS idx_tools_cached_at ON tools(cached_at);
            CREATE INDEX IF NOT EXISTS idx_mcp_cached_at ON mcp_servers(cached_at);
        """)
        self._conn.commit()

        logger.info("Cache database initialized")

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ============================================================================
    # SYNC FROM CLOUD
    # ============================================================================

    async def sync_from_cloud(self, cloud_client):
        """
        Sync all tenant data from cloud and cache locally.

        This is called on startup to populate the cache.

        Args:
            cloud_client: CloudAPIClient instance

        Example:
            await cache.sync_from_cloud(cloud_client)
        """
        from ..api.cloud_client import CloudAPIClient

        logger.info("Syncing tenant data from cloud...")
        start_time = datetime.utcnow()

        # Fetch all data from cloud
        data = await cloud_client.sync_all_tenant_data()

        # Cache tenant info
        await self._cache_tenant(data["tenant"])

        # Cache agents
        for agent in data["agents"]:
            await self._cache_agent(agent)

        # Cache tools
        for tool in data["tools"]:
            await self._cache_tool(tool)

        # Cache MCP servers
        for mcp in data["mcp_servers"]:
            await self._cache_mcp_server(mcp)

        # Cache groups
        for group in data["groups"]:
            await self._cache_group(group)

        # Cache users
        for user in data["users"]:
            await self._cache_user(user)

        # Update last sync time
        self._set_metadata("last_sync_time", datetime.utcnow().isoformat())

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Sync complete in {elapsed:.2f}s: "
            f"{len(data['agents'])} agents, {len(data['tools'])} tools, "
            f"{len(data['mcp_servers'])} MCP servers, {len(data['groups'])} groups, "
            f"{len(data['users'])} users"
        )

    # ============================================================================
    # TENANT
    # ============================================================================

    async def _cache_tenant(self, tenant_data: Dict[str, Any]):
        """Cache tenant info"""
        self._conn.execute(
            "INSERT OR REPLACE INTO tenant (id, data, cached_at) VALUES (?, ?, ?)",
            (tenant_data["id"], json.dumps(tenant_data), datetime.utcnow())
        )
        self._conn.commit()

        # In-memory cache
        self._memory_cache[f"tenant:{tenant_data['id']}"] = CacheEntry(
            key=f"tenant:{tenant_data['id']}",
            value=tenant_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_tenant(self) -> Optional[Dict[str, Any]]:
        """Get cached tenant info"""
        # Check memory cache first
        for key, entry in self._memory_cache.items():
            if key.startswith("tenant:") and not entry.is_expired():
                return entry.value

        # Check database
        cursor = self._conn.execute("SELECT data FROM tenant LIMIT 1")
        row = cursor.fetchone()
        if row:
            tenant_data = json.loads(row["data"])

            # Update memory cache
            self._memory_cache[f"tenant:{tenant_data['id']}"] = CacheEntry(
                key=f"tenant:{tenant_data['id']}",
                value=tenant_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return tenant_data

        return None

    # ============================================================================
    # AGENTS
    # ============================================================================

    async def _cache_agent(self, agent_data: Dict[str, Any]):
        """Cache single agent"""
        self._conn.execute(
            "INSERT OR REPLACE INTO agents (id, data, cached_at) VALUES (?, ?, ?)",
            (agent_data["id"], json.dumps(agent_data), datetime.utcnow())
        )
        self._conn.commit()

        # In-memory cache
        self._memory_cache[f"agent:{agent_data['id']}"] = CacheEntry(
            key=f"agent:{agent_data['id']}",
            value=agent_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached agent config by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent config dict or None if not found

        Example:
            agent_config = await cache.get_agent("agent-uuid")
            print(agent_config["llm_model"])  # "claude-sonnet-4.5"
        """
        # Check memory cache first
        cache_key = f"agent:{agent_id}"
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        # Check database
        cursor = self._conn.execute("SELECT data FROM agents WHERE id = ?", (agent_id,))
        row = cursor.fetchone()
        if row:
            agent_data = json.loads(row["data"])

            # Update memory cache
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=agent_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return agent_data

        return None

    async def get_agents(self) -> List[Dict[str, Any]]:
        """
        Get all cached agents.

        Returns:
            List of agent configs

        Example:
            agents = await cache.get_agents()
            for agent in agents:
                print(f"{agent['name']}: {agent['llm_model']}")
        """
        cursor = self._conn.execute("SELECT data FROM agents")
        rows = cursor.fetchall()

        agents = []
        for row in rows:
            agent_data = json.loads(row["data"])
            agents.append(agent_data)

            # Update memory cache
            cache_key = f"agent:{agent_data['id']}"
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=agent_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

        return agents

    async def refresh_agent(self, agent_id: str, cloud_client):
        """
        Refresh single agent from cloud.

        Called after updating agent via CRUD.

        Args:
            agent_id: Agent ID
            cloud_client: CloudAPIClient instance
        """
        agent_data = await cloud_client.fetch_agent(agent_id)
        await self._cache_agent(agent_data)
        logger.info(f"Refreshed agent cache: {agent_id}")

    async def delete_agent_from_cache(self, agent_id: str):
        """Delete agent from cache"""
        self._conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        self._conn.commit()

        # Remove from memory cache
        cache_key = f"agent:{agent_id}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        logger.info(f"Deleted agent from cache: {agent_id}")

    # ============================================================================
    # TOOLS
    # ============================================================================

    async def _cache_tool(self, tool_data: Dict[str, Any]):
        """Cache single tool"""
        self._conn.execute(
            "INSERT OR REPLACE INTO tools (id, data, cached_at) VALUES (?, ?, ?)",
            (tool_data["id"], json.dumps(tool_data), datetime.utcnow())
        )
        self._conn.commit()

        # In-memory cache
        self._memory_cache[f"tool:{tool_data['id']}"] = CacheEntry(
            key=f"tool:{tool_data['id']}",
            value=tool_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get cached tool config by ID"""
        # Check memory cache first
        cache_key = f"tool:{tool_id}"
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        # Check database
        cursor = self._conn.execute("SELECT data FROM tools WHERE id = ?", (tool_id,))
        row = cursor.fetchone()
        if row:
            tool_data = json.loads(row["data"])

            # Update memory cache
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=tool_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return tool_data

        return None

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all cached tools.

        Returns:
            List of tool configs with code and dependencies

        Example:
            tools = await cache.get_tools()
            for tool in tools:
                print(f"{tool['name']}: {tool['dependencies']}")
        """
        cursor = self._conn.execute("SELECT data FROM tools")
        rows = cursor.fetchall()

        tools = []
        for row in rows:
            tool_data = json.loads(row["data"])
            tools.append(tool_data)

            # Update memory cache
            cache_key = f"tool:{tool_data['id']}"
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=tool_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

        return tools

    async def refresh_tool(self, tool_id: str, cloud_client):
        """Refresh single tool from cloud"""
        tool_data = await cloud_client.fetch_tool(tool_id)
        await self._cache_tool(tool_data)
        logger.info(f"Refreshed tool cache: {tool_id}")

    async def delete_tool_from_cache(self, tool_id: str):
        """Delete tool from cache"""
        self._conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
        self._conn.commit()

        cache_key = f"tool:{tool_id}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        logger.info(f"Deleted tool from cache: {tool_id}")

    # ============================================================================
    # MCP SERVERS
    # ============================================================================

    async def _cache_mcp_server(self, mcp_data: Dict[str, Any]):
        """Cache single MCP server"""
        self._conn.execute(
            "INSERT OR REPLACE INTO mcp_servers (id, data, cached_at) VALUES (?, ?, ?)",
            (mcp_data["id"], json.dumps(mcp_data), datetime.utcnow())
        )
        self._conn.commit()

        # In-memory cache
        self._memory_cache[f"mcp:{mcp_data['id']}"] = CacheEntry(
            key=f"mcp:{mcp_data['id']}",
            value=mcp_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_mcp_server(self, mcp_id: str) -> Optional[Dict[str, Any]]:
        """Get cached MCP server config by ID"""
        cache_key = f"mcp:{mcp_id}"
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        cursor = self._conn.execute("SELECT data FROM mcp_servers WHERE id = ?", (mcp_id,))
        row = cursor.fetchone()
        if row:
            mcp_data = json.loads(row["data"])

            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=mcp_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return mcp_data

        return None

    async def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """
        Get all cached MCP servers.

        Returns:
            List of MCP server configs

        Example:
            mcp_servers = await cache.get_mcp_servers()
            for mcp in mcp_servers:
                print(f"{mcp['name']}: {mcp['command']} {mcp['args']}")
        """
        cursor = self._conn.execute("SELECT data FROM mcp_servers")
        rows = cursor.fetchall()

        mcp_servers = []
        for row in rows:
            mcp_data = json.loads(row["data"])
            mcp_servers.append(mcp_data)

            cache_key = f"mcp:{mcp_data['id']}"
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=mcp_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

        return mcp_servers

    async def refresh_mcp_server(self, mcp_id: str, cloud_client):
        """Refresh single MCP server from cloud"""
        mcp_data = await cloud_client.fetch_mcp_server(mcp_id)
        await self._cache_mcp_server(mcp_data)
        logger.info(f"Refreshed MCP server cache: {mcp_id}")

    async def delete_mcp_server_from_cache(self, mcp_id: str):
        """Delete MCP server from cache"""
        self._conn.execute("DELETE FROM mcp_servers WHERE id = ?", (mcp_id,))
        self._conn.commit()

        cache_key = f"mcp:{mcp_id}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        logger.info(f"Deleted MCP server from cache: {mcp_id}")

    # ============================================================================
    # GROUPS
    # ============================================================================

    async def _cache_group(self, group_data: Dict[str, Any]):
        """Cache single group"""
        self._conn.execute(
            "INSERT OR REPLACE INTO groups (id, data, cached_at) VALUES (?, ?, ?)",
            (group_data["id"], json.dumps(group_data), datetime.utcnow())
        )
        self._conn.commit()

        self._memory_cache[f"group:{group_data['id']}"] = CacheEntry(
            key=f"group:{group_data['id']}",
            value=group_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get cached group by ID"""
        cache_key = f"group:{group_id}"
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        cursor = self._conn.execute("SELECT data FROM groups WHERE id = ?", (group_id,))
        row = cursor.fetchone()
        if row:
            group_data = json.loads(row["data"])

            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=group_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return group_data

        return None

    async def get_groups(self) -> List[Dict[str, Any]]:
        """Get all cached groups"""
        cursor = self._conn.execute("SELECT data FROM groups")
        rows = cursor.fetchall()

        groups = []
        for row in rows:
            group_data = json.loads(row["data"])
            groups.append(group_data)

            cache_key = f"group:{group_data['id']}"
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=group_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

        return groups

    async def refresh_group(self, group_id: str, cloud_client):
        """Refresh single group from cloud"""
        group_data = await cloud_client.fetch_group(group_id)
        await self._cache_group(group_data)
        logger.info(f"Refreshed group cache: {group_id}")

    async def delete_group_from_cache(self, group_id: str):
        """Delete group from cache"""
        self._conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        self._conn.commit()

        cache_key = f"group:{group_id}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        logger.info(f"Deleted group from cache: {group_id}")

    # ============================================================================
    # USERS
    # ============================================================================

    async def _cache_user(self, user_data: Dict[str, Any]):
        """Cache single user"""
        self._conn.execute(
            "INSERT OR REPLACE INTO users (id, data, cached_at) VALUES (?, ?, ?)",
            (user_data["id"], json.dumps(user_data), datetime.utcnow())
        )
        self._conn.commit()

        self._memory_cache[f"user:{user_data['id']}"] = CacheEntry(
            key=f"user:{user_data['id']}",
            value=user_data,
            cached_at=datetime.utcnow(),
            ttl=self.ttl
        )

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user by ID"""
        cache_key = f"user:{user_id}"
        if cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        cursor = self._conn.execute("SELECT data FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            user_data = json.loads(row["data"])

            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=user_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

            return user_data

        return None

    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all cached users"""
        cursor = self._conn.execute("SELECT data FROM users")
        rows = cursor.fetchall()

        users = []
        for row in rows:
            user_data = json.loads(row["data"])
            users.append(user_data)

            cache_key = f"user:{user_data['id']}"
            self._memory_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=user_data,
                cached_at=datetime.utcnow(),
                ttl=self.ttl
            )

        return users

    async def refresh_user(self, user_id: str, cloud_client):
        """Refresh single user from cloud"""
        user_data = await cloud_client.fetch_user(user_id)
        await self._cache_user(user_data)
        logger.info(f"Refreshed user cache: {user_id}")

    async def delete_user_from_cache(self, user_id: str):
        """Delete user from cache"""
        self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self._conn.commit()

        cache_key = f"user:{user_id}"
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        logger.info(f"Deleted user from cache: {user_id}")

    # ============================================================================
    # METADATA
    # ============================================================================

    def _set_metadata(self, key: str, value: str):
        """Set cache metadata"""
        self._conn.execute(
            "INSERT OR REPLACE INTO cache_metadata (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.utcnow())
        )
        self._conn.commit()

    def _get_metadata(self, key: str) -> Optional[str]:
        """Get cache metadata"""
        cursor = self._conn.execute("SELECT value FROM cache_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else None

    async def get_last_sync_time(self) -> Optional[datetime]:
        """Get last sync time from cloud"""
        value = self._get_metadata("last_sync_time")
        if value:
            return datetime.fromisoformat(value)
        return None

    async def clear_all_cache(self):
        """Clear all cached data"""
        self._conn.executescript("""
            DELETE FROM tenant;
            DELETE FROM agents;
            DELETE FROM tools;
            DELETE FROM mcp_servers;
            DELETE FROM groups;
            DELETE FROM users;
            DELETE FROM cache_metadata;
        """)
        self._conn.commit()

        # Clear memory cache
        self._memory_cache.clear()

        logger.info("Cleared all cache data")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_cloud_cache: Optional[CloudDataCache] = None


def get_cloud_cache() -> CloudDataCache:
    """
    Get singleton cloud cache instance.

    Must be initialized first via initialize_cloud_cache().

    Example:
        cache = get_cloud_cache()
        agents = await cache.get_agents()
    """
    global _cloud_cache
    if _cloud_cache is None:
        raise RuntimeError("Cloud cache not initialized. Call initialize_cloud_cache() first.")
    return _cloud_cache


async def initialize_cloud_cache(cache_dir: str, ttl: int = 300) -> CloudDataCache:
    """
    Initialize singleton cloud cache instance.

    Called on startup with cache directory from settings.

    Args:
        cache_dir: Directory to store cache database
        ttl: Time-to-live for cache entries (seconds)

    Example:
        cache = await initialize_cloud_cache("/home/user/.agentverse/cache")
    """
    global _cloud_cache
    _cloud_cache = CloudDataCache(cache_dir, ttl)
    await _cloud_cache.initialize()
    logger.info(f"Cloud cache initialized at {cache_dir}")
    return _cloud_cache


def shutdown_cloud_cache():
    """Shutdown cloud cache (close database connection)"""
    global _cloud_cache
    if _cloud_cache:
        _cloud_cache.close()
        _cloud_cache = None
        logger.info("Cloud cache shut down")
