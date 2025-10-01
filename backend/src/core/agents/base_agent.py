# =========================================
# File: app/agents/base_agent.py  
# Purpose: Agent decides: respond vs custom tool vs MCP vs other agent, with multi-step control loop
# =========================================
from __future__ import annotations
import json
import inspect
import re
from typing import Any, Callable, Optional, Dict, List
from src.core.llm.factory import get_llm

# Import structured response models
from .response_models import parse_agent_response, get_response_schema, FinalResponse, ToolCallResponse, MCPCallResponse

# Agent memory system is handled through session_store
# No separate memory manager needed

# Constants
MAX_CONVERSATION_HISTORY = 20  # Number of recent messages to include in context
MAX_PLANNING_STEPS = 8         # Maximum steps for agent planning loop
MAX_VALIDATION_ATTEMPTS = 3    # Maximum attempts to fix @mention validation


def agent_tool(fn: Callable):
    setattr(fn, "__agent_tool__", True)
    return fn


class BaseAgent:
    def __init__(self, agent_id: str, llm_config: Optional[Dict[str, str]] = None):
        self.agent_id = agent_id
        self.metadata: Dict[str, Any] = {}
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.mcp = None
        self.llm_config = llm_config or {"provider": "openai", "model": "gpt-4o-mini"}

        # Memory is handled through session_store conversation history

    def load_metadata(self, name: str, description: str, folder_path: str):
        self.metadata = {"name": name, "description": description, "folder_path": folder_path}

    def attach_mcp(self, mcp_client: Any):
        self.mcp = mcp_client

    def get_capabilities_summary(self) -> str:
        """Return a summary of this agent's capabilities including tools and MCP servers."""
        parts = []
        
        # Add specialty/description
        specialty = self.metadata.get('description', 'General purpose agent')
        parts.append(f"Specialty: {specialty}")
        
        # Add custom tools
        if self.tools:
            tool_details = []
            for name, func in self.tools.items():
                # Get function signature for better tool understanding
                try:
                    sig = inspect.signature(func)
                    params = []
                    for param_name, param in sig.parameters.items():
                        if param.annotation != inspect.Parameter.empty:
                            type_name = getattr(param.annotation, '__name__', str(param.annotation))
                            if param.default != inspect.Parameter.empty:
                                params.append(f"{param_name}: {type_name} = {param.default}")
                            else:
                                params.append(f"{param_name}: {type_name}")
                        else:
                            params.append(param_name)
                    signature = f"{name}({', '.join(params)})"
                    tool_details.append(signature)
                except Exception:
                    tool_details.append(name)
            parts.append(f"Custom tools: {' | '.join(tool_details)}")
        else:
            parts.append("Custom tools: none")
        
        # Add MCP servers with actual tool names
        if self.mcp is None:
            parts.append("MCP servers: none (mcp is None)")
        elif not hasattr(self.mcp, 'servers'):
            parts.append(f"MCP servers: none (mcp has no servers attribute, type: {type(self.mcp)})")
        elif not self.mcp.servers:
            parts.append("MCP servers: none (empty servers dict)")
        else:
            mcp_summary = []
            for server_name, server_handle in self.mcp.servers.items():
                tool_count = len(server_handle.tools_cache)
                if tool_count > 0:
                    # Show first few tool names for context
                    tool_names = [tool.name for tool in server_handle.tools_cache[:3]]
                    if tool_count > 3:
                        tool_names.append(f"...+{tool_count-3} more")
                    mcp_summary.append(f"{server_name}({tool_count} tools: {', '.join(tool_names)})")
                else:
                    mcp_summary.append(f"{server_name}(0 tools)")
            parts.append(f"MCP servers: {' | '.join(mcp_summary)}")
        
        # Add conversation history capabilities
        parts.append("Conversation Memory: enabled via session_store")
        
        result = " | ".join(parts)
        return result

    def register_tools_from_module(self, mod: Any):
        for _, fn in inspect.getmembers(mod, inspect.isfunction):
            if getattr(fn, "__agent_tool__", False):
                self.tools[fn.__name__] = fn

    async def call_tool(self, group_id: str, tool_name: str, **kwargs):
        """Call a custom tool with logging and error handling"""
        # If tool isn't registered, log as error and return structured error (do not raise)
        if tool_name not in self.tools:
            from src.core.memory import session_store
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_error",
                content=f"❌ Tool error: {tool_name}\nerror: Unknown tool",
                metadata={"tool": tool_name, "error": "Unknown tool", "error_type": "UnknownTool"}
            )
            return {"isError": True, "tool": tool_name, "error": "Unknown tool", "error_type": "UnknownTool"}

        from src.core.telemetry.session_logger import session_logger
        from src.core.telemetry.events import emit_tool_call, emit_tool_result, emit_error
        from src.core.memory import session_store
        import time
        import json
        
        start_time = time.time()
        
        try:
            # Persist tool call to conversation history
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_call",
                content=f"🔧 Tool call: {tool_name}\nargs: " + json.dumps(kwargs, ensure_ascii=False, default=str)[:1000],
                metadata={"tool": tool_name, "params": kwargs}
            )
            res = self.tools[tool_name](**kwargs)
            if inspect.isawaitable(res):
                res = await res
            
            duration_ms = (time.time() - start_time) * 1000

            # Log successful tool call
            session_logger.log_tool_call(
                session_id=group_id,
                agent_id=self.agent_id,
                tool_name=tool_name,
                params=kwargs,
                duration_ms=duration_ms,
                result=res
            )

            # Emit real-time events for UI
            await emit_tool_call(group_id, self.agent_id, tool_name, "success", {"duration_ms": duration_ms})
            await emit_tool_result(group_id, self.agent_id, tool_name, str(res)[:100], {"duration_ms": duration_ms})
            # Persist tool result to conversation history
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_result",
                content=f"✅ Tool result: {tool_name}\nresult: " + json.dumps(res, ensure_ascii=False, default=str)[:2000],
                metadata={"tool": tool_name, "result": res}
            )
            
            return res
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log failed tool call
            session_logger.log_tool_call(
                session_id=group_id,
                agent_id=self.agent_id,
                tool_name=tool_name,
                params=kwargs,
                duration_ms=duration_ms,
                error=str(e)
            )

            # Emit real-time error event for UI
            await emit_error(group_id, f"tool_call:{tool_name}", str(e), {"agent_id": self.agent_id, "duration_ms": duration_ms})
            # Persist tool error to conversation history
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_error",
                content=f"❌ Tool error: {tool_name}\nerror: {str(e)}",
                metadata={"tool": tool_name, "error": str(e), "error_type": type(e).__name__}
            )
            # Do not interrupt the agent loop; return error object for planning
            return {"isError": True, "tool": tool_name, "error": str(e), "error_type": type(e).__name__}
    
    
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools for this agent"""
        if not self.mcp:
            return []
        return self.mcp.list_all_tools()

    async def respond(self, prompt: str, group_id: str, orchestrator=None, depth: int = 2) -> str:
        """Multi-step planner loop with structured output parsing.
        Agent responses are parsed using Pydantic models to ensure reliable JSON handling.
        Supported actions: final, call_tool, call_mcp
        """
        # Use agent-specific LLM configuration
        llm = get_llm(
            provider=self.llm_config.get("provider"),
            model=self.llm_config.get("model")
        )
        roster = []
        if orchestrator:
            roster = orchestrator.group_roster(group_id)
        roster_lines = "\n".join([f"- @{k} — {n}: {d}" for (k, n, d) in roster]) or "- (no other members)"

        # CONVERSATION CONTEXT - Get recent conversation history with enhanced context
        from src.core.memory import session_store
        def build_history_context() -> str:
            hist = session_store.get_history(group_id) if group_id else []
            if not hist:
                return ""
            recent = hist[-MAX_CONVERSATION_HISTORY:]  # Get recent messages
            lines: List[str] = []
            last_user_message = ""

            for msg in recent:
                role = msg.get("role", "unknown")
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")

                if role == "user":
                    lines.append(f"User: {content}")
                    last_user_message = content  # Track last user message for context
                elif role == "agent":
                    agent_key = msg.get("metadata", {}).get("agent_key", sender)
                    lines.append(f"{agent_key}: {content}")
                elif role == "system":
                    lines.append(f"[System]: {content}")
                elif role in ("tool_call", "tool_result", "tool_error", "mcp_call", "mcp_result"):
                    lines.append(f"[{role}]: {content}")

            # Add context about who is currently being addressed
            context_note = ""
            if last_user_message and f"@{self.agent_id}" in last_user_message:
                context_note = f"\n📍 IMPORTANT: You ({self.agent_id}) are being directly addressed by the user.\n"
            elif prompt and f"@{self.agent_id}" in prompt:
                # Find who mentioned this agent in the current prompt
                import re
                mention_pattern = r'(\w+):\s*.*@' + re.escape(self.agent_id)
                mention_match = re.search(mention_pattern, prompt)
                if mention_match:
                    mentioner = mention_match.group(1)
                    context_note = f"\n📍 IMPORTANT: You ({self.agent_id}) are being mentioned by {mentioner}.\n"

            return (
                "\n\n=== CONVERSATION HISTORY (Last 20 messages) ===\n"
                + "\n".join(lines)
                + context_note
                + "\n=== END HISTORY ===\n\n"
            )

        history_context = build_history_context()

        # Conversation context is already included in history_context

        
        # Build detailed MCP tools listing for agent awareness
        mcp_tools_detail = ""
        if self.mcp and self.mcp.servers:
            mcp_tools_detail = "\n=== MCP TOOLS AVAILABLE TO YOU ===\n"
            for server_name, server_handle in self.mcp.servers.items():
                if server_handle.tools_cache:
                    mcp_tools_detail += f"Server: {server_name}\n"
                    for tool in server_handle.tools_cache:
                        # Truncate long descriptions
                        desc = tool.description[:100] + "..." if len(tool.description) > 100 else tool.description
                        
                        # Extract required and optional parameters
                        params = tool.parameters.get("properties", {})
                        required_params = tool.parameters.get("required", [])
                        
                        param_info = []
                        for param_name, param_def in params.items():
                            param_desc = param_def.get("description", "")[:50]
                            if len(param_desc) > 47:
                                param_desc = param_desc[:47] + "..."
                            
                            if param_name in required_params:
                                param_info.append(f"{param_name}* ({param_desc})")
                            else:
                                param_info.append(f"{param_name} ({param_desc})")
                        
                        param_str = ", ".join(param_info) if param_info else "none"
                        mcp_tools_detail += f"  - {tool.name}: {desc}\n"
                        mcp_tools_detail += f"    Params: {param_str}\n"
                    mcp_tools_detail += "\n"
            mcp_tools_detail += "To call MCP tools use: {\"action\":\"call_mcp\",\"server\":\"<server>\",\"tool\":\"<tool_name>\",\"params\":{...}}\n"
            mcp_tools_detail += "⚡ Parameters marked with * are REQUIRED. Use exact parameter names shown above.\n"
            mcp_tools_detail += "=== END MCP TOOLS ===\n"

        
        # BUILD COLLABORATIVE PROMPT with structured response schema
        response_schema = get_response_schema()

        sys = (
            f"Agent: {self.agent_id} ({self.metadata.get('name')})\n"
            f"Specialty: {self.metadata.get('description', 'General purpose')}\n"
            f"CAPABILITIES: {self.get_capabilities_summary()}\n"
            f"{mcp_tools_detail}"
            f"Group: {roster_lines}\n"
            f"{history_context}"
            f"{response_schema}\n"
            f"RULES AND GUIDELINES:\n"
            f"- DEFAULT to 'final' action for all normal conversation and responses\n"
            f"- Use 'call_tool' only for your registered tools; if another agent has the tool, use 'final' and delegate\n"
            f"- Use 'call_mcp' only for MCP server operations explicitly requested\n"
            f"- NEVER invent tools - if unavailable, use 'final' to explain or delegate\n"
            f"- 🤖 COLLABORATION STRATEGY:\n"
            f"  • PREFER agent-to-agent collaboration over returning to user\n"
            f"  • Only interact with agents listed in Group section above\n"
            f"  • Delegate appropriately based on agent specialties\n"
            f"- 🎯 MENTION RULES:\n"
            f"  • ALWAYS end responses with exactly ONE @mention\n"
            f"  • If USER mentioned you: respond to @user\n"
            f"  • If AGENT mentioned you: respond to that @agent (see context above)\n"
            f"  • If asking another agent for help: mention that @agent\n"
            f"  • Single-agent groups: always mention @user\n"
            f"  • Continue workflows collaboratively rather than breaking to user\n"
            f"- 🎯 MANDATORY @MENTION RULES:\n"
            f"  • EVERY 'final' response MUST include exactly ONE @mention\n"
            f"  • @user: when conversation complete, user input needed, or errors need attention\n"
            f"  • @agent_name: when delegating, collaborating, or continuing workflows\n"
            f"  • Think: 'Can another agent help?' before defaulting to @user\n"
            f"  • Only mention agents listed in Group section\n"
            f"- When tagged by another agent (@{self.agent_id}), engage collaboratively\n"
            f"- Use structured JSON responses only - system will handle parsing reliably\n"
            f"- Call tools ONE AT A TIME for multi-step operations"
        )

        observations: List[Dict[str, Any]] = []
        last_tool: Optional[str] = None
        last_server: Optional[str] = None

        async def decide(user_or_obs: str) -> Dict[str, Any]:
            # Support both old and new LLM interface
            if hasattr(llm, 'simple_chat'):
                raw = await llm.simple_chat(system=sys, user=user_or_obs)
            else:
                # Fallback to old interface
                raw = await llm.chat(system=sys, user=user_or_obs)

            # Use structured response parsing
            try:
                parsed_response = parse_agent_response(raw)

                # Convert to dict format expected by existing logic
                if isinstance(parsed_response, FinalResponse):
                    return {"action": "final", "text": parsed_response.text}
                elif isinstance(parsed_response, ToolCallResponse):
                    return {"action": "call_tool", "tool_name": parsed_response.tool, "kwargs": parsed_response.inputs}
                elif isinstance(parsed_response, MCPCallResponse):
                    return {"action": "call_mcp", "server": parsed_response.server, "tool": parsed_response.tool, "params": parsed_response.inputs}
                else:
                    # Fallback to final response
                    return {"action": "final", "text": str(parsed_response)}

            except Exception as e:
                print(f"⚠️ Structured parsing failed for {self.agent_id}: {e}")
                print(f"Raw response: {repr(raw)}")
                # Fallback to final response with error notice
                return {"action": "final", "text": f"[Parsing error occurred] {raw} @user"}

        # First decision based on the user prompt
        state = await decide(f"User prompt: {prompt}")
        steps = 0

        while steps < MAX_PLANNING_STEPS:
            steps += 1
            act = (state.get("action") or "").lower()

            if act == "final":
                final_response = state.get("text", "")

                # VALIDATION WALL: Check for mandatory @mentions
                validated_response = await self._validate_and_fix_response(final_response, roster, group_id, sys)

                # Experience is automatically stored in session_store conversation history

                return validated_response

            if act == "call_tool":
                tool = state.get("tool_name")
                kwargs = state.get("kwargs", {})

                # Validate tool exists before calling
                if tool not in self.tools:
                    obs = {"kind": "tool_error", "tool": tool, "result": f"Tool '{tool}' not found. Available tools: {list(self.tools.keys())}"}
                    observations.append(obs)

                    # Update state to continue with error context
                    obs_context = f"Tool '{tool}' not found. Available tools: {list(self.tools.keys())}\nWhat should I do next?"
                    state = await decide(obs_context)
                    continue

                result = await self.call_tool(group_id, tool, **kwargs)
                last_tool = tool
                
                # Feed the observation back to the model
                obs = {"kind": "tool_result", "tool": tool, "result": result}
                observations.append(obs)
                
                # Build context with ALL previous observations AND chat history so agent remembers everything
                # Rebuild history context to include just-written tool_call/result entries
                history_context = build_history_context()
                obs_context = f"Original user request: {prompt}\n\n"
                if history_context.strip():
                    obs_context += history_context + "\n"
                obs_context += "Previous actions taken:\n"
                for i, observation in enumerate(observations, 1):
                    obs_context += f"{i}. {observation['kind']}: {observation['tool']} → {str(observation['result'])[:100]}{'...' if len(str(observation['result'])) > 100 else ''}\n"
                obs_context += f"\nLatest result: {json.dumps(obs, ensure_ascii=False)}\n\nWhat should I do next?"
                
                state = await decide(obs_context)
                continue

            if act == "call_mcp":
                if not self.mcp:
                    obs = {"kind": "mcp_error", "server": "unknown", "tool": "unknown", "result": "MCP not attached to this agent"}
                    observations.append(obs)

                    obs_context = f"MCP not available. No MCP tools can be called.\nWhat should I do next?"
                    state = await decide(obs_context)
                    continue

                server = state.get("server")
                tool = state.get("tool")
                params = state.get("params", {})

                # Validate MCP server and tool exist
                if not server or not tool:
                    obs = {"kind": "mcp_error", "server": server, "tool": tool, "result": "Missing server or tool name"}
                    observations.append(obs)

                    obs_context = f"MCP call failed: Missing server or tool name. Available MCP tools: {self.list_mcp_tools()}\nWhat should I do next?"
                    state = await decide(obs_context)
                    continue
                # Persist MCP call
                from src.core.memory import session_store
                from src.core.telemetry.events import emit_mcp_call, emit_error
                import time

                start_time = time.time()
                session_store.append_message(group_id, sender=self.agent_id, role="mcp_call", content=f"🔧 MCP call: {server}/{tool}\nargs: " + json.dumps(params, ensure_ascii=False, default=str)[:1000], metadata={"server": server, "tool": tool, "params": params})

                # Emit real-time MCP call event for UI
                await emit_mcp_call(group_id, self.agent_id, server, tool, "calling", {"params": params})

                try:
                    result = await self.mcp.invoke(group_id, self.agent_id, server, tool, **params)
                    last_server, last_tool = server, tool
                    duration_ms = (time.time() - start_time) * 1000

                    obs = {"kind": "mcp_result", "server": server, "tool": tool, "result": result}
                    observations.append(obs)

                    # Persist MCP result
                    session_store.append_message(group_id, sender=self.agent_id, role="mcp_result", content=f"✅ MCP result: {server}/{tool}\nresult: " + json.dumps(result, ensure_ascii=False, default=str)[:2000], metadata={"server": server, "tool": tool, "result": result})

                    # Emit real-time MCP result event for UI
                    await emit_mcp_call(group_id, self.agent_id, server, tool, "success", {"duration_ms": duration_ms, "result_preview": str(result)[:200]})

                except Exception as me:
                    duration_ms = (time.time() - start_time) * 1000
                    err_obj = {"isError": True, "server": server, "tool": tool, "error": str(me), "error_type": type(me).__name__}
                    observations.append({"kind": "mcp_error", "server": server, "tool": tool, "error": str(me)})
                    session_store.append_message(group_id, sender=self.agent_id, role="mcp_error", content=f"❌ MCP error: {server}/{tool}\nerror: {str(me)}", metadata=err_obj)

                    # Emit real-time MCP error event for UI
                    await emit_error(group_id, f"mcp_call:{server}/{tool}", str(me), {"agent_id": self.agent_id, "duration_ms": duration_ms})

                    result = err_obj
                
                # Build context with ALL previous observations AND chat history so agent remembers everything
                # Rebuild history context to include just-written mcp_call/result entries
                history_context = build_history_context()
                obs_context = f"Original user request: {prompt}\n\n"
                if history_context.strip():
                    obs_context += history_context + "\n"
                obs_context += "Previous actions taken:\n"
                for i, observation in enumerate(observations, 1):
                    obs_context += f"{i}. {observation['kind']}: {observation['tool']} → {str(observation['result'])[:100]}{'...' if len(str(observation['result'])) > 100 else ''}\n"
                obs_context += f"\nLatest result: {json.dumps(obs, ensure_ascii=False)}\n\nWhat should I do next?"
                
                state = await decide(obs_context)
                continue

            # Unknown action
            return "[error] Unknown action"

        return "[error] Stopped after max planning steps]"

    async def _validate_and_fix_response(self, response: str, roster: List, group_id: str, system_prompt: str, max_attempts: int = MAX_VALIDATION_ATTEMPTS) -> str:
        """
        Validation wall: Ensures response contains exactly one @mention.
        If not, sends response back to agent for correction.
        """
        import re
        from src.core.llm.factory import get_llm

        # Extract @mentions from response
        MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_\-]+)", re.DOTALL)
        mentions = MENTION_PATTERN.findall(response)

        # Get available agent keys from roster (exclude self to prevent infinite loops)
        available_agents = [agent[0] for agent in roster if agent[0] != self.agent_id] + ["user"]

        # Check if response has exactly one @mention
        if len(mentions) == 1:
            mentioned_agent = mentions[0]
            # Validate mention is to a valid agent or user
            if mentioned_agent in available_agents:
                return response
            else:
                # Invalid mention target - need to fix
                mentions = []  # Treat as no valid mention

        # Invalid response - needs correction
        attempt = 0
        current_response = response

        while attempt < max_attempts:
            attempt += 1
            print(f"🔄 Validation wall: Response from {self.agent_id} attempt {attempt} - fixing missing/multiple @mentions")

            # Prepare validation error message
            if len(mentions) == 0:
                error_msg = (
                    f"⚠️ VALIDATION ERROR: Your response is missing a required @mention.\n"
                    f"MANDATORY: Every response must include exactly ONE @mention.\n"
                    f"Available options: @user, {', '.join(f'@{agent[0]}' for agent in roster)}\n\n"
                    f"Your original response:\n{current_response}\n\n"
                    f"Please rewrite your response including exactly one appropriate @mention:"
                )
            else:
                error_msg = (
                    f"⚠️ VALIDATION ERROR: Your response has {len(mentions)} @mentions but exactly ONE is required.\n"
                    f"Found mentions: {', '.join(f'@{m}' for m in mentions)}\n"
                    f"Available options: @user, {', '.join(f'@{agent[0]}' for agent in roster)}\n\n"
                    f"Your original response:\n{current_response}\n\n"
                    f"Please rewrite your response with exactly one appropriate @mention:"
                )

            # Get LLM to fix the response
            llm = get_llm(
                provider=self.llm_config.get("provider"),
                model=self.llm_config.get("model")
            )

            try:
                # Use simple format for correction
                from src.core.llm.base import LLMMessage
                messages = [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=error_msg)
                ]

                corrected_response = await llm.chat(messages)

                # Check corrected response
                corrected_mentions = MENTION_PATTERN.findall(corrected_response)

                if len(corrected_mentions) == 1:
                    print(f"✅ Validation wall: Response corrected after {attempt} attempts")
                    return corrected_response
                else:
                    print(f"❌ Validation wall: Attempt {attempt} still invalid ({len(corrected_mentions)} mentions)")
                    current_response = corrected_response
                    mentions = corrected_mentions

            except Exception as e:
                print(f"❌ Validation wall: Error during correction attempt {attempt}: {e}")
                continue

        # If all attempts failed, force add @user mention
        print(f"⚠️ Validation wall: Max attempts reached, forcing @user mention")
        if not response.strip().endswith("@user"):
            return f"{response.rstrip()} @user"
        return response