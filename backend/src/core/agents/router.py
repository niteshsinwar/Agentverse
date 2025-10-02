# =========================================
# File: app/agents/router.py
# Purpose: Unified router treating all participants (users and agents) equally
# =========================================
from __future__ import annotations
import asyncio
import re
from typing import Any, Optional, Tuple

from src.core.memory import session_store
from src.core.telemetry.events import emit_error, emit_message

MENTION = re.compile(r"@([A-Za-z0-9_\-]+)", re.DOTALL)


class Router:
    def __init__(self, orchestrator_service: Any):
        self.orchestrator_service = orchestrator_service

    def parse(self, text: str) -> Optional[Tuple[str, str]]:
        # Look for @mentions anywhere in the text
        text = text.strip()
        matches = MENTION.findall(text)
        
        if not matches:
            return None
        
        # Get unique agent names mentioned
        unique_agents = list(dict.fromkeys(matches))  # Preserves order, removes duplicates
        
        # Enforce only one unique agent per message (same agent can be mentioned multiple times)
        if len(unique_agents) > 1:
            # Multiple different agents found - this violates the one-target rule
            return None
        
        agent_key = unique_agents[0]
        
        # For content, use the entire text but remove ALL @mentions of this agent
        content = re.sub(r"@" + re.escape(agent_key) + r"\b", "", text).strip()
        
        # If no content remains after removing @mentions, use the original text
        if not content:
            content = text
            
        return agent_key, content

    async def route_message(self, group_id: str, message: str, mentioner: str = "user") -> str:
        """
        Unified message routing for all participants (users and agents).

        Args:
            group_id: The group to route message in
            message: The message content
            mentioner: Who sent this message ("user" or agent_key)

        Returns:
            Error message if routing failed, empty string if successful
        """
        members = session_store.list_group_agents(group_id)

        # 1. Handle single-agent groups (auto-route to the only agent)
        if len(members) == 1 and mentioner == "user":
            agent_key = members[0]

            # Store user message immediately
            session_store.append_message(group_id, sender="user", role="user", content=message)
            await emit_message(group_id, sender="user", role="user", content=message)

            # Check if group chain is active before processing
            if not self.orchestrator_service.is_group_chain_active(group_id):
                print(f"🛑 Single-agent processing blocked for group {group_id}")
                return ""

            # Process agent response asynchronously
            asyncio.create_task(self._process_agent_response(group_id, agent_key, message, mentioner))
            return ""

        # 2. Parse @mentions for multi-agent groups or agent-to-agent communication
        parsed = self.parse(message)
        if not parsed:
            if mentioner == "user":
                # User in multi-agent group must use @mentions
                matches = MENTION.findall(message.strip())
                if len(matches) > 1:
                    return f"Please tag only ONE agent at a time. Found multiple @mentions: {', '.join('@' + m for m in matches)}"
                else:
                    return "Please start your message with @AgentKey (e.g., @agent_1 How many records?)."
            else:
                # Agent message without @mention - just store it, no further routing
                session_store.append_message(group_id, sender=mentioner, role="agent", content=message, metadata={"agent_key": mentioner})
                await emit_message(group_id, sender=mentioner, role="agent", content=message, agent_key=mentioner)
                return ""

        # 3. Route to mentioned agent
        target_agent, content = parsed
        members_set = set(session_store.list_group_agents(group_id))

        if target_agent not in members_set:
            return f"Unknown or non-member agent '@{target_agent}' for this group."

        # Store the original message (preserves @mention in UI)
        # Skip storage if this is a U-turn routing (message already stored)
        if mentioner != "user":
            # This is agent-to-agent routing (U-turn), message already stored in _process_agent_response
            pass
        else:
            # This is user message, store it
            role = "user"
            metadata = {}
            session_store.append_message(group_id, sender=mentioner, role=role, content=message, metadata=metadata)
            await emit_message(group_id, sender=mentioner, role=role, content=message, agent_key=None)

        # Process target agent response asynchronously (U-turn flow)
        asyncio.create_task(self._process_agent_response(group_id, target_agent, content, mentioner))

        return ""

    async def handle_user_message(self, group_id: str, text: str, sender: str = "user") -> str:
        """Legacy method - delegates to unified route_message"""
        return await self.route_message(group_id, text, sender)

    async def _process_agent_response(self, group_id: str, agent_key: str, content: str, mentioned_by: str = "user") -> None:
        """
        Process agent response asynchronously - enables immediate UI display.
        This method runs in the background while the user sees their message immediately.
        """
        try:
            # Check if group chain is stopped
            if not self.orchestrator_service.is_group_chain_active(group_id):
                print(f"🛑 Agent {agent_key} processing stopped for group {group_id}")
                return
            # Add context about who mentioned this agent
            enhanced_content = content
            if mentioned_by != "user":
                enhanced_content = f"[Context: You were mentioned by {mentioned_by}]\n\n{content}"

            # Get agent response with document context
            reply = await self.orchestrator_service.orchestrator.process_user_message(group_id, agent_key, enhanced_content)

            # Save agent response only if it's not empty
            if str(reply).strip():
                session_store.append_message(group_id, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key, "mentioned_by": mentioned_by})
                await emit_message(group_id, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)

                # Check if group chain is still active before U-turn routing
                if not self.orchestrator_service.is_group_chain_active(group_id):
                    print(f"🛑 U-turn routing blocked for group {group_id}")
                    return

                # U-turn routing: Agent response goes back through router for mention processing
                await self.route_message(group_id, str(reply), agent_key)

                # Check for user mentions to trigger sound notification
                await self._emit_user_notification(group_id, agent_key, str(reply))

        except Exception as e:
            print(f"❌ Error processing agent response: {e}")
            await emit_error(group_id, "router", f"Agent response failed: {str(e)}")

    # Legacy methods removed - now using unified route_message approach

    async def _emit_user_notification(self, group_id: str, agent_key: str, message: str) -> None:
        """
        Emit special notification event when user is mentioned - triggers sound notification.
        """
        if "@user" in message.lower():
            from src.core.telemetry.events import EVENT_BUS, TelemetryEvent, now_ts
            await EVENT_BUS.publish(TelemetryEvent(
                ts=now_ts(),
                group_id=group_id,
                kind="user_mention",
                agent_key=agent_key,
                payload={"message": message, "notification": "sound"}
            ))
