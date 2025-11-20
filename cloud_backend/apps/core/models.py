"""
Core Models - Base models and utilities for all apps
"""

from django.db import models
from django.conf import settings
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


class Permission(TimeStampedModel):
    """
    Permission model - Fine-grained access control for users and agents.

    Defines what actions a user/agent can perform on resources.
    Applies to BOTH humans and agents uniformly.

    Example:
        # User has full access to specific agent
        Permission(
            tenant=tenant1,
            subject_type='user',
            subject_id=user_uuid,
            resource_type='agent',
            resource_id=agent_uuid,
            can_view=True,
            can_create=False,
            can_update=True,
            can_delete=False,
            can_execute=True
        )

        # Agent can execute all tools
        Permission(
            tenant=tenant1,
            subject_type='agent',
            subject_id=agent_uuid,
            resource_type='tool',
            resource_id=None,  # None = all tools
            can_execute=True
        )
    """

    # Multi-tenancy
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text="Tenant this permission belongs to",
        db_index=True
    )

    # Subject (who has the permission) - can be user OR agent
    subject_type = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User'),
            ('agent', 'Agent'),
        ],
        help_text="Type of entity this permission applies to"
    )
    subject_id = models.UUIDField(
        help_text="ID of the user or agent"
    )

    # Resource (what the permission applies to)
    resource_type = models.CharField(
        max_length=20,
        choices=[
            ('agent', 'Agent'),
            ('tool', 'Tool'),
            ('mcp_server', 'MCP Server'),
            ('group', 'Group'),
            ('message', 'Message'),
            ('document', 'Document'),
        ],
        help_text="Type of resource"
    )
    resource_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="ID of specific resource (null = all resources of type)"
    )

    # Actions (CRUD + Execute)
    can_view = models.BooleanField(default=True, help_text="Can view/read resource")
    can_create = models.BooleanField(default=False, help_text="Can create new resources")
    can_update = models.BooleanField(default=False, help_text="Can update/edit resource")
    can_delete = models.BooleanField(default=False, help_text="Can delete resource")
    can_execute = models.BooleanField(default=False, help_text="Can execute (agents/tools only)")

    # Metadata
    granted_by = models.UUIDField(
        null=True,
        blank=True,
        help_text="User ID who granted this permission (admin)"
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for granting/revoking permission"
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = [
            ['tenant', 'subject_type', 'subject_id', 'resource_type', 'resource_id']
        ]
        indexes = [
            models.Index(fields=['tenant', 'subject_type', 'subject_id']),
            models.Index(fields=['tenant', 'resource_type', 'resource_id']),
            models.Index(fields=['subject_type', 'subject_id', 'resource_type']),
        ]

    def __str__(self):
        resource_str = f"{self.resource_type}"
        if self.resource_id:
            resource_str += f":{str(self.resource_id)[:8]}"
        else:
            resource_str += ":all"

        subject_str = f"{self.subject_type}:{str(self.subject_id)[:8]}"

        actions = []
        if self.can_view:
            actions.append("view")
        if self.can_create:
            actions.append("create")
        if self.can_update:
            actions.append("update")
        if self.can_delete:
            actions.append("delete")
        if self.can_execute:
            actions.append("execute")

        return f"{subject_str} → {resource_str} [{','.join(actions)}]"
