from django.db import models
from apps.core.models import TimeStampedModel

class Document(TimeStampedModel):
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
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return self.filename
