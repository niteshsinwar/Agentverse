from django.db import models
from apps.core.models import TimeStampedModel

class Group(TimeStampedModel):
    name = models.CharField(max_length=255, help_text="Group name")
    description = models.TextField(blank=True, null=True)
    members = models.JSONField(default=list, help_text="List of user IDs")
    assigned_agents = models.JSONField(default=list, help_text="List of agent IDs assigned to this group")
    created_by = models.UUIDField(help_text="User ID who created this group")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['name']), models.Index(fields=['created_by'])]

    def __str__(self):
        return self.name
