# =========================================
# File: app/agents/router.py
# Purpose: Route user messages that must @mention a group member
# =========================================
from __future__ import annotations
import asyncio
import re
from typing import Optional, Tuple
from src.core.memory import session_store
from src.core.telemetry.events import emit_message, emit_error

MENTION = re.compile(r"@([A-Za-z0-9_\-]+)", re.DOTALL)


class Router:
    def __init__(self, orchestrator):
        self.o = orchestrator

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

    async def handle_user_message(self, group_id: str, text: str, sender: str = "user") -> str:
        members = session_store.list_group_agents(group_id)

        # If this is an agent message, just process it for mentions and return
        if sender != "user":
            # Process mentions in agent message for automatic chaining
            await self._process_mentions_in_message(group_id, text, sender)
            return ""

        # Special case: if only one agent in group, auto-respond without @mention needed
        if len(members) == 1:
            agent_key = members[0]

            # Persist + emit user message
            session_store.append_message(group_id, sender="user", role="user", content=text)
            await emit_message(group_id, sender="user", role="user", content=text)

            # Get agent response with document context
            reply = await self.o.process_user_message(group_id, agent_key, text)

            # Save agent response only if it's not empty
            if str(reply).strip():
                session_store.append_message(group_id, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key})
                await emit_message(group_id, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)

                # Process mentions in agent response for automatic chaining
                await self._process_mentions_in_message(group_id, str(reply), agent_key)

            return str(reply)

        # For multiple agents, handle @mentions
        parsed = self.parse(text)
        if not parsed:
            # Check if there are multiple @mentions
            matches = MENTION.findall(text.strip())
            if len(matches) > 1:
                return f"Please tag only ONE agent or user at a time. Found multiple @mentions: {', '.join('@' + m for m in matches)}"
            else:
                return "Please start your message with @AgentKey … (e.g., @agent_1 How many records?)."

        agent_key, content = parsed
        members = set(session_store.list_group_agents(group_id))
        if agent_key not in members:
            return f"Unknown or non-member agent '@{agent_key}' for this group."

        # Use the same logic as single-agent case but with parsed content
        # Persist + emit user message
        session_store.append_message(group_id, sender=sender, role="user" if sender == "user" else "agent", content=text)
        await emit_message(group_id, sender=sender, role="user" if sender == "user" else "agent", content=text)

        # Get agent response with document context
        reply = await self.o.process_user_message(group_id, agent_key, content)

        # Save agent response only if it's not empty
        if str(reply).strip():
            session_store.append_message(group_id, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key})
            await emit_message(group_id, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)

            # Process mentions in agent response for automatic chaining
            await self._process_mentions_in_message(group_id, str(reply), agent_key)

        return str(reply)

    async def _process_mentions_in_message(self, group_id: str, message: str, current_sender: str, max_depth: int = 5):
        """
        Queue agent mentions for processing - enables real-time conversation display.
        Each agent response appears immediately in UI, then triggers next agent.
        """
        if max_depth <= 0:
            return  # Prevent infinite loops

        agent_mention = self.parse(message)
        if agent_mention:
            target_agent_key, mentioned_content = agent_mention
            members = set(session_store.list_group_agents(group_id))

            # Only route if target agent is in the group and different from current sender
            if target_agent_key in members and target_agent_key != current_sender:
                # Queue agent-to-agent mention for background processing
                # This allows the current response to appear in UI immediately
                asyncio.create_task(self._handle_queued_mention(
                    group_id, target_agent_key, mentioned_content, current_sender, max_depth - 1
                ))

    async def _handle_queued_mention(self, group_id: str, target_agent_key: str, mentioned_content: str, original_sender: str, remaining_depth: int):
        """
        Handle queued agent mention - processes in background for real-time UI updates.
        """
        try:
            # Process agent-to-agent communication
            agent_reply = await self.o.process_user_message(group_id, target_agent_key, mentioned_content)

            # Save the agent-to-agent response (appears immediately in UI)
            if str(agent_reply).strip():
                session_store.append_message(group_id, sender=target_agent_key, role="agent", content=str(agent_reply), metadata={"agent_key": target_agent_key})
                await emit_message(group_id, sender=target_agent_key, role="agent", content=str(agent_reply), agent_key=target_agent_key)

                # Check for user mentions to trigger sound notification
                if "@user" in str(agent_reply).lower():
                    await self._emit_user_notification(group_id, target_agent_key, str(agent_reply))

                # Continue processing any @mentions in this response (non-recursive)
                await self._process_mentions_in_message(group_id, str(agent_reply), target_agent_key, remaining_depth)

        except Exception as e:
            print(f"❌ Error processing queued mention: {e}")
            await emit_error(group_id, "router", f"Agent-to-agent mention failed: {str(e)}")

    async def _emit_user_notification(self, group_id: str, agent_key: str, message: str):
        """
        Emit special notification event when user is mentioned - triggers sound notification.
        """
        from src.core.telemetry.events import EVENT_BUS, TelemetryEvent, now_ts
        await EVENT_BUS.publish(TelemetryEvent(
            ts=now_ts(),
            group_id=group_id,
            kind="user_mention",
            agent_key=agent_key,
            payload={"message": message, "notification": "sound"}
        ))

    async def route_message(self, group_id: str, message: str) -> str:
        """Route a message (used internally for agent-to-agent communication)"""
        return await self.handle_user_message(group_id, message)
