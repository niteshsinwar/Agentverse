
# =========================================
# File: app/agents/orchestrator.py
# Purpose: Build/hold agents; enforce group membership on agent->agent calls
# =========================================
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import asyncio

from src.core.agents.registry import build_agent, discover_agents
from src.core.document_processing.manager import document_manager
from src.core.memory import session_store
from src.core.telemetry.events import emit_agent_call
from src.core.config.settings import get_settings


class AgentOrchestrator:
    def __init__(self) -> None:
        """
        Initialize agent orchestrator.

        Loads agents from either:
        - Cloud cache (if cloud_enabled=True)
        - Local agent_store/ directory (if cloud_enabled=False)
        """
        self.settings = get_settings()
        self.specs = {}  # Will be loaded asynchronously
        self._agents: Dict[str, Any] = {}
        self._cloud_mode = self.settings.cloud_enabled

        # Load agents synchronously for backward compatibility
        if not self._cloud_mode:
            self.specs = discover_agents()  # Local agent_store
        else:
            # Cloud mode - agents will be loaded asynchronously
            print("☁️  Cloud mode: Agents will be loaded from cloud cache")

    async def _load_cloud_agents(self) -> None:
        """Load agents from cloud cache (async)"""
        try:
            from src.core.agents.cloud_agent_loader import discover_cloud_agents
            self.specs = await discover_cloud_agents()
            print(f"☁️  Loaded {len(self.specs)} agents from cloud cache")
        except Exception as e:
            print(f"⚠️  Failed to load agents from cloud cache: {e}")
            self.specs = {}

    def refresh_agents(self) -> None:
        """
        Refresh agent discovery after new agents are created.

        For local mode: Re-scans agent_store/ directory
        For cloud mode: Re-loads from cloud cache
        """
        if not self._cloud_mode:
            # Local mode
            self.specs = discover_agents()
            print(f"🔄 Refreshed agent discovery (local): {list(self.specs.keys())}")
        else:
            # Cloud mode - refresh asynchronously
            asyncio.create_task(self._refresh_cloud_agents())

        # Clear cached agents so they get rebuilt with new specs
        self._agents.clear()

    async def _refresh_cloud_agents(self) -> None:
        """Refresh agents from cloud cache (async)"""
        print("🔄 Refreshing agents from cloud cache...")
        await self._load_cloud_agents()
        print(f"✅ Cloud agents refreshed: {list(self.specs.keys())}")

    def list_available_agents(self) -> Dict[str, Any]:
        return self.specs

    async def get_agent(self, key: str) -> Any:
        """
        Get agent instance.

        For local mode: Builds from agent_store/ directory
        For cloud mode: Builds from cloud cache
        """
        if key not in self.specs:
            raise ValueError(f"Unknown agent '{key}'")

        if key not in self._agents:
            if not self._cloud_mode:
                # Local mode
                self._agents[key] = await build_agent(self.specs[key])
            else:
                # Cloud mode
                from src.core.agents.cloud_agent_loader import build_cloud_agent
                self._agents[key] = await build_cloud_agent(self.specs[key])

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
        callee = await self.get_agent(target_key)
        
        # Add document context for the target agent
        enhanced_prompt = prompt  # Document context now handled via conversation history
        
        try:
            reply = await callee.respond(enhanced_prompt, group_id=group_id, orchestrator=self, depth=depth - 1)
            await emit_agent_call(group_id, caller_key, target_key, status="end")
            return reply
        except Exception as e:
            await emit_agent_call(group_id, caller_key, target_key, status="error", meta={"error": str(e)})
            return f"[error] Agent call failed: {e}"


    async def process_user_message(self, group_id: str, agent_id: str, message: str, rag_context: str = "") -> str:
        """
        Process user message with RAG context

        Args:
            group_id: Group ID
            agent_id: Target agent ID
            message: User message
            rag_context: Retrieved RAG context (from rag_service)

        Returns:
            Response payload
        """
        agent = await self.get_agent(agent_id)

        try:
            # Pass RAG context to agent
            response_payload = await agent.respond(
                message,
                group_id=group_id,
                orchestrator=self,
                rag_context=rag_context  # RAG context passed here
            )
            if isinstance(response_payload, dict):
                response_payload.setdefault("text", "")
            else:
                response_payload = {"text": str(response_payload)}
            return response_payload
        except Exception as e:
            error_msg = f"[error] Agent response failed: {e}"
            print(f"❌ Agent {agent_id} error: {e}")
            print(f"📍 Error type: {type(e).__name__}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return {
                "text": error_msg
            }
