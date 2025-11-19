"""
Cloud Agent Loader - Load agents from cloud cache instead of agent_store

This module provides an alternative to registry.py for loading agents when cloud
integration is enabled. Instead of reading from agent_store/ directory, it loads
agent configs from the local cloud cache (synced from Django backend).

Data Flow:
1. Cloud cache synced on startup (agents, tools, MCP configs)
2. Cloud agent loader reads from cache
3. Builds BaseAgent instances with cached configs
4. Agent execution uses cached tools and MCP servers

Benefits:
- CRUD operations use cloud (centralized, multi-user)
- Execution uses cached configs (fast, offline-capable)
- No need to maintain local agent_store/ directory

Author: AgentVerse Team
"""

import importlib.util
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging

from src.core.agents.base_agent import BaseAgent
from src.core.mcp.client import MCPManager
from src.core.cache import get_cloud_cache

logger = logging.getLogger(__name__)


@dataclass
class CloudAgentSpec:
    """Agent specification from cloud cache"""
    key: str  # Agent ID
    name: str
    description: str
    emoji: str
    llm: Dict[str, str]  # LLM configuration with provider and model
    system_prompt: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None  # Tool configs
    mcp_servers: Optional[List[Dict[str, Any]]] = None  # MCP server configs


async def discover_cloud_agents() -> Dict[str, CloudAgentSpec]:
    """
    Discover agents from cloud cache.

    This is the cloud alternative to registry.discover_agents().
    Instead of reading from agent_store/ directory, it loads from cloud cache.

    Returns:
        Dict mapping agent_id -> CloudAgentSpec

    Example:
        agents = await discover_cloud_agents()
        for agent_id, spec in agents.items():
            print(f"{spec.name}: {spec.llm['model']}")
    """
    try:
        cache = get_cloud_cache()
        agents_data = await cache.get_agents()

        agents: Dict[str, CloudAgentSpec] = {}

        for agent_data in agents_data:
            agent_id = agent_data["id"]

            # Extract LLM configuration
            llm_config = {
                "provider": agent_data.get("llm_provider", "openai"),
                "model": agent_data.get("llm_model", "gpt-4o-mini")
            }

            # Get tools for this agent (filtered by agent assignment)
            tools_data = await cache.get_tools()
            agent_tools = []
            # TODO: Filter tools assigned to this agent
            # For now, include all tools (will be filtered by permissions later)

            # Get MCP servers for this agent
            mcp_data = await cache.get_mcp_servers()
            agent_mcp = []
            # TODO: Filter MCP servers assigned to this agent

            agents[agent_id] = CloudAgentSpec(
                key=agent_id,
                name=agent_data.get("name", "Unnamed Agent"),
                description=agent_data.get("description", ""),
                emoji=agent_data.get("config", {}).get("emoji", "🤖"),
                llm=llm_config,
                system_prompt=agent_data.get("system_prompt"),
                config=agent_data.get("config", {}),
                tools=agent_tools,
                mcp_servers=agent_mcp
            )

        logger.info(f"Discovered {len(agents)} agents from cloud cache")
        return agents

    except Exception as e:
        logger.error(f"Failed to discover agents from cloud cache: {e}")
        return {}


def _create_temp_tools_module(tools_data: List[Dict[str, Any]]) -> Optional[Any]:
    """
    Create temporary Python module from tool code stored in cloud.

    Takes tool code from cloud cache and creates an importable Python module.
    This allows tools to be executed as if they were in tools.py file.

    Args:
        tools_data: List of tool configs with code from cloud

    Returns:
        Python module with tool functions

    Example tool_data format:
        {
            "id": "tool-uuid",
            "name": "web_search",
            "code": "from langchain.tools import tool\n@tool\ndef web_search(query: str)...",
            "dependencies": ["requests", "beautifulsoup4"]
        }
    """
    if not tools_data:
        return None

    try:
        # Combine all tool code into single module
        combined_code = "\n\n".join([
            tool["code"] for tool in tools_data
            if tool.get("code")
        ])

        if not combined_code:
            return None

        # Create temporary file for tools module
        # Use timestamp for unique module name
        module_name = f"cloud_agent_tools_{int(time.time() * 1000000)}"

        # Clean up old modules to prevent memory leaks
        old_modules = [k for k in sys.modules.keys() if k.startswith("cloud_agent_tools_")]
        for old_mod in old_modules:
            del sys.modules[old_mod]

        # Create temporary Python file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(combined_code)
            temp_path = f.name

        # Import the temporary module
        spec = importlib.util.spec_from_file_location(module_name, temp_path)
        if spec is None or spec.loader is None:
            os.unlink(temp_path)
            return None

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Clean up temporary file
        os.unlink(temp_path)

        return mod

    except Exception as e:
        logger.error(f"Failed to create tools module from cloud data: {e}")
        return None


def _create_mcp_config_from_cloud(mcp_servers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create MCP configuration from cloud MCP server configs.

    Converts cloud MCP server configs to the format expected by MCPManager.

    Args:
        mcp_servers: List of MCP server configs from cloud

    Returns:
        MCP config dict in format:
        {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
                    "env": {"KEY": "value"}
                }
            }
        }

    Example cloud MCP server format:
        {
            "id": "mcp-uuid",
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
            "env": {"KEY": "value"}
        }
    """
    if not mcp_servers:
        return {}

    mcp_config = {"mcpServers": {}}

    for mcp in mcp_servers:
        server_name = mcp.get("name", "")
        if not server_name:
            continue

        mcp_config["mcpServers"][server_name] = {
            "command": mcp.get("command", ""),
            "args": mcp.get("args", []),
            "env": mcp.get("env", {})
        }

    return mcp_config


async def build_cloud_agent(spec: CloudAgentSpec) -> BaseAgent:
    """
    Build agent from cloud cache data.

    This is the cloud alternative to registry.build_agent().
    Instead of reading from agent_store/ directory, it builds agent
    from cached cloud configs.

    Args:
        spec: CloudAgentSpec with agent metadata and configs

    Returns:
        Initialized BaseAgent instance

    Example:
        agents = await discover_cloud_agents()
        for agent_id, spec in agents.items():
            agent = await build_cloud_agent(spec)
            response = await agent.respond("Hello", group_id="group-1")
    """
    # Create base agent with LLM config
    agent = BaseAgent(agent_id=spec.key, llm_config=spec.llm)

    # Load metadata
    # Note: folder_path is set to temp directory since we don't use agent_store
    temp_folder = Path(tempfile.gettempdir()) / "agentverse_agents" / spec.key
    temp_folder.mkdir(parents=True, exist_ok=True)

    agent.load_metadata(
        name=spec.name,
        description=spec.description,
        folder_path=str(temp_folder)
    )

    # Set system prompt if available
    if spec.system_prompt:
        # TODO: Add system prompt to BaseAgent
        # For now, it will be handled by context builder
        pass

    # Attach MCP manager if MCP servers are configured
    if spec.mcp_servers:
        mcp_config = _create_mcp_config_from_cloud(spec.mcp_servers)
        if mcp_config.get("mcpServers"):
            mcp_manager = MCPManager.from_config(mcp_config)
            agent.attach_mcp(mcp_manager)

            # Auto-discover tools from MCP servers
            if mcp_manager.servers:
                await mcp_manager.discover_tools()

    # Register tools from cloud cache
    if spec.tools:
        tools_module = _create_temp_tools_module(spec.tools)
        if tools_module:
            agent.register_tools_from_module(tools_module)

    logger.info(f"Built agent from cloud cache: {spec.name} ({spec.key})")
    return agent


async def refresh_cloud_agent(agent_id: str) -> Optional[BaseAgent]:
    """
    Refresh single agent from cloud cache.

    Called after updating agent via CRUD to get latest config.

    Args:
        agent_id: Agent ID

    Returns:
        Updated BaseAgent instance or None if not found

    Example:
        # After updating agent via API
        updated_agent = await refresh_cloud_agent("agent-uuid")
    """
    try:
        cache = get_cloud_cache()
        agent_data = await cache.get_agent(agent_id)

        if not agent_data:
            logger.warning(f"Agent not found in cache: {agent_id}")
            return None

        # Build CloudAgentSpec
        llm_config = {
            "provider": agent_data.get("llm_provider", "openai"),
            "model": agent_data.get("llm_model", "gpt-4o-mini")
        }

        spec = CloudAgentSpec(
            key=agent_id,
            name=agent_data.get("name", "Unnamed Agent"),
            description=agent_data.get("description", ""),
            emoji=agent_data.get("config", {}).get("emoji", "🤖"),
            llm=llm_config,
            system_prompt=agent_data.get("system_prompt"),
            config=agent_data.get("config", {}),
            tools=[],  # TODO: Get agent tools
            mcp_servers=[]  # TODO: Get agent MCP servers
        )

        # Build and return agent
        return await build_cloud_agent(spec)

    except Exception as e:
        logger.error(f"Failed to refresh agent from cloud cache: {e}")
        return None


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
Example: Switch between local agent_store and cloud cache

# OLD WAY (local agent_store):
from src.core.agents.registry import discover_agents, build_agent

agents_specs = discover_agents()
for agent_id, spec in agents_specs.items():
    agent = await build_agent(spec)


# NEW WAY (cloud cache):
from src.core.agents.cloud_agent_loader import discover_cloud_agents, build_cloud_agent

agent_specs = await discover_cloud_agents()
for agent_id, spec in agent_specs.items():
    agent = await build_cloud_agent(spec)
"""
