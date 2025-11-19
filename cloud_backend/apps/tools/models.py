from django.db import models
from apps.core.models import TimeStampedModel

class Tool(TimeStampedModel):
    name = models.CharField(max_length=255, help_text="Tool name")
    description = models.TextField(help_text="Tool description")
    code = models.TextField(help_text="Python code for the tool")
    dependencies = models.JSONField(default=list, help_text="Python package dependencies")
    created_by = models.UUIDField(help_text="User ID who created this tool")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['name']), models.Index(fields=['created_by'])]

    def __str__(self):
        return self.name
