# =========================================
# File: app/agents/router.py
# Purpose: Route user messages that must @mention a group member
# =========================================
from __future__ import annotations
import re
from typing import Optional, Tuple
from src.core.memory import session_store
from src.core.telemetry.events import emit_message

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

    async def handle_user_message(self, group_id: str, text: str) -> str:
        members = session_store.list_group_agents(group_id)
        
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
            
            return str(reply)
        
        # Original code for multiple agents
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

        # Persist + emit user message
        session_store.append_message(group_id, sender="user", role="user", content=text)
        await emit_message(group_id, sender="user", role="user", content=text)

        # Get agent response with document context
        reply = await self.o.process_user_message(group_id, agent_key, content)

        # Save agent response only if it's not empty (post_message returns empty string)
        if str(reply).strip():
            session_store.append_message(group_id, sender=agent_key, role="agent", content=str(reply), metadata={"agent_key": agent_key})
            await emit_message(group_id, sender=agent_key, role="agent", content=str(reply), agent_key=agent_key)

            # Check if agent response contains @mentions for agent-to-agent communication
            agent_mention = self.parse(str(reply))
            if agent_mention:
                target_agent_key, mentioned_content = agent_mention
                members = set(session_store.list_group_agents(group_id))

                # Only route if target agent is in the group and different from current agent
                if target_agent_key in members and target_agent_key != agent_key:
                    # Process agent-to-agent communication
                    agent_reply = await self.o.process_user_message(group_id, target_agent_key, mentioned_content)

                    # Save the agent-to-agent response
                    if str(agent_reply).strip():
                        session_store.append_message(group_id, sender=target_agent_key, role="agent", content=str(agent_reply), metadata={"agent_key": target_agent_key})
                        await emit_message(group_id, sender=target_agent_key, role="agent", content=str(agent_reply), agent_key=target_agent_key)

        return str(reply)

    async def route_message(self, group_id: str, message: str) -> str:
        """Route a message (used internally for agent-to-agent communication)"""
        return await self.handle_user_message(group_id, message)
