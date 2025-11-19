"""
Agent Models
"""

from django.db import models
from apps.core.models import TimeStampedModel


class Agent(TimeStampedModel):
    """
    Agent model - AI agent configuration.

    Each agent has:
    - Name and description
    - LLM provider and model
    - System prompt
    - Configuration (temperature, max_tokens, etc.)
    - Emoji icon
    - Creator info
    """

    name = models.CharField(max_length=255, help_text="Agent name")
    description = models.TextField(help_text="Agent description")
    emoji = models.CharField(max_length=10, default='🤖')

    # LLM Configuration
    llm_provider = models.CharField(
        max_length=50,
        choices=[
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('gemini', 'Google Gemini'),
            ('ollama', 'Ollama'),
        ],
        default='openai',
        help_text="LLM provider"
    )
    llm_model = models.CharField(
        max_length=100,
        help_text="LLM model name (e.g., gpt-4o, claude-sonnet-4.5)"
    )

    # System prompt
    system_prompt = models.TextField(
        blank=True,
        null=True,
        help_text="System prompt for the agent"
    )

    # Configuration (JSON field for flexibility)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional configuration (temperature, max_tokens, etc.)"
    )

    # Creator
    created_by = models.UUIDField(help_text="User ID who created this agent")

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['llm_provider']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.emoji} {self.name}"
