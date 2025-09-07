
# =========================================
# File: app/agent/orchestrator.py
# Purpose: Build/hold agents; enforce group membership on agent->agent calls
# =========================================
from __future__ import annotations
from typing import Dict, Any, List, Tuple
from app.agents.registry import discover_agents, build_agent
from app.memory import session_store
from app.telemetry.events import emit_agent_call


class AgentOrchestrator:
    def __init__(self) -> None:
        self.specs = discover_agents()  # key -> AgentSpec
        self._agents: Dict[str, Any] = {}

    def list_available_agents(self) -> Dict[str, Any]:
        return self.specs

    def get_agent(self, key: str):
        if key not in self.specs:
            raise ValueError(f"Unknown agent '{key}'")
        if key not in self._agents:
            self._agents[key] = build_agent(self.specs[key])
        return self._agents[key]

    def group_roster(self, group_id: str) -> List[Tuple[str, str, str]]:
        """Return list of (key, name, description) for members of a group."""
        members = session_store.list_group_agents(group_id)
        out: List[Tuple[str, str, str]] = []
        for key in members:
            spec = self.specs.get(key)
            if spec:
                out.append((key, spec.name, spec.description))
        return out

    async def agent_call(self, group_id: str, caller_key: str, target_key: str, prompt: str, depth: int = 2) -> str:
        # Enforce: target must be part of the same group
        members = set(session_store.list_group_agents(group_id))
        if target_key not in members:
            await emit_agent_call(group_id, caller_key, target_key, status="blocked", meta={"reason": "callee_not_in_group"})
            return f"[blocked] @{target_key} is not a member of this group."

        if depth <= 0:
            await emit_agent_call(group_id, caller_key, target_key, status="blocked", meta={"reason": "max_depth"})
            return "[blocked] Max agent-call depth reached."

        await emit_agent_call(group_id, caller_key, target_key, status="start", meta={"prompt": prompt})
        callee = self.get_agent(target_key)
        try:
            reply = await callee.respond(prompt, group_id=group_id, orchestrator=self, depth=depth - 1)
            await emit_agent_call(group_id, caller_key, target_key, status="end")
            return reply
        except Exception as e:
            await emit_agent_call(group_id, caller_key, target_key, status="error", meta={"error": str(e)})
            return f"[error] Agent call failed: {e}"
        except Exception as e:
            await emit_agent_call(group_id, caller_key, target_key, status="error", meta={"error": str(e)})
            return f"[error] Agent call failed: {e}"