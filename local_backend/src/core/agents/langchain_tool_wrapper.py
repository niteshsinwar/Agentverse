"""
LangChain Tool Wrapper - Simplified

Converts all tools (custom + MCP + meta) into standard LangChain tools.
Zero glue code - pure LangChain standards.
"""

import inspect
import json
import time
from typing import List, Dict, Any

from langchain.tools import StructuredTool

from src.core.memory import session_store
from src.core.telemetry.events import emit_tool_call, emit_tool_result, emit_error, emit_mcp_call


class LangChainToolWrapper:
    """
    Simple wrapper that converts tools to LangChain format.

    No glue code, no custom JSON parsing - just standard LangChain.
    """

    def __init__(
        self,
        custom_tools: List[Any],
        mcp_servers: Dict[str, Any],
        agent_id: str
    ):
        self.custom_tools = custom_tools or []
        self.mcp_servers = mcp_servers or {}
        self.agent_id = agent_id

    def get_all_tools(self, group_id: str) -> List[StructuredTool]:
        """
        Get ALL tools as standard LangChain Tools.

        Returns:
        - Custom tools (from tools.py)
        - MCP tools (from MCP servers)
        - reflect (meta-tool for internal thoughts - LangGraph only)

        LangGraph handles:
        - Native function calling (automatic)
        - JSON schema validation (automatic)
        - Sequential execution (automatic)
        - Error handling (automatic)
        """
        tools = []

        # Custom tools
        for tool in self.custom_tools:
            tools.append(self._wrap_custom_tool(tool, group_id))

        # MCP tools
        for server_name, server in self.mcp_servers.items():
            # MCPServerConnection has _tools_cache (List[MCPTool])
            for mcp_tool in server._tools_cache:
                tools.append(self._wrap_mcp_tool(server_name, mcp_tool, group_id))

        # Add reflect tool for internal reasoning (LangGraph needs this explicitly)
        tools.append(self._create_reflect_tool(group_id))

        return tools

    def _create_reflect_tool(self, group_id: str) -> StructuredTool:
        """
        Create reflect tool for internal reasoning/thoughts.

        LangGraph uses function calling, so we need an explicit tool
        for the agent to express internal thoughts.
        """
        agent_id = self.agent_id

        async def reflect_impl(thought: str) -> str:
            """
            Internal reflection tool - agent uses this to think out loud.

            Args:
                thought: The agent's internal reasoning or planning

            Returns:
                Confirmation message
            """
            start_time = time.time()

            # Persist thought to DB
            session_store.append_message(
                group_id=group_id,
                sender=agent_id,
                role="agent_thought",
                content=thought,
                metadata={
                    "type": "langgraph_reflection",
                    "agent_id": agent_id,
                    "tool_type": "meta"
                }
            )

            # Emit SSE event
            from src.core.telemetry.events import emit_agent_thought
            await emit_agent_thought(
                group_id=group_id,
                agent_key=agent_id,
                thought=thought,
                meta={"type": "langgraph_reflection"}
            )

            duration_ms = (time.time() - start_time) * 1000

            # Emit tool call event for consistency
            await emit_tool_call(
                group_id, agent_id, "reflect", "success",
                {"duration_ms": duration_ms, "tool_type": "meta"}
            )

            return "Reflection recorded. Continue with your task."

        return StructuredTool.from_function(
            func=reflect_impl,
            coroutine=reflect_impl,  # Same function for sync and async
            name="reflect",
            description=(
                "Use this tool to express your internal thoughts, reasoning, or planning. "
                "Call this BEFORE taking actions to show your thinking process. "
                "This helps users understand your decision-making."
            )
        )

    def _wrap_custom_tool(self, tool: Any, group_id: str) -> StructuredTool:
        """
        Wrap custom tool with telemetry + persistence.

        LangChain pattern: func and coroutine must have IDENTICAL signatures.
        - func: Used for schema inference (reads parameters)
        - coroutine: Used for async execution (with telemetry)
        """
        tool_func = tool.get("execute")
        tool_name = tool["name"]
        tool_description = tool.get("description", f"Tool: {tool_name}")
        agent_id = self.agent_id

        # LangChain will pass args/kwargs based on the func signature
        # We DON'T need to manually copy signatures - just pass through

        # Create async wrapper with telemetry
        async def async_tool_with_telemetry(*args, **kwargs):
            start_time = time.time()

            # Combine args and kwargs for display
            all_params = kwargs.copy()
            if args:
                # If positional args exist, they're likely from LangChain passing single dict
                if len(args) == 1 and isinstance(args[0], dict):
                    all_params = args[0]
                else:
                    all_params['_positional_args'] = args

            # Persist tool call to DB (before execution)
            session_store.append_message(
                group_id=group_id,
                sender=agent_id,
                role="tool_call",
                content=f"🔧 Tool call: {tool_name}\n" + json.dumps(all_params, ensure_ascii=False, default=str, indent=2)[:1000],
                metadata={"tool": tool_name, "params": all_params, "tool_type": "custom"}
            )

            # Emit SSE event for tool call
            await emit_tool_call(group_id, agent_id, tool_name, "calling", {"params": all_params, "tool_type": "custom"})

            try:
                # Call original tool with both args and kwargs
                result = tool_func(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result

                duration_ms = (time.time() - start_time) * 1000

                # Persist tool result to DB
                session_store.append_message(
                    group_id=group_id,
                    sender=agent_id,
                    role="tool_result",
                    content=f"✅ Tool result: {tool_name}\nresult: " + json.dumps(result, ensure_ascii=False, default=str)[:2000],
                    metadata={"tool": tool_name, "result": result, "tool_type": "custom"}
                )

                # Emit SSE events for tool result
                await emit_tool_call(group_id, agent_id, tool_name, "success", {"duration_ms": duration_ms, "params": kwargs, "tool_type": "custom"})
                await emit_tool_result(group_id, agent_id, tool_name, str(result)[:100], {"duration_ms": duration_ms, "tool_type": "custom"})

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                session_store.append_message(
                    group_id=group_id,
                    sender=agent_id,
                    role="tool_error",
                    content=f"❌ Tool error: {tool_name}\nerror: {str(e)}",
                    metadata={"tool": tool_name, "error": str(e), "error_type": type(e).__name__, "tool_type": "custom"}
                )
                await emit_error(group_id, f"tool_call:{tool_name}", str(e), {"agent_id": agent_id, "duration_ms": duration_ms, "tool_type": "custom"})
                raise

        # Create StructuredTool - LangChain will infer schema from tool_func
        # and call async_tool_with_telemetry for execution
        return StructuredTool.from_function(
            func=tool_func,                      # For schema inference (original function)
            coroutine=async_tool_with_telemetry, # For execution with telemetry
            name=tool_name,
            description=tool_description
        )

    def _wrap_mcp_tool(self, server_name: str, mcp_tool, group_id: str) -> StructuredTool:
        """
        Wrap MCP tool with telemetry + persistence.

        Args:
            server_name: Name of MCP server
            mcp_tool: MCPTool dataclass instance
            group_id: Current group ID

        LangChain pattern: func and coroutine must have IDENTICAL signatures.
        """
        full_tool_name = f"{server_name}_{mcp_tool.name}"
        tool_description = mcp_tool.description or f"MCP tool: {full_tool_name}"
        agent_id = self.agent_id

        # Get the MCP server connection
        mcp_server = self.mcp_servers[server_name]

        # Create async wrapper with telemetry
        async def async_mcp_with_telemetry(**kwargs):
            start_time = time.time()

            # Persist MCP call to DB (before execution)
            session_store.append_message(
                group_id=group_id,
                sender=agent_id,
                role="mcp_call",
                content=f"🔧 MCP call: {server_name}/{mcp_tool.name}\n" + json.dumps(kwargs, ensure_ascii=False, default=str, indent=2)[:1000],
                metadata={"server": server_name, "tool": mcp_tool.name, "params": kwargs, "tool_type": "mcp"}
            )

            # Emit SSE event for MCP call
            await emit_mcp_call(group_id, agent_id, server_name, mcp_tool.name, "calling", {"params": kwargs, "tool_type": "mcp"})

            try:
                # Call MCP server's call_tool method
                result = await mcp_server.call_tool(mcp_tool.name, kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Persist MCP result to DB
                session_store.append_message(
                    group_id=group_id,
                    sender=agent_id,
                    role="mcp_result",
                    content=f"✅ MCP result: {server_name}/{mcp_tool.name}\nresult: " + json.dumps(result, ensure_ascii=False, default=str)[:2000],
                    metadata={"server": server_name, "tool": mcp_tool.name, "result": result, "tool_type": "mcp"}
                )

                # Emit SSE event for MCP success
                await emit_mcp_call(group_id, agent_id, server_name, mcp_tool.name, "success", {"duration_ms": duration_ms, "result_preview": str(result)[:200], "tool_type": "mcp"})

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                session_store.append_message(
                    group_id=group_id,
                    sender=agent_id,
                    role="mcp_error",
                    content=f"❌ MCP error: {server_name}/{mcp_tool.name}\nerror: {str(e)}",
                    metadata={"server": server_name, "tool": mcp_tool.name, "error": str(e), "error_type": type(e).__name__, "tool_type": "mcp"}
                )
                await emit_error(group_id, f"mcp_call:{server_name}/{mcp_tool.name}", str(e), {"agent_id": agent_id, "duration_ms": duration_ms, "tool_type": "mcp"})
                raise

        # Create StructuredTool - LangChain will infer schema from parameters
        return StructuredTool.from_function(
            coroutine=async_mcp_with_telemetry,
            name=full_tool_name,
            description=tool_description,
            args_schema=mcp_tool.parameters if mcp_tool.parameters else None
        )

    def get_tools_summary(self) -> str:
        """Simple summary for system prompt."""
        custom_count = len(self.custom_tools)
        # MCPServerConnection has _tools_cache (List[MCPTool])
        mcp_count = sum(len(s._tools_cache) for s in self.mcp_servers.values())

        return f"Available tools: {custom_count} custom, {mcp_count} MCP"
