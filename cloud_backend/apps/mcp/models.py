from django.db import models
from apps.core.models import TimeStampedModel

class MCPServer(TimeStampedModel):
    name = models.CharField(max_length=255, help_text="MCP server name")
    description = models.TextField(blank=True, null=True)
    command = models.CharField(max_length=255, help_text="Command to run (e.g., npx)")
    args = models.JSONField(default=list, help_text="Command arguments")
    env = models.JSONField(default=dict, help_text="Environment variables")
    created_by = models.UUIDField(help_text="User ID who created this MCP server")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['name']), models.Index(fields=['created_by'])]

    def __str__(self):
        return self.name
