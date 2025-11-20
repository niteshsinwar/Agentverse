"""
ViewSet Mixins for Permission and License Enforcement

Provides permission-based access control and license limit enforcement for all resources.

Author: AgentVerse Team
"""

from rest_framework.exceptions import PermissionDenied
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
