# =========================================
# File: app/mcp/client.py
# Purpose: Per-agent MCP runner + transparent telemetry on invokes
# =========================================
from __future__ import annotations
from typing import Any, Dict, List, Optional
import subprocess
import os
import json
import asyncio
from app.telemetry.events import emit_mcp_call


class MCPServerHandle:
    def __init__(self, name: str, spec: Dict[str, Any]) -> None:
        self.name = name
        self.spec = spec
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.tools_cache: List[Dict[str, Any]] = []  # fill after handshake if desired


class MCPManager:
    def __init__(self) -> None:
        self.servers: Dict[str, MCPServerHandle] = {}

    @classmethod
    def from_config(cls, mcp_json: dict) -> "MCPManager":
        inst = cls()
        servers = (mcp_json or {}).get("mcpServers", {})
        for name, spec in servers.items():
            inst.servers[name] = MCPServerHandle(name, spec)
            # NOTE: For brevity we avoid launching now; spawn lazily on first invoke
        return inst

    def list_all_tools(self) -> List[Dict[str, Any]]:
        # If your MCP servers expose tool discovery, populate tools_cache
        out: List[Dict[str, Any]] = []
        for h in self.servers.values():
            for t in h.tools_cache:
                out.append({"server": h.name, **t})
        return out

    async def _ensure_server(self, handle: MCPServerHandle) -> None:
        if handle.proc is not None:
            return
        cmd = [handle.spec.get("command")] + handle.spec.get("args", [])
        env = os.environ.copy()
        env.update(handle.spec.get("env", {}))
        handle.proc = await asyncio.create_subprocess_exec(*cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, env=env)

    async def invoke(self, group_id: str, agent_key: str, server_name: str, tool_name: str, **params) -> Any:
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server '{server_name}'")
        handle = self.servers[server_name]
        
        # Save MCP call start as message
        from app.memory import session_store
        mcp_start_msg = f"🔧 **MCP Call:** `{server_name}/{tool_name}({', '.join(f'{k}={v}' for k, v in params.items())})`"
        session_store.append_message(group_id, sender=agent_key, role="mcp_call", content=mcp_start_msg,
                                   metadata={"server": server_name, "tool_name": tool_name, "params": params, "status": "start"})
        
        await emit_mcp_call(group_id, agent_key, server_name, tool_name, status="start", meta={"params": params})
        try:
            await self._ensure_server(handle)
            # --- Implement MCP stdio protocol here ---
            # For demo we just echo
            result = {"echo": {"server": server_name, "tool": tool_name, "params": params}}
            
            # Save MCP result as message  
            result_preview = str(result)
            if len(result_preview) > 200:
                result_preview = result_preview[:200] + "..."
            mcp_result_msg = f"📤 **MCP Result:** `{server_name}/{tool_name}` → {result_preview}"
            session_store.append_message(group_id, sender=agent_key, role="mcp_result", content=mcp_result_msg,
                                       metadata={"server": server_name, "tool_name": tool_name, "result": str(result)})
            
            await emit_mcp_call(group_id, agent_key, server_name, tool_name, status="end")
            return result
        except Exception as e:
            # Save MCP error as message
            error_msg = f"❌ **MCP Error:** `{server_name}/{tool_name}` → {str(e)}"
            session_store.append_message(group_id, sender=agent_key, role="mcp_error", content=error_msg,
                                       metadata={"server": server_name, "tool_name": tool_name, "error": str(e)})
            await emit_mcp_call(group_id, agent_key, server_name, tool_name, status="error", meta={"error": str(e)})
            raise


mcp_manager = MCPManager()
