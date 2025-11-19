"""
Agent Models
"""

from django.db import models, connection
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

    Agents are tenant-specific - isolated per tenant for multi-tenancy.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='agents',
        help_text="Tenant this agent belongs to",
        db_index=True
    )

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
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'llm_provider']),
            models.Index(fields=['tenant', 'created_by']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        # Ensure agent names are unique within a tenant
        unique_together = [['tenant', 'name']]

    def __str__(self):
        return f"{self.emoji} {self.name}"

    def save(self, *args, **kwargs):
        """Auto-set tenant from current schema context"""
        if not self.tenant_id:
            schema_name = connection.schema_name
            if schema_name != 'public':
                from apps.tenants.models import Tenant
                self.tenant = Tenant.objects.get(schema_name=schema_name)
        super().save(*args, **kwargs)
