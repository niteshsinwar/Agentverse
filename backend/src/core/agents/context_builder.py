"""
Agent Context Builder - Centralized Context Management

This module provides ALL context that agents receive. Understanding what gets
injected and why is critical for agent behavior.

═══════════════════════════════════════════════════════════════════════════════
CONTEXT COMPONENTS - What Agents See and Why
═══════════════════════════════════════════════════════════════════════════════

1. 🆔 AGENT IDENTITY
   What: Agent ID, name, and specialty description
   Why: Agents need to know WHO they are and WHAT they specialize in
   Example: "You are filesystem_agent (File & Directory Manager)"
            "Specialty: Manage files, folders, read/write operations"
   Impact: Helps agent understand its role and stay in its domain

2. 🛠️ CAPABILITIES (Tools Summary)
   What: Count of custom tools + MCP tools available
   Why: Agents need to know WHAT actions they can take
   Example: "Available tools: 13 custom, 4 MCP"
   Impact: Agent knows if it can solve a task or needs to delegate

   Components:
   - Custom tools: Defined in agent's tools.py (mkdir, write_file, etc.)
   - MCP tools: From MCP servers (browser_navigate, browser_type, etc.)
   - Reflect tool: Universal meta-tool for planning/thinking (ALL agents get this)

3. 👥 GROUP ROSTER
   What: List of all agents in current group with their specialties
   Why: Agents need to know WHO to collaborate with and WHAT they do
   Example: "- @filesystem_agent — File Manager: Handles file operations"
            "- @playwright_agent — Web Automation: Browser navigation"
   Impact: Enables smart delegation (agent knows who to @mention for tasks)
   Note: Descriptions come from agent.yaml metadata, critical for collaboration

4. 💬 CONVERSATION SUMMARY (Progressive)
   What: AI-generated summary of earlier messages (when >20 messages)
   Why: Prevents context overflow, maintains long conversation memory
   Example: "User requested file creation. Agent created folder and files."
   Impact: Agent remembers key points from long conversations
   Trigger: Automatic after 20 messages, uses LLM to summarize
   Storage: Persisted in database, reused across sessions

5. 📜 RECENT CONVERSATION (Last 10 Messages)
   What: Exact transcript of last 10 messages (user, agent, thoughts, tools)
   Why: Agents need immediate context for current conversation flow
   Example: "User: create folder"
            "filesystem_agent: [Thought] I have mkdir tool"
            "[tool_call] mkdir called with {...}"
   Impact: Agent sees what just happened and can continue naturally
   Includes: User messages, agent responses, tool calls, tool results, thoughts

6. 📚 RETRIEVED KNOWLEDGE BASE (RAG Context)
   What: Relevant chunks from document embeddings (if any match query)
   Why: Agents can answer questions using uploaded documents
   Example: "Transformer architecture uses self-attention mechanism..."
   Impact: Agent can cite actual documents instead of hallucinating
   Source: ChromaDB vector search on user's uploaded docs
   Threshold: Only included if similarity > 0.35

7. 📋 RULES & GUIDELINES (Battle-tested)
   What: Behavioral instructions for collaboration, @mentions, tools
   Why: Ensures consistent, predictable agent behavior
   Impact: Defines HOW agents should behave in different scenarios

   Includes:
   - @Mention system (control transfer mechanism)
   - Autonomous decision-making hierarchy
   - Reflect tool usage guidance
   - Task validation (sufficient info check)
   - Knowledge base integration
   - Tool execution patterns

═══════════════════════════════════════════════════════════════════════════════
FLOW VISUALIZATION
═══════════════════════════════════════════════════════════════════════════════

User sends message
      ↓
Router determines target agent
      ↓
Context Builder assembles:
      ├─ Agent Identity (WHO am I?)
      ├─ Capabilities (WHAT can I do?)
      ├─ Group Roster (WHO can I collaborate with?)
      ├─ Conversation Summary (WHAT happened earlier?)
      ├─ Recent Messages (WHAT just happened?)
      ├─ RAG Context (WHAT knowledge is relevant?)
      └─ Rules (HOW should I behave?)
      ↓
LangGraph Agent receives full context
      ↓
Agent makes decision (autonomous framework)
      ↓
Agent executes (tools/reflect/response)
      ↓
Result sent to user/other agents

═══════════════════════════════════════════════════════════════════════════════
"""
from typing import Dict, Any, List, Tuple, Optional
from src.core.memory import session_store


MAX_CONVERSATION_HISTORY = 20


class AgentContextBuilder:
    """
    Centralized context builder for all agents.

    Provides two main interfaces:
    1. build_system_prompt() - For deprecated agents (JSON-based)
    2. build_agent_context() - For new LangChain agents (natural language)

    Both use shared helper methods for consistency.
    """

    # ============================================================================
    # HELPER METHODS (Shared by both old and new agents)
    # ============================================================================

    async def _get_summarized_conversation(
        self,
        group_id: str
    ) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Get conversation with optional summarization.

        Returns:
            (summary_text, recent_messages)
        """
        hist = session_store.get_history(group_id) if group_id else []
        if not hist:
            return None, []

        message_count = len(hist)

        # Get settings
        from src.core.config.settings import get_settings
        settings = get_settings()
        summary_enabled = getattr(settings, 'conversation_summary_enabled', True)
        trigger_count = getattr(settings, 'conversation_summary_trigger_count', 20)

        # Check if summarization needed
        if summary_enabled and message_count >= trigger_count:
            from src.core.memory.summarizer import conversation_summarizer

            # Get existing summary
            summary_data = session_store.get_group_summary(group_id)
            previous_summary = summary_data["summary"] if summary_data else None
            last_summarized_count = summary_data["last_summarized_count"] if summary_data else 0

            # Process conversation
            result = await conversation_summarizer.process_conversation(
                full_conversation=hist,
                previous_summary=previous_summary,
                last_summarized_count=last_summarized_count
            )

            if result["should_summarize"]:
                # Save new summary
                session_store.upsert_group_summary(
                    group_id=group_id,
                    summary=result["summary"],
                    last_summarized_count=result["total_summarized"]
                )

            return result["summary"], result["recent_messages"]
        else:
            # No summarization - return recent messages
            return None, hist[-MAX_CONVERSATION_HISTORY:]

    def _format_conversation_history(
        self,
        messages: List[Dict[str, Any]],
        limit: int = 10
    ) -> str:
        """
        Format conversation messages into readable history.

        Args:
            messages: List of message dicts
            limit: Max messages to include

        Returns:
            Formatted history string
        """
        lines = []

        for msg in messages[-limit:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            sender = msg.get("sender", "unknown")

            if role == "user":
                lines.append(f"User: {content}")
            elif role == "agent":
                agent_key = msg.get("metadata", {}).get("agent_key", sender)
                lines.append(f"{agent_key}: {content}")
            elif role == "system":
                lines.append(f"[System] {content}")
            elif role == "agent_thought":
                lines.append(f"[Thought] {content}")
            elif role in ("tool_call", "tool_result", "tool_error", "mcp_call", "mcp_result", "mcp_error"):
                lines.append(f"[{role}] {content}")

        return "\n".join(lines) if lines else "(No conversation yet)"

    def _format_roster(self, roster: List[Tuple[str, str, str]]) -> str:
        """Format roster as detailed list."""
        return "\n".join([
            f"- @{k} — {n}: {d}"
            for (k, n, d) in roster
        ]) or "- (no other members)"

    def _build_history_section(
        self,
        summary_text: Optional[str],
        history_text: str,
        rag_context: str,
        recent_msg_count: int
    ) -> str:
        """
        Build formatted history section with summary and RAG.

        Returns:
            Complete history section with markers
        """
        sections = []

        # Add summary if available
        if summary_text:
            sections.append(f"\n\n=== CONVERSATION SUMMARY (Earlier Messages) ===\n{summary_text}\n")

        # Add recent conversation
        sections.append(f"\n\n=== RECENT CONVERSATION (Last {recent_msg_count} messages) ===\n")
        sections.append(history_text)
        sections.append("\n=== END HISTORY ===\n")

        # Add RAG context if available
        if rag_context and rag_context.strip():
            sections.append(f"\n=== RETRIEVED KNOWLEDGE BASE (Latest) ===\n{rag_context}\n")
            sections.append("=== END RETRIEVED KNOWLEDGE ===\n")

        return "".join(sections)

    def _get_battle_tested_rules(self, agent_id: str) -> str:
        """
        Get battle-tested rules and guidelines for LangGraph agents.

        Args:
            agent_id: Current agent ID

        Returns:
            Complete behavioral rules and guidelines
        """
        rules = (
            "RULES AND GUIDELINES:\n"
            "- You respond with natural language (NOT JSON)\n"
            "- Tools are called automatically when you decide to use them\n"
        )

        # Battle-tested behavioral rules
        rules += (
            f"- 🎯 @MENTION SYSTEM (Controls Workflow):\n"
            f"  • EVERY response MUST end with exactly ONE @mention\n"
            f"  • @mention TRANSFERS CONTROL - when you mention someone, they get the task next\n"
            f"  • This is how you call/invoke another agent or return control to user\n"
            f"  • Only use agents listed in Group section above\n"
            f"  \n"
            f"  When to use each:\n"
            f"  • @user: Task complete, need user input, errors, or chit-chat response\n"
            f"  • @agent_name: Delegating to specialist, continuing collaborative workflow\n"
            f"  \n"
            f"- 🤖 AUTONOMOUS & COLLABORATIVE BEHAVIOR:\n"
            f"  • PREFER agent-to-agent collaboration over returning to user\n"
            f"  • Be AUTONOMOUS: If you have sufficient info + right tools, solve it yourself\n"
            f"  • Be COLLABORATIVE: Delegate to specialists instead of struggling alone\n"
            f"  • Be INTELLIGENT: Don't ask for info already in conversation history\n"
            f"  \n"
            f"  Decision hierarchy when given a task:\n"
            f"  1. Check: Do I have sufficient information? (review conversation + knowledge base)\n"
            f"  2. If YES → Solve it yourself (use reflect tool to plan, then execute)\n"
            f"  3. If NO → Can another agent in group help? (check specialties)\n"
            f"  4. If agents can't help → Ask @user specific clarifying questions\n"
            f"  \n"
            f"  Handling user requests:\n"
            f"  • Vague/unclear: Ask specific clarifying questions about what you need\n"
            f"  • Chit-chat: Respond naturally, mention @user\n"
            f"  • Complex tasks: Use reflect tool to plan, break into steps, execute\n"
            f"  • Extremely specific: Execute directly if you have the capability\n"
        )

        rules += (
            f"- 💭 REFLECT TOOL (Planning & Deep Thinking):\n"
            f"  • Use reflect() to share your internal thoughts, planning, and reasoning\n"
            f"  • Call reflect() BEFORE taking actions to show your decision-making process\n"
            f"  • This helps users understand WHY you're doing what you're doing\n"
            f"  \n"
            f"  When to use reflect():\n"
            f"  • Complex tasks with multiple steps → Plan the workflow\n"
            f"  • Analyzing if you have sufficient info → Think out loud about what's missing\n"
            f"  • Deciding between options → Explain your reasoning\n"
            f"  • Before delegating to another agent → Explain why they're better suited\n"
            f"  • Breaking down vague requests → Show your understanding and approach\n"
            f"  \n"
            f"  Examples:\n"
            f"  • reflect(thought=\"User wants folder + files. I have mkdir and write_file tools. Plan: 1) mkdir, 2) write first file, 3) write second file\")\n"
            f"  • reflect(thought=\"Task needs web navigation but I'm filesystem_agent. playwright_agent has browser tools. Will delegate to them.\")\n"
            f"  • reflect(thought=\"Request is vague - they said 'make it better' but no specifics. I should ask what aspect they want improved.\")\n"
            f"  \n"
            f"- ⚙️ TOOL EXECUTION:\n"
            f"  • Call tools ONE AT A TIME for multi-step operations\n"
            f"  • Each tool call should complete before starting the next\n"
            f"  • This allows real-time UI updates as you work\n"
            f"  \n"
            f"- 📚 KNOWLEDGE BASE USAGE:\n"
            f"  • Retrieved knowledge appears in RETRIEVED KNOWLEDGE BASE section above\n"
            f"  • ALWAYS check retrieved context before answering questions\n"
            f"  • Use retrieved information naturally in responses\n"
            f"  • If context insufficient, acknowledge and ask for clarification\n"
            f"  • Do NOT hallucinate - use retrieved context or admit uncertainty\n"
            f"  • If no relevant knowledge retrieved, say so and offer to search or ask user"
        )

        return rules

    # ============================================================================
    # REACT AGENT METHODS (Production - Used by all current agents)
    # ============================================================================

    async def build_react_agent_identity(
        self,
        agent_id: str,
        agent_metadata: Dict[str, Any],
        roster: List[Tuple[str, str, str]],
        tools_summary: str
    ) -> str:
        """
        Build agent identity for ReAct agent (NO conversation history).

        This method injects:
        1. 🆔 AGENT IDENTITY: WHO am I and WHAT do I specialize in?
        2. 🛠️ CAPABILITIES: WHAT tools/actions can I take?
        3. 👥 GROUP ROSTER: WHO can I collaborate with and WHAT do they do?
        4. 📋 RULES: HOW should I behave?

        Note: Conversation history handled separately for ReAct format compatibility.

        Args:
            agent_id: Unique agent identifier (e.g., "filesystem_agent")
            agent_metadata: Dict with 'name' and 'description' from agent.yaml
                           ⚠️ Description is CRITICAL - shown to other agents for delegation
            roster: List of (agent_id, name, description) for ALL agents in group
                   ⚠️ This enables collaboration - agents see who to delegate to
            tools_summary: "Available tools: X custom, Y MCP" (from tool wrapper)

        Returns:
            Complete identity context (no conversation/RAG - those come separately)
        """
        # Format roster with descriptions (CRITICAL for agent collaboration)
        # Each line: "- @agent_id — Name: Description"
        # This tells agents WHO can help and WHAT they specialize in
        roster_lines = self._format_roster(roster)

        identity = (
            # 1. AGENT IDENTITY: WHO am I?
            f"AGENT IDENTITY:\n"
            f"You are {agent_id} ({agent_metadata.get('name')})\n"
            # Specialty from agent.yaml - defines agent's domain
            f"Specialty: {agent_metadata.get('description', 'General purpose')}\n"
            # Tools summary - lets agent know if it CAN solve a task
            f"Capabilities: {tools_summary}\n\n"

            # 2. GROUP ROSTER: WHO can I work with?
            # ⚠️ CRITICAL: Agents use this to decide who to @mention for delegation
            # Without descriptions, agents can't delegate intelligently
            f"GROUP MEMBERS:\n"
            f"{roster_lines}\n\n"

            # 3. RULES & GUIDELINES: HOW should I behave?
            # Includes @mention system, autonomous behavior, reflect tool, etc.
            f"{self._get_battle_tested_rules(agent_id)}"
        )

        return identity

    async def build_react_conversation_context(
        self,
        group_id: str,
        rag_context: str = ""
    ) -> str:
        """
        Build conversation context for ReAct agent.

        This method injects:
        1. 💬 CONVERSATION SUMMARY: What happened earlier? (if >20 messages)
        2. 📜 RECENT MESSAGES: What just happened? (last 10 messages)
        3. 📚 RAG CONTEXT: What knowledge is relevant? (from document search)

        This is separate from identity to support ReAct's message-based format.

        Args:
            group_id: Current conversation group ID
            rag_context: Retrieved document chunks from ChromaDB (optional)
                        ⚠️ Only included if vector search finds relevant docs (similarity > 0.35)

        Returns:
            Complete conversation + knowledge context (identity comes separately)
        """
        # Get conversation with automatic summarization
        # If >20 messages: Returns (summary, last 10 messages)
        # If <20 messages: Returns (None, all messages up to 20)
        summary_text, recent_messages = await self._get_summarized_conversation(group_id)

        # Format messages into readable transcript
        # Includes: user messages, agent responses, thoughts, tool calls, results
        history_text = self._format_conversation_history(recent_messages, limit=10)

        # Build context section with clear markers
        sections = []

        # 1. CONVERSATION SUMMARY (only if conversation is long)
        # WHY: Prevents context overflow in long conversations
        # HOW: LLM generates summary of messages 1-N, keeps recent 10 raw
        if summary_text:
            sections.append(f"CONVERSATION SUMMARY (Earlier Messages):\n{summary_text}\n")

        # 2. RECENT CONVERSATION (always included)
        # WHY: Agent needs immediate context to continue naturally
        # WHAT: Last 10 messages with full detail (user, agent, tools, thoughts)
        sections.append(f"RECENT CONVERSATION (Last {len(recent_messages[-10:])} messages):\n")
        sections.append(history_text)

        # 3. RETRIEVED KNOWLEDGE BASE (only if RAG found relevant docs)
        # WHY: Agents should cite documents instead of hallucinating
        # WHEN: User uploaded docs + query matched embeddings (similarity > 0.35)
        # SOURCE: ChromaDB vector search on user's document collection
        if rag_context and rag_context.strip():
            sections.append(f"\n\nRETRIEVED KNOWLEDGE BASE:\n{rag_context}")

        return "\n".join(sections) if sections else "(No prior conversation)"


# Global instance
context_builder = AgentContextBuilder()
