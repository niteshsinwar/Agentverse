# =========================================
# File: app/agents/base_agent.py  
# Purpose: Agent decides: respond vs custom tool vs MCP vs other agent, with multi-step control loop
# =========================================
from __future__ import annotations
import json
import inspect
from typing import Any, Callable, Optional, Dict, List
from app.llm.factory import get_llm
from app.telemetry.events import emit_tool_call, emit_tool_result


def agent_tool(fn: Callable):
    setattr(fn, "__agent_tool__", True)
    return fn


class BaseAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.metadata: Dict[str, Any] = {}
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.mcp = None

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
        
        # Add MCP servers with debug info
        if self.mcp is None:
            parts.append("MCP servers: none (mcp is None)")
        elif not hasattr(self.mcp, 'servers'):
            parts.append(f"MCP servers: none (mcp has no servers attribute, type: {type(self.mcp)})")
        elif not self.mcp.servers:
            parts.append("MCP servers: none (empty servers dict)")
        else:
            server_names = list(self.mcp.servers.keys())
            parts.append(f"MCP servers: {', '.join(server_names)}")
        
        result = " | ".join(parts)
        return result

    def register_tools_from_module(self, mod: Any):
        for _, fn in inspect.getmembers(mod, inspect.isfunction):
            if getattr(fn, "__agent_tool__", False):
                self.tools[fn.__name__] = fn

    async def call_tool(self, group_id: str, tool_name: str, **kwargs):
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
            
        # Save tool call start as message
        from app.memory import session_store
        tool_start_msg = f"🔧 **Tool Call:** `{tool_name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})`"
        session_store.append_message(group_id, sender=self.agent_id, role="tool_call", content=tool_start_msg, 
                                   metadata={"tool_name": tool_name, "params": kwargs, "status": "start"})
        
        await emit_tool_call(group_id, self.agent_id, tool_name, status="start", meta={"params": kwargs})
        try:
            res = self.tools[tool_name](**kwargs)
            if inspect.isawaitable(res):
                res = await res
                
            # Save tool result as message
            result_preview = str(res)
            if len(result_preview) > 200:
                result_preview = result_preview[:200] + "..."
            tool_result_msg = f"📤 **Tool Result:** `{tool_name}` → {result_preview}"
            session_store.append_message(group_id, sender=self.agent_id, role="tool_result", content=tool_result_msg,
                                       metadata={"tool_name": tool_name, "result": str(res)})
            
            # Emit a short excerpt (first 300 chars) for transparency
            excerpt = str(res)
            if len(excerpt) > 300:
                excerpt = excerpt[:300] + "…"
            await emit_tool_result(group_id, self.agent_id, tool_name, excerpt)
            await emit_tool_call(group_id, self.agent_id, tool_name, status="end")
            return res
        except Exception as e:
            # Save tool error as message with better context
            error_text = str(e)
            
            # Add helpful hints for common parameter errors
            if "unexpected keyword argument" in error_text and tool_name in self.tools:
                try:
                    sig = inspect.signature(self.tools[tool_name])
                    param_names = list(sig.parameters.keys())
                    error_text += f" (Expected parameters: {', '.join(param_names)})"
                except:
                    pass
            
            error_msg = f"❌ **Tool Error:** `{tool_name}` → {error_text}"
            session_store.append_message(group_id, sender=self.agent_id, role="tool_error", content=error_msg,
                                       metadata={"tool_name": tool_name, "error": error_text})
            await emit_tool_call(group_id, self.agent_id, tool_name, status="error", meta={"error": error_text})
            
            # Return error information instead of raising - let agent decide what to do
            return {"error": True, "message": error_text, "tool": tool_name}

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
        llm = get_llm()
        roster = []
        if orchestrator:
            roster = orchestrator.group_roster(group_id)
        roster_lines = "\n".join([f"- @{k} — {n}: {d}" for (k, n, d) in roster]) or "- (no other members)"

        # Get conversation history for context
        from app.memory import session_store
        history = session_store.get_history(group_id) if group_id else []
        
        # Format recent conversation history (last 10 messages)
        history_context = ""
        if history:
            recent_history = history[-10:]  # Last 10 messages
            history_lines = []
            for msg in recent_history:
                role = msg.get("role", "unknown")
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")
                if role == "user":
                    history_lines.append(f"User: {content}")
                elif role == "agent":
                    agent_key = msg.get("metadata", {}).get("agent_key", sender)
                    history_lines.append(f"{agent_key}: {content}")
                elif role == "system":
                    history_lines.append(f"[System]: {content}")
            if history_lines:
                history_context = f"\n\n=== CONVERSATION HISTORY (You can see and reference these messages) ===\n" + "\n".join(history_lines) + "\n=== END HISTORY ===\n\n"

        sys = (
            f"Agent: {self.agent_id} ({self.metadata.get('name')})\n"
            f"Specialty: {self.metadata.get('description', 'General purpose')}\n"
            f"CAPABILITIES: {self.get_capabilities_summary()}\n"
            f"Group: {roster_lines}\n"
            f"{history_context}"
            f"Action loop - return JSON only:\n"
            f"- final: {{\"action\":\"final\",\"text\":\"response\"}} - USE THIS for normal conversation\n"
            f"- call_tool: {{\"action\":\"call_tool\",\"tool_name\":\"<tool_name>\",\"kwargs\":{{...}}}} - Only for specific tool requests\n"
            f"- call_mcp: {{\"action\":\"call_mcp\",\"server\":\"<server>\",\"tool\":\"<tool>\",\"params\":{{...}}}} - Only for MCP operations\n\n"
            f"Rules:\n"
            f"- DEFAULT to 'final' action for all normal conversation and responses\n"
            f"- 🚨 CRITICAL: You MUST ALWAYS end EVERY response by tagging exactly ONE target (@agent_name OR @user)\n"
            f"- ❌ NEVER submit a response without a tag - this breaks the conversation flow\n"
            f"- NEVER tag multiple agents or both agent and user in same response\n"
            f"- If responding to user, tag '@user' to transfer control back to user\n"
            f"- If continuing conversation with agents, tag '@agent_name' to transfer control to that agent\n"
            f"- When tagged by another agent (@{self.agent_id}), respond and tag exactly ONE target to continue\n"
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
                if clean_raw.endswith((' @user', ' @agent_1', ' @agent_2', ' @agent_3')):
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
                return state.get("text", "")

            if act == "call_tool":
                tool = state.get("tool_name")
                kwargs = state.get("kwargs", {})
                
                result = await self.call_tool(group_id, tool, **kwargs)
                last_tool = tool
                
                # Feed the observation back to the model
                obs = {"kind": "tool_result", "tool": tool, "result": result}
                observations.append(obs)
                
                # Build context with ALL previous observations AND chat history so agent remembers everything
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
                result = await self.mcp.invoke(group_id, self.agent_id, server, tool, **params)
                last_server, last_tool = server, tool
                obs = {"kind": "mcp_result", "server": server, "tool": tool, "result": result}
                observations.append(obs)
                
                # Build context with ALL previous observations AND chat history so agent remembers everything
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