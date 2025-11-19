"""
Core Models - Base models and utilities for all apps
"""

from django.db import models
import uuid


class TimeStampedModel(models.Model):
    """
    Abstract base class with created_at and updated_at timestamps.

    All tenant models should inherit from this.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
