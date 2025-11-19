from django.db import models, connection
from apps.core.models import TimeStampedModel

class Group(TimeStampedModel):
    """
    Group model - Teams/channels for organizing users and agents.

    Groups are tenant-specific - each tenant has isolated groups.
    Users can be members of groups within their tenant.
    Agents can be assigned to groups for team-based conversations.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='groups',
        help_text="Tenant this group belongs to",
        db_index=True
    )

    name = models.CharField(max_length=255, help_text="Group name")
    description = models.TextField(blank=True, null=True)
    members = models.JSONField(default=list, help_text="List of user IDs")
    assigned_agents = models.JSONField(default=list, help_text="List of agent IDs assigned to this group")
    created_by = models.UUIDField(help_text="User ID who created this group")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'name']),
            models.Index(fields=['tenant', 'created_by']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        # Ensure group names are unique within a tenant
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
