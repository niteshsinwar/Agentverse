"""
ViewSet Mixins for Permission and License Enforcement

Provides permission-based access control and license limit enforcement for all resources.

Author: AgentVerse Team
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from django.db import connection
from apps.tenants.models import Tenant


class LicenseEnforcedViewSet:
    """
    Mixin to enforce license limits on resource creation.

    Prevents tenants from exceeding their plan limits.

    Usage:
        class AgentViewSet(LicenseEnforcedViewSet, viewsets.ModelViewSet):
            license_limit_key = 'max_agents'

    License limits are defined in settings.LICENSE_TIERS and stored in Tenant.license_limits.
    Free tier example:
        - max_agents: 4
        - max_tools: 7
        - max_mcp_servers: 3
        - max_groups: 2
        - max_documents: 10
        - max_messages_per_month: 1000
        - max_storage_mb: 1024
    """

    license_limit_key = None  # Override in ViewSet (e.g., 'max_agents')

    def check_license_limit(self):
        """
        Check if tenant has reached license limit for this resource type.

        Raises:
            PermissionDenied: If limit is reached
        """
        if not self.license_limit_key:
            return  # No limit to check

        schema_name = connection.schema_name

        # Skip check for public schema
        if schema_name == 'public':
            return

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            raise PermissionDenied("Tenant not found")

        # Get current count of resources
        current_count = self.get_queryset().count()

        # Get limit from tenant license
        limit = tenant.get_limit(self.license_limit_key)

        # -1 means unlimited (pro/enterprise tiers)
        if limit == -1:
            return

        # Check if limit reached
        if current_count >= limit:
            resource_name = self.license_limit_key.replace('max_', '').replace('_', ' ').title()

            raise PermissionDenied(
                f"License limit reached: You have reached your plan's limit for {resource_name} "
                f"(maximum: {limit}, current: {current_count}). "
                f"Please upgrade your plan to create more {resource_name.lower()}."
            )

    def perform_create(self, serializer):
        """
        Override perform_create to add license check.

        This is called before creating a new resource.
        """
        self.check_license_limit()
        super().perform_create(serializer)


class PermissionFilteredViewSet:
    """
    Mixin to enforce fine-grained permissions from Permission model.

    Checks if user (or agent) has permission to perform actions on resources.

    Permission model fields:
        - subject: user OR agent (subject_type + subject_id)
        - resource: agent, tool, mcp_server, group, message, document (resource_type + resource_id)
        - actions: can_view, can_create, can_update, can_delete, can_execute

    Usage:
        class AgentViewSet(PermissionFilteredViewSet, LicenseEnforcedViewSet, viewsets.ModelViewSet):
            permission_resource_type = 'agent'

    Behavior:
        - Admins bypass permission checks (full access)
        - Regular users must have explicit permissions
        - View: requires can_view=True
        - Create: requires can_create=True (on resource_type, not specific resource)
        - Update: requires can_update=True (on specific resource or resource_type)
        - Delete: requires can_delete=True (on specific resource or resource_type)
        - Execute: requires can_execute=True (agents/tools only)
    """

    permission_resource_type = None  # Override in ViewSet (e.g., 'agent', 'tool')

    def _get_current_tenant(self):
        """Get current tenant from schema"""
        schema_name = connection.schema_name
        if schema_name == 'public':
            return None
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return None

    def _has_permission_for_action(self, user, resource_type, resource_id, action):
        """
        Check if user has permission for action on resource.

        Args:
            user: User object
            resource_type: 'agent', 'tool', 'mcp_server', 'group', 'message', 'document'
            resource_id: UUID of specific resource (or None for general permission)
            action: 'can_view', 'can_create', 'can_update', 'can_delete', 'can_execute'

        Returns:
            bool: True if user has permission
        """
        from .models import Permission

        # Admins bypass permission checks
        if hasattr(user, 'is_admin') and user.is_admin():
            return True

        tenant = self._get_current_tenant()
        if not tenant:
            return False

        # Check for specific resource permission first
        if resource_id:
            specific_perm = Permission.objects.filter(
                tenant=tenant,
                subject_type='user',
                subject_id=user.id,
                resource_type=resource_type,
                resource_id=resource_id
            ).first()

            if specific_perm and getattr(specific_perm, action, False):
                return True

        # Check for general resource type permission (resource_id=None)
        general_perm = Permission.objects.filter(
            tenant=tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=resource_type,
            resource_id__isnull=True
        ).first()

        if general_perm and getattr(general_perm, action, False):
            return True

        return False

    def check_permission_for_create(self, user):
        """Check if user can create this resource type"""
        if not self.permission_resource_type:
            return  # No permission enforcement

        has_perm = self._has_permission_for_action(
            user,
            self.permission_resource_type,
            None,  # General create permission
            'can_create'
        )

        if not has_perm:
            raise PermissionDenied(
                f"You do not have permission to create {self.permission_resource_type}s"
            )

    def check_permission_for_update(self, user, obj):
        """Check if user can update this specific resource"""
        if not self.permission_resource_type:
            return

        has_perm = self._has_permission_for_action(
            user,
            self.permission_resource_type,
            obj.id,
            'can_update'
        )

        if not has_perm:
            raise PermissionDenied(
                f"You do not have permission to update this {self.permission_resource_type}"
            )

    def check_permission_for_delete(self, user, obj):
        """Check if user can delete this specific resource"""
        if not self.permission_resource_type:
            return

        has_perm = self._has_permission_for_action(
            user,
            self.permission_resource_type,
            obj.id,
            'can_delete'
        )

        if not has_perm:
            raise PermissionDenied(
                f"You do not have permission to delete this {self.permission_resource_type}"
            )

    def _filter_queryset_by_permissions(self, queryset):
        """Apply permission filtering to queryset"""
        if not self.permission_resource_type:
            return queryset

        user = self.request.user

        # Admins see all
        if hasattr(user, 'is_admin') and user.is_admin():
            return queryset

        # Filter by can_view permission
        from .models import Permission

        tenant = self._get_current_tenant()
        if not tenant:
            return queryset.none()

        # Get all permissions for this user and resource type
        permissions = Permission.objects.filter(
            tenant=tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=self.permission_resource_type,
            can_view=True
        )

        # If user has general permission (resource_id=None), show all
        if permissions.filter(resource_id__isnull=True).exists():
            return queryset

        # Otherwise, filter by specific resource IDs
        allowed_ids = list(permissions.filter(
            resource_id__isnull=False
        ).values_list('resource_id', flat=True))

        if allowed_ids:
            return queryset.filter(id__in=allowed_ids)

        # No permissions = no access
        return queryset.none()

    def get_queryset(self):
        """Get base queryset and apply permission filtering"""
        # Get the base queryset (may include tenant filtering from child class)
        if hasattr(super(), 'get_queryset'):
            queryset = super().get_queryset()
        else:
            queryset = self.queryset if hasattr(self, 'queryset') and self.queryset is not None else self.model.objects.all()

        # Apply permission filtering on top
        return self._filter_queryset_by_permissions(queryset)

    def perform_create(self, serializer):
        """Check create permission before creating"""
        self.check_permission_for_create(self.request.user)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        """Check update permission before updating"""
        self.check_permission_for_update(self.request.user, serializer.instance)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        """Check delete permission before deleting"""
        self.check_permission_for_delete(self.request.user, instance)
        super().perform_destroy(instance)
