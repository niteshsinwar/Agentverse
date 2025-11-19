from django.db import models, connection
from apps.core.models import TimeStampedModel

class Message(TimeStampedModel):
    """
    Message model - Chat messages in groups.

    Messages are tenant-specific - isolated per tenant for multi-tenancy.
    Each message belongs to a group within a tenant.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Tenant this message belongs to",
        db_index=True
    )

    group = models.UUIDField(help_text="Group ID this message belongs to")
    sender_type = models.CharField(max_length=20, choices=[('user', 'User'), ('agent', 'Agent')], help_text="Who sent the message")
    sender_id = models.UUIDField(help_text="User or Agent ID")
    content = models.TextField(help_text="Message content")
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['tenant', 'group', 'created_at']),
            models.Index(fields=['tenant', 'sender_id']),
        ]

    def __str__(self):
        return f"[{self.tenant.name}] {self.sender_type}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        """Auto-set tenant from current schema context"""
        if not self.tenant_id:
            schema_name = connection.schema_name
            if schema_name != 'public':
                from apps.tenants.models import Tenant
                self.tenant = Tenant.objects.get(schema_name=schema_name)
        super().save(*args, **kwargs)
