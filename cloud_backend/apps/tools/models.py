from django.db import models, connection
from apps.core.models import TimeStampedModel

class Tool(TimeStampedModel):
    """
    Tool model - Custom Python tools for agents.

    Tools are tenant-specific - isolated per tenant for multi-tenancy.
    Each tool contains Python code that agents can execute.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='tools',
        help_text="Tenant this tool belongs to",
        db_index=True
    )

    name = models.CharField(max_length=255, help_text="Tool name")
    description = models.TextField(help_text="Tool description")
    code = models.TextField(help_text="Python code for the tool")
    dependencies = models.JSONField(default=list, help_text="Python package dependencies")
    created_by = models.UUIDField(help_text="User ID who created this tool")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'created_by']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        # Ensure tool names are unique within a tenant
        unique_together = [['tenant', 'name']]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"

    def save(self, *args, **kwargs):
        """Auto-set tenant from current schema context"""
        if not self.tenant_id:
            schema_name = connection.schema_name
            if schema_name != 'public':
                from apps.tenants.models import Tenant
                self.tenant = Tenant.objects.get(schema_name=schema_name)
        super().save(*args, **kwargs)
