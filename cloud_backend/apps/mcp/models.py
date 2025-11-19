from django.db import models, connection
from apps.core.models import TimeStampedModel

class MCPServer(TimeStampedModel):
    """
    MCP Server model - Model Context Protocol server configuration.

    MCP servers are tenant-specific - isolated per tenant for multi-tenancy.
    Each MCP server provides tools and resources that agents can use.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='mcp_servers',
        help_text="Tenant this MCP server belongs to",
        db_index=True
    )

    name = models.CharField(max_length=255, help_text="MCP server name")
    description = models.TextField(blank=True, null=True)
    command = models.CharField(max_length=255, help_text="Command to run (e.g., npx)")
    args = models.JSONField(default=list, help_text="Command arguments")
    env = models.JSONField(default=dict, help_text="Environment variables")
    created_by = models.UUIDField(help_text="User ID who created this MCP server")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'created_by']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        # Ensure MCP server names are unique within a tenant
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
