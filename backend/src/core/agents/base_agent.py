# =========================================
# File: src/core/agents/base_agent.py
# Purpose: Enhanced agent with LangChain LLM and self-reflection planning loop
# =========================================
from __future__ import annotations
import inspect
import json
from typing import Any, Callable, Dict, List, Optional

from src.core.llm.factory import get_llm
from src.core.telemetry.events import (
    emit_agent_thought,
    emit_error,
    emit_mcp_call,
    emit_tool_call,
    emit_tool_result,
)
from src.core.telemetry.session_logger import session_logger

from .response_models import (
    FinalResponse,
    MCPCallResponse,
    SelfReflectResponse,
    ToolCallResponse,
    get_response_schema,
    parse_agent_response,
)

# Constants
MAX_CONVERSATION_HISTORY = 20
MAX_PLANNING_STEPS = 8
MAX_VALIDATION_ATTEMPTS = 3


def agent_tool(fn: Callable):
    """Decorator for custom tools - keeps tools simple and smooth"""
    setattr(fn, "__agent_tool__", True)
    return fn


class BaseAgent:
    """
    Enhanced agent with LangChain LLM integration.

    Business Logic (PRESERVED):
    - Agent only uses tools from its tools.py or mcp.json
    - Four actions: final, call_tool, call_mcp, self_reflect
    - @mention routing for agent-to-agent communication
    - Group-aware: knows roster, history, descriptions
    - Multi-tenant: same agent in multiple groups with separate history
    """

    def __init__(self, agent_id: str, llm_config: Optional[Dict[str, str]] = None):
        self.agent_id = agent_id
        self.metadata: Dict[str, Any] = {}
        self.tools: Dict[str, Callable[..., Any]] = {}
        self.mcp = None
        self.llm_config = llm_config or {"provider": "openai", "model": "gpt-4o-mini"}

    def load_metadata(self, name: str, description: str, folder_path: str) -> None:
        """Load agent metadata"""
        self.metadata = {"name": name, "description": description, "folder_path": folder_path}

    def attach_mcp(self, mcp_client: Any) -> None:
        """Attach MCP client for external tools"""
        self.mcp = mcp_client

    def get_capabilities_summary(self) -> str:
        """Return a summary of this agent's capabilities"""
        parts: List[str] = []

        specialty = self.metadata.get("description", "General purpose agent")
        parts.append(f"Specialty: {specialty}")

        # Custom tools
        if self.tools:
            tool_details: List[str] = []
            for name, func in self.tools.items():
                try:
                    sig = inspect.signature(func)
                    params: List[str] = []
                    for param_name, param in sig.parameters.items():
                        if param.annotation != inspect.Parameter.empty:
                            type_name = getattr(param.annotation, "__name__", str(param.annotation))
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

        # MCP servers
        if self.mcp is None:
            parts.append("MCP servers: none (mcp is None)")
        elif not hasattr(self.mcp, "servers"):
            parts.append(f"MCP servers: none (mcp has no servers attribute, type: {type(self.mcp)})")
        elif not self.mcp.servers:
            parts.append("MCP servers: none (empty servers dict)")
        else:
            mcp_summary: List[str] = []
            for server_name, server_handle in self.mcp.servers.items():
                tool_count = len(server_handle._tools_cache)
                if tool_count > 0:
                    tool_names = [tool.name for tool in server_handle._tools_cache[:3]]
                    if tool_count > 3:
                        tool_names.append(f"...+{tool_count-3} more")
                    mcp_summary.append(f"{server_name}({tool_count} tools: {', '.join(tool_names)})")
                else:
                    mcp_summary.append(f"{server_name}(0 tools)")
            parts.append(f"MCP servers: {' | '.join(mcp_summary)}")

        parts.append("Conversation Memory: enabled via session_store")

        return " | ".join(parts)

    def register_tools_from_module(self, mod: Any) -> None:
        """Register tools from module - only @agent_tool decorator"""
        for _, fn in inspect.getmembers(mod, inspect.isfunction):
            if getattr(fn, "__agent_tool__", False):
                self.tools[fn.__name__] = fn

    async def call_tool(self, group_id: str, tool_name: str, **kwargs: Any) -> Any:
        """Call a custom tool with logging and error handling"""
        if tool_name not in self.tools:
            from src.core.memory import session_store

            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_error",
                content=f"❌ Tool error: {tool_name}\nerror: Unknown tool",
                metadata={"tool": tool_name, "error": "Unknown tool", "error_type": "UnknownTool"},
            )
            return {"isError": True, "tool": tool_name, "error": "Unknown tool", "error_type": "UnknownTool"}

        from src.core.telemetry.session_logger import session_logger
        from src.core.telemetry.events import emit_tool_call, emit_tool_result, emit_error
        from src.core.memory import session_store
        import time

        start_time = time.time()

        try:
            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_call",
                content="🔧 Tool call: "
                + f"{tool_name}\nargs: "
                + json.dumps(kwargs, ensure_ascii=False, default=str)[:1000],
                metadata={"tool": tool_name, "params": kwargs},
            )
            res = self.tools[tool_name](**kwargs)
            if inspect.isawaitable(res):
                res = await res

            duration_ms = (time.time() - start_time) * 1000

            session_logger.log_tool_call(
                session_id=group_id,
                agent_id=self.agent_id,
                tool_name=tool_name,
                params=kwargs,
                duration_ms=duration_ms,
                result=res,
            )

            await emit_tool_call(
                group_id,
                self.agent_id,
                tool_name,
                "success",
                {"duration_ms": duration_ms, "params": kwargs},
            )
            await emit_tool_result(
                group_id,
                self.agent_id,
                tool_name,
                str(res)[:100],
                {"duration_ms": duration_ms},
            )

            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_result",
                content="✅ Tool result: "
                + f"{tool_name}\nresult: "
                + json.dumps(res, ensure_ascii=False, default=str)[:2000],
                metadata={"tool": tool_name, "result": res},
            )

            return res

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            session_logger.log_tool_call(
                session_id=group_id,
                agent_id=self.agent_id,
                tool_name=tool_name,
                params=kwargs,
                duration_ms=duration_ms,
                error=str(e),
            )

            await emit_error(
                group_id,
                f"tool_call:{tool_name}",
                str(e),
                {"agent_id": self.agent_id, "duration_ms": duration_ms},
            )

            session_store.append_message(
                group_id=group_id,
                sender=self.agent_id,
                role="tool_error",
                content=f"❌ Tool error: {tool_name}\nerror: {str(e)}",
                metadata={"tool": tool_name, "error": str(e), "error_type": type(e).__name__},
            )

            return {"isError": True, "tool": tool_name, "error": str(e), "error_type": type(e).__name__}

    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        if not self.mcp:
            return []
        return self.mcp.list_all_tools()

    async def respond(self, prompt: str, group_id: str, orchestrator: Any = None, depth: int = 2) -> Dict[str, Any]:
        """Entry-point for agent responses with structured metadata."""
        return await self._respond_inner(prompt, group_id, orchestrator, depth)

    async def _respond_inner(self, prompt: str, group_id: str, orchestrator: Any = None, depth: int = 2) -> Dict[str, Any]:
        """
        Multi-step planner loop with LangChain LLM.

        Supports four actions:
        - final: return a response to the user (must include @mention)
        - call_tool: invoke a local tool from tools.py
        - call_mcp: invoke an MCP tool
        - self_reflect: internal planning/thinking step
        """
        llm = get_llm(
            provider=self.llm_config.get("provider"),
            model=self.llm_config.get("model"),
        )

        roster = []
        if orchestrator:
            roster = orchestrator.group_roster(group_id)
        roster_lines = "\n".join([f"- @{k} — {n}: {d}" for (k, n, d) in roster]) or "- (no other members)"

        from src.core.memory import session_store

        def build_history_context() -> str:
            hist = session_store.get_history(group_id) if group_id else []
            if not hist:
                return ""
            recent = hist[-MAX_CONVERSATION_HISTORY:]
            lines: List[str] = []
            last_user_message = ""

            for msg in recent:
                role = msg.get("role", "unknown")
                sender = msg.get("sender", "unknown")
                content = msg.get("content", "")

                if role == "user":
                    lines.append(f"User: {content}")
                    last_user_message = content
                elif role == "agent":
                    agent_key = msg.get("metadata", {}).get("agent_key", sender)
                    lines.append(f"{agent_key}: {content}")
                elif role == "system":
                    lines.append(f"[System]: {content}")
                elif role == "agent_thought":
                    lines.append(f"[Thought]: {content}")
                elif role in ("tool_call", "tool_result", "tool_error", "mcp_call", "mcp_result", "mcp_error"):
                    lines.append(f"[{role}]: {content}")

            context_note = ""
            if last_user_message and f"@{self.agent_id}" in last_user_message:
                context_note = f"\n📍 IMPORTANT: You ({self.agent_id}) are being directly addressed by the user.\n"
            elif prompt and f"@{self.agent_id}" in prompt:
                import re

                mention_pattern = r"(\w+):\s*.*@" + re.escape(self.agent_id)
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

        # Build MCP tools listing
        mcp_tools_detail = ""
        if self.mcp and self.mcp.servers:
            mcp_tools_detail = "\n=== MCP TOOLS AVAILABLE TO YOU ===\n"
            for server_name, server_handle in self.mcp.servers.items():
                if server_handle._tools_cache:
                    mcp_tools_detail += f"Server: {server_name}\n"
                    for tool in server_handle._tools_cache:
                        desc = tool.description[:100] + "..." if len(tool.description) > 100 else tool.description

                        params = tool.parameters.get("properties", {})
                        required_params = tool.parameters.get("required", [])

                        param_info: List[str] = []
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
            mcp_tools_detail += '\nTo call MCP tools: {"action":"call_mcp","server":"<server>","tool":"<tool>","params":{...}}\n'
            mcp_tools_detail += "⚡ Parameters marked with * are REQUIRED - extract them from user's request.\n"
            mcp_tools_detail += "Example: 'navigate to google.com' → params: {\"url\": \"https://google.com\"}\n"
            mcp_tools_detail += "=== END MCP TOOLS ===\n"

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
            f"- 🧠 SELF-REFLECTION:\n"
            f"  • Reflect only when the task requires planning or multi-step coordination\n"
            f"  • A reflection without new insight is wasteful—move to 'final' instead\n"
            f"  • After reflecting, either act (tool/MCP) with the updated plan or produce the 'final' answer\n"
            f"  • Never loop on identical reflections; the system will terminate them\n"
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
        last_reflection_signature: Optional[str] = None
        must_finalize = False

        def format_observation(observation: Dict[str, Any]) -> str:
            kind = observation.get("kind")

            if kind == "tool_result":
                preview = str(observation.get("result"))[:120]
                return f"Tool '{observation.get('tool')}' → {preview}"
            if kind == "tool_error":
                return f"Tool '{observation.get('tool')}' errored: {observation.get('result')}"
            if kind == "mcp_result":
                preview = str(observation.get("result"))[:120]
                return f"MCP {observation.get('server')}/{observation.get('tool')} → {preview}"
            if kind == "mcp_error":
                error_msg = observation.get("error") or observation.get("result")
                return f"MCP {observation.get('server')}/{observation.get('tool')} errored: {error_msg}"
            if kind == "agent_thought":
                pieces = [observation.get("thought") or ""]
                if observation.get("plan"):
                    pieces.append(f"Plan: {observation['plan']}")
                if observation.get("evaluation"):
                    pieces.append(f"Evaluation: {observation['evaluation']}")
                if observation.get("metric"):
                    pieces.append(f"Metric: {observation['metric']}")
                status = observation.get("should_continue")
                if status is False:
                    pieces.append("Status: planning complete")
                elif status is True:
                    pieces.append("Status: continuing planning")
                return " | ".join([p for p in pieces if p])
            return str(observation)

        def summarize_observations(latest_obs: Dict[str, Any], enforce_final: bool = False) -> str:
            history_ctx = build_history_context()
            summary = f"Original user request: {prompt}\n\n"
            if history_ctx.strip():
                summary += history_ctx + "\n"

            summary += "Previous actions taken:\n"
            if observations:
                for i, obs in enumerate(observations, 1):
                    summary += f"{i}. {format_observation(obs)}\n"
            else:
                summary += "• None so far\n"

            summary += f"\nLatest result: {json.dumps(latest_obs, ensure_ascii=False)}\n\n"
            guidance = (
                "Evaluate progress toward the goal. Decide whether to call a tool, call an MCP tool, "
                "take a brief self_reflect planning step, or produce the final answer. Only use tools when necessary."
            )
            if enforce_final:
                guidance += " STOP PLANNING NOW: respond with {\"action\":\"final\", ...}. Do NOT output self_reflect again."
            else:
                guidance += " Reserve self_reflect for focused planning adjustments when new insights appear."
            summary += guidance
            return summary

        async def decide(user_or_obs: str) -> Dict[str, Any]:
            """Make decision using LangChain LLM"""
            raw = await llm.simple_chat(system=sys, user=user_or_obs)

            try:
                parsed_response = parse_agent_response(raw)

                if isinstance(parsed_response, FinalResponse):
                    return {
                        "action": "final",
                        "text": parsed_response.text,
                        "raw_model": parsed_response,
                    }
                if isinstance(parsed_response, ToolCallResponse):
                    return {
                        "action": "call_tool",
                        "tool_name": parsed_response.tool,
                        "kwargs": parsed_response.inputs,
                    }
                if isinstance(parsed_response, MCPCallResponse):
                    return {
                        "action": "call_mcp",
                        "server": parsed_response.server,
                        "tool": parsed_response.tool,
                        "params": parsed_response.inputs,
                    }
                if isinstance(parsed_response, SelfReflectResponse):
                    return {
                        "action": "self_reflect",
                        "thought": parsed_response.thought,
                        "plan": parsed_response.plan,
                        "evaluation": parsed_response.evaluation,
                        "metric": parsed_response.metric,
                        "should_continue": parsed_response.should_continue,
                        "raw_model": parsed_response,
                    }
                return {"action": "final", "text": str(parsed_response)}

            except Exception as e:
                print(f"⚠️ Structured parsing failed for {self.agent_id}: {e}")
                print(f"Raw response: {repr(raw)}")
                return {"action": "final", "text": f"[Parsing error occurred] {raw} @user"}

        state = await decide(f"User prompt: {prompt}")

        steps = 0

        while steps < MAX_PLANNING_STEPS:
            steps += 1
            act = (state.get("action") or "").lower()

            if must_finalize and act != "final":
                forced_state = await decide(
                    "STOP. Planning is complete. Respond with valid JSON where \"action\" is \"final\" and you answer the user. "
                    "Do NOT return self_reflect, call_tool, or call_mcp."
                )
                state = forced_state
                act = (state.get("action") or "").lower()

                if act != "final":
                    latest_reflection = next(
                        (obs for obs in reversed(observations) if obs.get("kind") == "agent_thought"),
                        None,
                    )
                    fallback_text = ""
                    if latest_reflection:
                        fallback_text = latest_reflection.get("plan") or latest_reflection.get("thought") or ""
                    fallback_text = fallback_text.strip() or "Continuing with the requested answer."
                    if "@user" not in fallback_text:
                        fallback_text = f"{fallback_text} @user"

                    state = {
                        "action": "final",
                        "text": fallback_text,
                        "raw_model": None,
                    }
                    act = "final"

            if act == "final":
                final_response = state.get("text", "")
                model_payload: FinalResponse | None = state.get("raw_model")

                validated_response = await self._validate_and_fix_response(final_response, roster, group_id, sys)

                return {
                    "text": validated_response,
                }

            if act == "call_tool":
                tool = state.get("tool_name")
                kwargs = state.get("kwargs", {})

                if tool not in self.tools:
                    obs = {
                        "kind": "tool_error",
                        "tool": tool,
                        "result": f"Tool '{tool}' not found. Available tools: {list(self.tools.keys())}",
                    }
                    observations.append(obs)
                    state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                    continue

                result = await self.call_tool(group_id, tool, **kwargs)
                obs = {"kind": "tool_result", "tool": tool, "result": result}
                observations.append(obs)

                state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                continue

            if act == "call_mcp":
                if not self.mcp:
                    obs = {"kind": "mcp_error", "server": "unknown", "tool": "unknown", "result": "MCP not attached to this agent"}
                    observations.append(obs)
                    state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                    continue

                server = state.get("server")
                tool = state.get("tool")
                params = state.get("params", {})

                if not server or not tool:
                    obs = {"kind": "mcp_error", "server": server, "tool": tool, "result": "Missing server or tool name"}
                    observations.append(obs)
                    state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                    continue

                from src.core.telemetry.events import emit_mcp_call, emit_error
                import time

                start_time = time.time()
                session_store.append_message(
                    group_id,
                    sender=self.agent_id,
                    role="mcp_call",
                    content="🔧 MCP call: "
                    + f"{server}/{tool}\nargs: "
                    + json.dumps(params, ensure_ascii=False, default=str)[:1000],
                    metadata={"server": server, "tool": tool, "params": params},
                )

                await emit_mcp_call(group_id, self.agent_id, server, tool, "calling", {"params": params})

                try:
                    result = await self.mcp.invoke(group_id, self.agent_id, server, tool, **params)
                    duration_ms = (time.time() - start_time) * 1000

                    obs = {"kind": "mcp_result", "server": server, "tool": tool, "result": result}
                    observations.append(obs)

                    session_store.append_message(
                        group_id,
                        sender=self.agent_id,
                        role="mcp_result",
                        content="✅ MCP result: "
                        + f"{server}/{tool}\nresult: "
                        + json.dumps(result, ensure_ascii=False, default=str)[:2000],
                        metadata={"server": server, "tool": tool, "result": result},
                    )

                    await emit_mcp_call(
                        group_id,
                        self.agent_id,
                        server,
                        tool,
                        "success",
                        {"duration_ms": duration_ms, "result_preview": str(result)[:200]},
                    )

                except Exception as me:
                    duration_ms = (time.time() - start_time) * 1000
                    err_obj = {
                        "isError": True,
                        "server": server,
                        "tool": tool,
                        "error": str(me),
                        "error_type": type(me).__name__,
                    }
                    observations.append({"kind": "mcp_error", "server": server, "tool": tool, "error": str(me)})
                    session_store.append_message(
                        group_id,
                        sender=self.agent_id,
                        role="mcp_error",
                        content=f"❌ MCP error: {server}/{tool}\nerror: {str(me)}",
                        metadata=err_obj,
                    )

                    await emit_error(
                        group_id,
                        f"mcp_call:{server}/{tool}",
                        str(me),
                        {"agent_id": self.agent_id, "duration_ms": duration_ms},
                    )

                state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                continue

            if act == "self_reflect":
                reflect_model: SelfReflectResponse | None = state.get("raw_model")
                thought_text = (reflect_model.thought if reflect_model else None) or state.get("thought") or ""
                plan_text = (reflect_model.plan if reflect_model else None) or state.get("plan")
                evaluation_text = (reflect_model.evaluation if reflect_model else None) or state.get("evaluation")
                metric_text = (reflect_model.metric if reflect_model else None) or state.get("metric")
                raw_should_continue = None
                if reflect_model and reflect_model.should_continue is not None:
                    raw_should_continue = reflect_model.should_continue
                elif "should_continue" in state:
                    raw_should_continue = state.get("should_continue")
                should_continue = bool(raw_should_continue) if raw_should_continue is not None else False

                signature_payload = {
                    "thought": thought_text,
                    "plan": plan_text or "",
                    "evaluation": evaluation_text or "",
                    "metric": metric_text or "",
                }
                signature = json.dumps(signature_payload, sort_keys=True)
                is_duplicate_reflection = signature == last_reflection_signature
                last_reflection_signature = signature

                if not should_continue:
                    must_finalize = True

                summary_lines = [f"🧠 Reflection (step {steps}): {thought_text}"]
                if plan_text:
                    summary_lines.append(f"Next: {plan_text}")
                if evaluation_text:
                    summary_lines.append(f"Assessment: {evaluation_text}")
                if metric_text:
                    summary_lines.append(f"Metric: {metric_text}")
                summary_lines.append(
                    "Planning complete — preparing final response."
                    if not should_continue
                    else "Continuing planning briefly…"
                )
                formatted_content = "\n".join(summary_lines)
                metadata = {
                    "message_type": "agent_thought",
                    "plan": plan_text,
                    "evaluation": evaluation_text,
                    "metric": metric_text,
                    "should_continue": should_continue,
                    "step": steps,
                    "duplicate": is_duplicate_reflection,
                }

                if not is_duplicate_reflection:
                    session_store.append_message(
                        group_id=group_id,
                        sender=self.agent_id,
                        role="agent_thought",
                        content=formatted_content,
                        metadata=metadata,
                    )
                    await emit_agent_thought(
                        group_id=group_id,
                        agent_key=self.agent_id,
                        thought=thought_text,
                        meta={
                            "plan": plan_text,
                            "evaluation": evaluation_text,
                            "metric": metric_text,
                            "step": steps,
                            "should_continue": should_continue,
                        },
                    )

                obs = {
                    "kind": "agent_thought",
                    "thought": thought_text,
                    "plan": plan_text,
                    "evaluation": evaluation_text,
                    "metric": metric_text,
                    "should_continue": should_continue,
                }
                observations.append(obs)

                state = await decide(summarize_observations(obs, enforce_final=must_finalize))
                continue

            return {
                "text": "[error] Unknown action",
                "metadata": {"reason": "unknown_action"},
            }

        return {
            "text": "[error] Stopped after max planning steps]",
            "metadata": {"reason": "max_steps"},
        }

    async def _validate_and_fix_response(
        self,
        response: str,
        roster: List[Any],
        group_id: str,
        system_prompt: str,
        max_attempts: int = MAX_VALIDATION_ATTEMPTS,
    ) -> str:
        """Validation wall: Ensures response contains exactly one @mention"""
        import re

        from src.core.llm.factory import get_llm as get_llm_for_validation

        MENTION_PATTERN = re.compile(r"@([A-Za-z0-9_\-]+)", re.DOTALL)
        mentions = MENTION_PATTERN.findall(response)

        available_agents = [agent[0] for agent in roster if agent[0] != self.agent_id] + ["user"]

        if len(mentions) == 1:
            mentioned_agent = mentions[0]
            if mentioned_agent in available_agents:
                return response
            mentions = []

        attempt = 0
        current_response = response

        llm = get_llm_for_validation(
            provider=self.llm_config.get("provider"),
            model=self.llm_config.get("model"),
        )

        while attempt < max_attempts:
            attempt += 1
            print(f"🔄 Validation wall: Response from {self.agent_id} attempt {attempt} - fixing missing/multiple @mentions")

            if len(mentions) == 0:
                error_msg = (
                    "⚠️ VALIDATION ERROR: Your response is missing a required @mention.\n"
                    "MANDATORY: Every response must include exactly ONE @mention.\n"
                    f"Available options: @user, {', '.join(f'@{agent[0]}' for agent in roster)}\n\n"
                    f"Your original response:\n{current_response}\n\n"
                    "Please rewrite your response including exactly one appropriate @mention:"
                )
            else:
                error_msg = (
                    f"⚠️ VALIDATION ERROR: Your response has {len(mentions)} @mentions but exactly ONE is required.\n"
                    f"Found mentions: {', '.join(f'@{m}' for m in mentions)}\n"
                    f"Available options: @user, {', '.join(f'@{agent[0]}' for agent in roster)}\n\n"
                    f"Your original response:\n{current_response}\n\n"
                    "Please rewrite your response with exactly one appropriate @mention:"
                )

            try:
                corrected_response = await llm.simple_chat(system=system_prompt, user=error_msg)
                corrected_mentions = MENTION_PATTERN.findall(corrected_response)

                if len(corrected_mentions) == 1 and corrected_mentions[0] in available_agents:
                    print(f"✅ Validation wall: Response corrected after {attempt} attempts")
                    return corrected_response

                print(f"❌ Validation wall: Attempt {attempt} still invalid ({len(corrected_mentions)} mentions)")
                current_response = corrected_response
                mentions = corrected_mentions

            except Exception as e:
                print(f"❌ Validation wall: Error during correction attempt {attempt}: {e}")
                continue

        print("⚠️ Validation wall: Max attempts reached, forcing @user mention")
        if not response.strip().endswith("@user"):
            return f"{response.rstrip()} @user"
        return response
