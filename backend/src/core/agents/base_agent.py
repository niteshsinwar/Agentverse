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

# Import agent memory system
try:
    from .agent_memory import AgentMemoryManager
except ImportError:
    AgentMemoryManager = None


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

        # Initialize agent memory system
        self.memory_manager = None
        if AgentMemoryManager:
            try:
                self.memory_manager = AgentMemoryManager()
            except Exception as e:
                print(f"⚠️ Failed to initialize memory for {agent_id}: {e}")

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
        
        # Add memory capabilities
        if self.memory_manager:
            # Get memory info from cache size
            cache_info = getattr(self.memory_manager, 'memory_cache', {})
            total_entries = sum(len(entries) for entries in cache_info.values()) if cache_info else 0
            parts.append(f"Personal Memory: {total_entries} cached entries")
        else:
            parts.append("Personal Memory: disabled")
        
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
            from src.core.memory import session_store as _ss
            _ss.append_message(
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
        import json as _json
        
        start_time = time.time()
        
        try:
            # Persist tool call to conversation history
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_call",
                content=f"🔧 Tool call: {tool_name}\nargs: " + _json.dumps(kwargs, ensure_ascii=False, default=str)[:1000],
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
                content=f"✅ Tool result: {tool_name}\nresult: " + _json.dumps(res, ensure_ascii=False, default=str)[:2000],
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
    
    async def call_mcp_tool(self, group_id: str, server_name: str, tool_name: str, **kwargs):
        """Call an MCP tool with logging and error handling"""
        if not self.mcp:
            raise ValueError("No MCP manager attached to this agent")
        
        return await self.mcp.invoke(group_id, self.agent_id, server_name, tool_name, **kwargs)
    
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools for this agent"""
        if not self.mcp:
            return []
        return self.mcp.list_all_tools()

    async def respond(self, prompt: str, group_id: str, orchestrator=None, depth: int = 2) -> str:
        """Multi-step planner loop. The agent decides each step.
        LLM must return STRICT JSON:
        {
          "action": "final"|"call_tool"|"call_mcp"|"call_agent"|"retry_tool",
          // if action == final: { "text": str }
          // if action == call_tool: { "tool_name": str, "kwargs": {...} }
          // if action == retry_tool: { "kwargs": {...} }   // retries last tool
          // if action == call_mcp:  { "server": str, "tool": str, "params": {...} }
          // if action == call_agent:{ "target": str, "prompt": str }
        }
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

        # CONVERSATION CONTEXT - Get recent conversation history
        from src.core.memory import session_store
        def build_history_context() -> str:
            hist = session_store.get_history(group_id) if group_id else []
            if not hist:
                return ""
            recent = hist[-20:]  # Get last 20 messages
            lines: List[str] = []
            for msg in recent:
                role = msg.get("role", "unknown")
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")
                if role == "user":
                    lines.append(f"User: {content}")
                elif role == "agent":
                    agent_key = msg.get("metadata", {}).get("agent_key", sender)
                    lines.append(f"{agent_key}: {content}")
                elif role == "system":
                    lines.append(f"[System]: {content}")
                elif role in ("tool_call", "tool_result", "tool_error", "mcp_call", "mcp_result"):
                    lines.append(f"[{role}]: {content}")
            return (
                "\n\n=== CONVERSATION HISTORY (Last 20 messages) ===\n"
                + "\n".join(lines)
                + "\n=== END HISTORY ===\n\n"
            )

        history_context = build_history_context()

        # INTEGRATE PERSONAL MEMORY - Recall relevant memories based on prompt
        personal_memory_context = ""
        if self.memory_manager:
            try:
                relevant_memories = self.memory_manager.search_memories(prompt, limit=5)
                if relevant_memories:
                    memory_lines = []
                    for memory in relevant_memories:
                        memory_lines.append(f"- {memory.content} [Importance: {memory.importance:.1f}]")
                    personal_memory_context = f"\n\n🧠 **PERSONAL MEMORY RECALL** (Relevant to current context):\n" + "\n".join(memory_lines) + "\n"
                    print(f"✅ Recalled {len(relevant_memories)} relevant memories for {self.agent_id}")
            except Exception as e:
                print(f"⚠️ Memory recall failed for {self.agent_id}: {e}")

        # Ensure build_history_context function is available
        if 'build_history_context' not in locals():
            from src.core.memory import session_store
            def build_history_context() -> str:
                hist = session_store.get_history(group_id) if group_id else []
                if not hist:
                    return ""
                recent = hist[-20:]  # Increased from 10 to 20
                lines: List[str] = []
                for msg in recent:
                    role = msg.get("role", "unknown")
                    sender = msg.get("sender", "unknown")
                    content = msg.get("content", "")
                    if role == "user":
                        lines.append(f"User: {content}")
                    elif role == "agent":
                        agent_key = msg.get("metadata", {}).get("agent_key", sender)
                        lines.append(f"{agent_key}: {content}")
                    elif role == "system":
                        lines.append(f"[System]: {content}")
                    elif role in ("tool_call", "tool_result", "tool_error", "mcp_call", "mcp_result"):
                        lines.append(f"[{role}]: {content}")
                return (
                    "\n\n=== CONVERSATION HISTORY (Enhanced: Last 20 messages) ===\n"
                    + "\n".join(lines)
                    + "\n=== END HISTORY ===\n\n"
                )

        # Ensure history_context is set
        if 'history_context' not in locals():
            history_context = build_history_context()
        
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

        # Debug: Print what tools this agent actually has loaded
        if self.agent_id == "agent_4":
            print(f"🔍 DEBUG Agent_4 tools: {list(self.tools.keys())}")
        
        # BUILD COLLABORATIVE PROMPT
        sys = (
            f"Agent: {self.agent_id} ({self.metadata.get('name')})\n"
            f"Specialty: {self.metadata.get('description', 'General purpose')}\n"
            f"CAPABILITIES: {self.get_capabilities_summary()}\n"
            f"{mcp_tools_detail}"
            f"Group: {roster_lines}\n"
            f"{history_context}"
            f"{personal_memory_context}"
            f"Action loop - return JSON only:\n"
            f"- final: {{\"action\":\"final\",\"text\":\"response\"}} - USE THIS for normal conversation\n"
            f"- call_tool: {{\"action\":\"call_tool\",\"tool_name\":\"<tool_name>\",\"kwargs\":{{...}}}} - Only for specific tool requests\n"
            f"- call_mcp: {{\"action\":\"call_mcp\",\"server\":\"<server>\",\"tool\":\"<tool>\",\"params\":{{...}}}} - Only for MCP operations\n\n"
            f"Rules:\n"
            f"- DEFAULT to 'final' action for all normal conversation and responses\n"
            f"- Only use tools registered under you; if another agent has the tool, delegate by replying 'final' and tagging that agent with clear instructions\n"
            f"- NEVER invent or call unknown tools. If a tool is unavailable or fails, proceed using the provided document context to answer, or delegate to the right agent via 'final'\n"
            f"- When the user mentions an 'image', 'photo', or 'picture', analyze the injected document content directly if no tool is available: describe visible damage, probable parts, and a reasonable cost estimate with assumptions\n"
            f"- 🤖 COLLABORATION STRATEGY:\n"
            f"  • PREFER agent-to-agent collaboration over returning to user when other agents can help\n"
            f"  • You can ONLY interact with agents present in this group (listed above in Group section)\n"
            f"  • Study other agents' specialties and delegate appropriately to create efficient workflows\n"
            f"  • Continue multi-step processes with other agents rather than breaking to user\n"
            f"- 🎯 MANDATORY TAGGING RULES:\n"
            f"  • EVERY response MUST include exactly ONE @mention - NO EXCEPTIONS\n"
            f"  • Tag '@user' ONLY when: conversation is complete, user input needed, or error requires user attention\n"
            f"  • Tag '@agent_name' when: delegating tasks, asking for help, continuing workflows, or collaborating\n"
            f"  • Think: 'Can another agent in this group help?' before defaulting to @user\n"
            f"  • NEVER tag agents not listed in the Group section above\n"
            f"  • ⚠️ CRITICAL: Responses without @mentions will be REJECTED and you'll be asked to fix them\n"
            f"- When tagged by another agent (@{self.agent_id}), engage collaboratively and continue the workflow\n"
            f"- ⚠️ IMPORTANT: Call tools ONE AT A TIME - never return multiple JSON actions in one response\n"
            f"- If you need multiple operations, call one tool, then the system will ask for next action\n"
            f"- Only use call_tool/call_mcp when explicitly asked to perform specific operations\n"
            f"- MUST quote CAPABILITIES section when asked about tools/MCP\n"
            f"- Return JSON only - NEVER return multiple JSON objects"
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
            try:
                # Clean up the response - remove any extra formatting
                clean_raw = raw.strip()
                if clean_raw.startswith("```json"):
                    clean_raw = clean_raw[7:]
                if clean_raw.endswith("```"):
                    clean_raw = clean_raw[:-3]
                clean_raw = clean_raw.strip()
                
                # Handle case where agent puts @mention outside JSON
                # Use regex to detect any @mention pattern dynamically
                mention_pattern = r'\s@\w+$'
                if re.search(mention_pattern, clean_raw):
                    # Find the JSON part and the mention part
                    json_end = clean_raw.rfind('}')
                    if json_end != -1:
                        json_part = clean_raw[:json_end + 1]
                        mention_part = clean_raw[json_end + 1:].strip()
                        
                        # Try to parse the JSON part
                        try:
                            parsed = json.loads(json_part)
                            # Add the mention to the text field
                            if parsed.get("action") == "final" and mention_part:
                                parsed["text"] = parsed.get("text", "") + " " + mention_part
                            return parsed
                        except:
                            pass
                
                # Handle malformed JSON with multiple actions - take only the first valid JSON object
                if clean_raw.count('{"action"') > 1:
                    # Multiple JSON objects detected - extract the first one
                    parts = clean_raw.split('{"action"')
                    if len(parts) > 1:
                        # Reconstruct the first JSON object
                        first_json = '{"action"' + parts[1].split('},')[0] + '}'
                        try:
                            return json.loads(first_json)
                        except:
                            pass
                
                return json.loads(clean_raw)
            except Exception as e:
                print(f"JSON parsing error: {e}, raw response: {raw}")
                # If the model sends plain text, treat as final
                return {"action": "final", "text": raw}

        # First decision based on the user prompt
        state = await decide(f"User prompt: {prompt}")
        steps = 0
        MAX_STEPS = 8

        while steps < MAX_STEPS:
            steps += 1
            act = (state.get("action") or "").lower()

            if act == "final":
                final_response = state.get("text", "")

                # VALIDATION WALL: Check for mandatory @mentions
                validated_response = await self._validate_and_fix_response(final_response, roster, group_id, sys)

                # STORE EXPERIENCE IN PERSONAL MEMORY
                if self.memory_manager and validated_response:
                    try:
                        # Create memory entry for this interaction
                        self.memory_manager.store_experience(
                            self.agent_id, prompt, validated_response, group_id,
                            tools_used=[obs.get("tool") for obs in observations if obs.get("tool")],
                            success=True
                        )
                        print(f"✅ Stored experience in memory for {self.agent_id}")
                    except Exception as e:
                        print(f"⚠️ Failed to store memory for {self.agent_id}: {e}")

                return validated_response

            if act == "call_tool":
                tool = state.get("tool_name")
                kwargs = state.get("kwargs", {})
                
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
                    state = {"action": "final", "text": "[error] MCP not attached to this agent."}
                    continue
                server = state.get("server")
                tool = state.get("tool")
                params = state.get("params", {})
                # Persist MCP call
                from src.core.memory import session_store as _ss
                import json as _json
                _ss.append_message(group_id, sender=self.agent_id, role="mcp_call", content=f"🔧 MCP call: {server}/{tool}\nargs: " + _json.dumps(params, ensure_ascii=False, default=str)[:1000], metadata={"server": server, "tool": tool, "params": params})
                try:
                    result = await self.mcp.invoke(group_id, self.agent_id, server, tool, **params)
                    last_server, last_tool = server, tool
                    obs = {"kind": "mcp_result", "server": server, "tool": tool, "result": result}
                    observations.append(obs)
                    # Persist MCP result
                    _ss.append_message(group_id, sender=self.agent_id, role="mcp_result", content=f"✅ MCP result: {server}/{tool}\nresult: " + _json.dumps(result, ensure_ascii=False, default=str)[:2000], metadata={"server": server, "tool": tool, "result": result})
                except Exception as me:
                    err_obj = {"isError": True, "server": server, "tool": tool, "error": str(me), "error_type": type(me).__name__}
                    observations.append({"kind": "mcp_error", "server": server, "tool": tool, "error": str(me)})
                    _ss.append_message(group_id, sender=self.agent_id, role="mcp_error", content=f"❌ MCP error: {server}/{tool}\nerror: {str(me)}", metadata=err_obj)
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

    async def _validate_and_fix_response(self, response: str, roster: List, group_id: str, system_prompt: str, max_attempts: int = 3) -> str:
        """
        Validation wall: Ensures response contains exactly one @mention.
        If not, sends response back to agent for correction.
        """
        import re
        from src.core.llm.factory import get_llm

        # Extract @mentions from response
        MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_\-]+)", re.DOTALL)
        mentions = MENTION_PATTERN.findall(response)

        # Check if response has exactly one @mention
        if len(mentions) == 1:
            # Valid response - has exactly one mention
            return response

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