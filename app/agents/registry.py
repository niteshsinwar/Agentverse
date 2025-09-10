# File: app/agents/registry.py
# Purpose: Discover + construct agents from folders (agent.yaml + mcp.json + tools.py)
# =========================================
from __future__ import annotations
import os, json, yaml, importlib.util
from dataclasses import dataclass
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.mcp.client import mcp_manager, MCPManager


AGENTS_ROOT = os.path.join("app", "agents")


@dataclass
class AgentSpec:
    key: str
    name: str
    description: str
    folder: str
    mcp_config: Dict[str, Any]
    emoji: str = "🔧"  # Default emoji if not specified
    tools_module: Optional[str] = None


def _load_yaml(p: str) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _import_tools_py(path: str):
    if not os.path.exists(path):
        return None
    # Use unique module name with timestamp to avoid caching issues
    import time
    agent_dir = os.path.basename(os.path.dirname(path))
    module_name = f"agent_tools_{agent_dir}_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def discover_agents() -> Dict[str, AgentSpec]:
    agents: Dict[str, AgentSpec] = {}
    for entry in os.listdir(AGENTS_ROOT):
        full = os.path.join(AGENTS_ROOT, entry)
        if not os.path.isdir(full):
            continue
        if entry.startswith("__"):  # __pycache__
            continue
        ay = os.path.join(full, "agent.yaml")
        mj = os.path.join(full, "mcp.json")
        if os.path.exists(ay) and os.path.exists(mj):
            meta = _load_yaml(ay)
            with open(mj, "r", encoding="utf-8") as f:
                mcp = json.load(f)
            tools_py = os.path.join(full, "tools.py")
            agents[entry] = AgentSpec(
                key=entry,
                name=meta.get("name", entry),
                description=meta.get("description", ""),
                folder=full,
                mcp_config=mcp,
                emoji=meta.get("emoji", "🔧"),  # Read emoji from agent.yaml
                tools_module=tools_py if os.path.exists(tools_py) else None,
            )
    return agents


async def build_agent(spec: AgentSpec) -> BaseAgent:
    agent = BaseAgent(agent_id=spec.key)
    agent.load_metadata(name=spec.name, description=spec.description, folder_path=spec.folder)
    # Attach a dedicated MCP manager (per-agent JSON)
    mcp_manager = MCPManager.from_config(spec.mcp_config)
    agent.attach_mcp(mcp_manager)
    
    # Auto-start MCP servers to discover tools at initialization
    if mcp_manager.servers:
        await mcp_manager.start_all()
    
    if spec.tools_module:
        mod = _import_tools_py(spec.tools_module)
        if mod:
            agent.register_tools_from_module(mod)
    return agent
