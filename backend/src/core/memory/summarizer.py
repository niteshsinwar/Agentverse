"""
Conversation Summarizer
Implements progressive summarization for long conversations
Formula: When 20 messages → summarize first 10 + previous summary → keep last 10 raw
"""
from typing import List, Dict, Any, Optional
from src.core.config.settings import get_settings


class ConversationSummarizer:
    """
    Progressive conversation summarization using sliding window

    Industry-standard approach:
    - Trigger: Every N messages (default 20)
    - Summarize: First M messages (default 10) + previous summary
    - Keep: Last (N-M) messages raw (default 10)

    Result: Agent context = Summary + Last 10 messages
    """

    def __init__(self):
        self.settings = get_settings()

        # Load configuration
        self.enabled = getattr(self.settings, 'conversation_summary_enabled', True)
        self.trigger_count = getattr(self.settings, 'conversation_summary_trigger_count', 20)
        self.window_size = getattr(self.settings, 'conversation_summary_window_size', 10)
        # Use default LLM model for summarization
        self.model = getattr(self.settings, 'llm_model', 'gpt-4o-mini')
        self.max_tokens = getattr(self.settings, 'conversation_summary_max_tokens', 500)

        # Initialize LLM client
        self._init_llm_client()

    def _init_llm_client(self):
        """Initialize LLM client based on summary model"""
        # Determine provider from model name
        if self.model.startswith('gpt-'):
            from openai import OpenAI
            import os
            api_key = self.settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
            self.llm_client = OpenAI(api_key=api_key) if api_key else OpenAI()
            self.provider = "openai"
        elif self.model.startswith('claude-'):
            from anthropic import Anthropic
            import os
            api_key = self.settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
            self.llm_client = Anthropic(api_key=api_key) if api_key else Anthropic()
            self.provider = "anthropic"
        elif self.model.startswith('gemini-'):
            import google.generativeai as genai
            import os
            api_key = self.settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            self.llm_client = genai
            self.provider = "gemini"
        else:
            # Default to OpenAI
            from openai import OpenAI
            self.llm_client = OpenAI()
            self.provider = "openai"

    def should_summarize(self, message_count: int) -> bool:
        """
        Check if summarization should be triggered

        Args:
            message_count: Total messages in conversation

        Returns:
            True if message_count >= trigger_count
        """
        if not self.enabled:
            return False

        return message_count >= self.trigger_count

    def format_messages_for_summary(
        self,
        messages: List[Dict[str, Any]],
        previous_summary: Optional[str] = None
    ) -> str:
        """
        Format messages for LLM summarization

        Args:
            messages: List of message dicts with 'sender', 'role', 'content'
            previous_summary: Previous conversation summary (if exists)

        Returns:
            Formatted string for summarization prompt
        """
        formatted = []

        if previous_summary:
            formatted.append(f"**PREVIOUS SUMMARY:**\n{previous_summary}\n")

        formatted.append("**MESSAGES TO SUMMARIZE:**\n")
        for i, msg in enumerate(messages, 1):
            sender = msg.get('sender', 'unknown')
            content = msg.get('content', '')
            formatted.append(f"{i}. [{sender}]: {content}")

        return "\n".join(formatted)

    async def generate_summary(
        self,
        messages: List[Dict[str, Any]],
        previous_summary: Optional[str] = None
    ) -> str:
        """
        Generate conversation summary using LLM

        Args:
            messages: Messages to summarize (first 10 from conversation)
            previous_summary: Previous summary (recursive accumulation)

        Returns:
            Concise summary of conversation topics and key points
        """
        formatted_messages = self.format_messages_for_summary(messages, previous_summary)

        system_prompt = (
            "You are a conversation summarizer. Create a concise summary of the conversation "
            "that captures:\n"
            "1. Main topics discussed\n"
            "2. Key decisions or conclusions\n"
            "3. Important context for future messages\n"
            "4. User goals and agent responses\n\n"
            "Keep the summary brief (3-5 sentences max) and factual. "
            "If a previous summary exists, integrate it with the new messages to maintain continuity."
        )

        user_prompt = f"{formatted_messages}\n\nProvide a concise summary:"

        try:
            if self.provider == "openai":
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.3  # Low temp for factual summarization
                )
                summary = response.choices[0].message.content.strip()

            elif self.provider == "anthropic":
                response = self.llm_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                summary = response.content[0].text.strip()

            elif self.provider == "gemini":
                model = self.llm_client.GenerativeModel(
                    self.model,
                    system_instruction=system_prompt
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config={"max_output_tokens": self.max_tokens, "temperature": 0.3}
                )
                summary = response.text.strip()

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            print(f"📝 Generated summary ({len(summary)} chars)")
            return summary

        except Exception as e:
            print(f"⚠️ Summary generation failed: {e}")

            # Emit error telemetry
            try:
                from src.core.telemetry.events import emit_error
                import asyncio
                # Try to get group_id from messages
                group_id = messages[0].get('metadata', {}).get('group_id', 'unknown') if messages else 'unknown'
                asyncio.create_task(emit_error(
                    group_id=group_id,
                    where="summarizer",
                    message=f"Summary generation failed: {str(e)}"
                ))
            except:
                pass

            # Fallback: simple concatenation
            return f"Discussion topics: {', '.join([msg.get('content', '')[:50] for msg in messages[:3]])}..."

    async def process_conversation(
        self,
        full_conversation: List[Dict[str, Any]],
        previous_summary: Optional[str] = None,
        last_summarized_count: int = 0
    ) -> Dict[str, Any]:
        """
        Sliding window summarization with triggers every 20 messages

        Strategy:
        - Messages 1-19: Show all (no summary)
        - Message 20 (TRIGGER): Summarize 1-10, show summary + 11-20
        - Messages 21-29: Show summary + last 10 messages
        - Message 30 (TRIGGER): Summarize 11-20, show NEW summary + 21-30
        - And so on...

        Result: Context always contains AI summary + 10 recent messages

        Args:
            full_conversation: Complete conversation history
            previous_summary: Previous summary (if exists)
            last_summarized_count: How many messages already in the summary

        Returns:
            {
                "summary": str,  # Cumulative AI summary
                "recent_messages": List[Dict],  # Last 10 messages (raw)
                "total_summarized": int,  # How many messages in summary
                "should_summarize": bool  # Whether new summary was generated
            }
        """
        message_count = len(full_conversation)

        # Check if we've hit trigger count
        if message_count < self.trigger_count:
            # Not enough messages yet - show all
            return {
                "summary": None,
                "recent_messages": full_conversation,
                "total_summarized": 0,
                "should_summarize": False
            }

        # Calculate how many messages need to be summarized
        # We always keep last window_size (10) messages raw
        messages_that_can_be_summarized = message_count - self.window_size

        # Check if we need to create/update summary
        # Trigger when: messages_that_can_be_summarized - last_summarized_count >= window_size
        unsummarized_count = messages_that_can_be_summarized - last_summarized_count

        if unsummarized_count < self.window_size:
            # Not enough new messages to trigger re-summarization
            # Just return existing summary + last 10 messages
            recent_messages = full_conversation[-self.window_size:]
            print(f"📊 Using existing summary ({unsummarized_count} new messages, need {self.window_size} to trigger)")
            print(f"   Context: AI summary + last {len(recent_messages)} messages")
            return {
                "summary": previous_summary,
                "recent_messages": recent_messages,
                "total_summarized": last_summarized_count,
                "should_summarize": False
            }

        # TRIGGER: We have enough messages to summarize
        # Emit telemetry - summarization started
        try:
            from src.core.telemetry.events import emit_summarization
            # Extract group_id from first message if available
            group_id = full_conversation[0].get('metadata', {}).get('group_id', 'unknown') if full_conversation else 'unknown'
            await emit_summarization(
                group_id=group_id,
                status="start",
                meta={
                    "message_count": message_count,
                    "start_idx": last_summarized_count,
                    "end_idx": last_summarized_count + self.window_size
                }
            )
        except:
            pass

        # Summarize the next batch of window_size messages
        start_idx = last_summarized_count
        end_idx = start_idx + self.window_size
        messages_to_summarize = full_conversation[start_idx:end_idx]

        # Generate new cumulative summary
        new_summary = await self.generate_summary(messages_to_summarize, previous_summary)

        # Recent messages are always the last window_size messages
        recent_messages = full_conversation[-self.window_size:]

        new_total_summarized = end_idx

        print(f"📊 Summarization TRIGGERED:")
        print(f"   Total messages: {message_count}")
        print(f"   Summarized messages {start_idx+1}-{end_idx} (batch of {len(messages_to_summarize)})")
        print(f"   Total in summary: {new_total_summarized} messages")
        print(f"   Recent (raw): last {len(recent_messages)} messages")
        print(f"   Summary length: {len(new_summary)} chars")
        print(f"   Context: AI summary + messages {message_count - self.window_size + 1}-{message_count}")

        # Emit telemetry - summarization complete
        try:
            await emit_summarization(
                group_id=group_id,
                status="complete",
                meta={
                    "total_summarized": new_total_summarized,
                    "summary_length": len(new_summary),
                    "recent_messages_count": len(recent_messages)
                }
            )
        except:
            pass

        return {
            "summary": new_summary,
            "recent_messages": recent_messages,
            "total_summarized": new_total_summarized,
            "should_summarize": True
        }


# Global instance
conversation_summarizer = ConversationSummarizer()
