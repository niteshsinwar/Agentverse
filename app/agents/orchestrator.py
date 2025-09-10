
# =========================================
# File: app/agents/orchestrator.py
# Purpose: Build/hold agents; enforce group membership on agent->agent calls
# =========================================
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from app.agents.registry import discover_agents, build_agent
from app.memory import session_store
from app.telemetry.events import emit_agent_call
from app.document_processing.manager import document_manager


class AgentOrchestrator:
    def __init__(self) -> None:
        self.specs = discover_agents()  # key -> AgentSpec
        self._agents: Dict[str, Any] = {}

    def refresh_agents(self) -> None:
        """Refresh agent discovery after new agents are created"""
        self.specs = discover_agents()
        # Clear cached agents so they get rebuilt with new specs
        self._agents.clear()
        print(f"🔄 Refreshed agent discovery: {list(self.specs.keys())}")

    def list_available_agents(self) -> Dict[str, Any]:
        return self.specs

    async def get_agent(self, key: str):
        if key not in self.specs:
            raise ValueError(f"Unknown agent '{key}'")
        if key not in self._agents:
            self._agents[key] = await build_agent(self.specs[key])
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
        enhanced_prompt = self._enhance_prompt_with_documents(prompt, target_key, group_id)
        
        try:
            reply = await callee.respond(enhanced_prompt, group_id=group_id, orchestrator=self, depth=depth - 1)
            await emit_agent_call(group_id, caller_key, target_key, status="end")
            return reply
        except Exception as e:
            await emit_agent_call(group_id, caller_key, target_key, status="error", meta={"error": str(e)})
            return f"[error] Agent call failed: {e}"

    def _enhance_prompt_with_documents(self, prompt: str, agent_id: str, group_id: str) -> str:
        """Add relevant document context to the prompt - always include if documents exist"""
        try:
            # Always check for recent documents for this agent
            recent_docs = document_manager.get_recent_documents(agent_id, group_id, limit=3)
            
            # Debug document context passing
            print(f"🔍 Document context debug for {agent_id}: Found {len(recent_docs) if recent_docs else 0} recent docs")
            
            if recent_docs:
                # Get full document context with content for LLM processing
                doc_context = document_manager.get_agent_document_context(agent_id, group_id)
                
                if doc_context and "No documents found" not in doc_context:
                    # Always include full document context when docs exist
                    enhanced_prompt = f"{prompt}\n\n{doc_context}"
                    print(f"✅ Document context added to {agent_id} prompt (length: {len(doc_context)})")
                    return enhanced_prompt
                    
        except Exception as e:
            # Don't fail the main call if document context fails
            print(f"❌ Warning: Document context failed for {agent_id}: {e}")
            
        print(f"⚪ No document context added to {agent_id}")
        return prompt

    async def process_user_message(self, group_id: str, agent_id: str, message: str, query_for_docs: Optional[str] = None) -> str:
        """Process user message with optional document context"""
        agent = await self.get_agent(agent_id)
        
        # Add document context if requested or if message mentions documents
        enhanced_message = self._enhance_prompt_with_documents(message, agent_id, group_id)
        
        # If specific document query, search for relevant docs
        if query_for_docs:
            try:
                doc_context = document_manager.get_agent_document_context(agent_id, group_id, query_for_docs)
                enhanced_message = f"{enhanced_message}\n\n--- Relevant Documents ---\n{doc_context}"
            except Exception as e:
                pass  # Don't fail if document search fails
        
        try:
            return await agent.respond(enhanced_message, group_id=group_id, orchestrator=self)
        except Exception as e:
            return f"[error] Agent response failed: {e}"