from django.db import models
from apps.core.models import TimeStampedModel

class UsageLog(TimeStampedModel):
    tenant = models.UUIDField(help_text="Tenant ID")
    user = models.UUIDField(help_text="User ID", blank=True, null=True)
    action = models.CharField(max_length=100, help_text="Action type (e.g., 'message_sent', 'agent_created')")
    resource_type = models.CharField(max_length=50, help_text="Resource type (e.g., 'agent', 'message')", blank=True, null=True)
    resource_id = models.UUIDField(help_text="Resource ID", blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.action} at {self.created_at}"
