from django.db import models
from apps.core.models import TimeStampedModel

class Message(TimeStampedModel):
    group = models.UUIDField(help_text="Group ID this message belongs to")
    sender_type = models.CharField(max_length=20, choices=[('user', 'User'), ('agent', 'Agent')], help_text="Who sent the message")
    sender_id = models.UUIDField(help_text="User or Agent ID")
    content = models.TextField(help_text="Message content")
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['sender_id']),
        ]

    def __str__(self):
        return f"{self.sender_type}: {self.content[:50]}"
