from django.db import models, connection
from apps.core.models import TimeStampedModel

class Document(TimeStampedModel):
    """
    Document model - Files uploaded to groups.

    Documents are tenant-specific - isolated per tenant for multi-tenancy.
    Each document belongs to a group within a tenant.
    """

    # CRITICAL: Tenant field for multi-tenancy and local backend sync
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Tenant this document belongs to",
        db_index=True
    )

    group = models.UUIDField(help_text="Group ID this document belongs to")
    filename = models.CharField(max_length=500, help_text="Original filename")
    storage_path = models.CharField(max_length=1000, help_text="Path in storage (MinIO/S3)")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, help_text="MIME type")
    uploaded_by = models.UUIDField(help_text="User ID who uploaded")
    embeddings_indexed = models.BooleanField(default=False, help_text="Whether embeddings are in Qdrant")
    qdrant_collection = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'group', 'created_at']),
            models.Index(fields=['tenant', 'uploaded_by']),
            models.Index(fields=['tenant', 'embeddings_indexed']),
        ]

    def __str__(self):
        return f"[{self.tenant.name}] {self.filename}"

    def save(self, *args, **kwargs):
        """Auto-set tenant from current schema context"""
        if not self.tenant_id:
            schema_name = connection.schema_name
            if schema_name != 'public':
                from apps.tenants.models import Tenant
                self.tenant = Tenant.objects.get(schema_name=schema_name)
        super().save(*args, **kwargs)
