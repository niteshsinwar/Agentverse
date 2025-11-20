from rest_framework import viewsets, permissions
from django.db import connection
from apps.core.mixins import PermissionFilteredViewSet, LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import Agent
from .serializers import AgentSerializer

class AgentViewSet(PermissionFilteredViewSet, LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for Agent CRUD operations.

    SECURITY:
    - Agents are tenant-isolated. Explicit filtering prevents cross-tenant access.
    - Permission enforcement: Users must have Permission to view/create/update/delete agents
    - License limits enforced: Free tier limited to 4 agents, Pro/Enterprise unlimited.
    """
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    license_limit_key = 'max_agents'  # Enforce license limit
    permission_resource_type = 'agent'  # Enforce permission model

    def get_queryset(self):
        """
        Filter agents by current tenant.

        PermissionFilteredViewSet mixin will further filter by user permissions.
        """
        schema_name = connection.schema_name

        # Prevent access from public schema
        if schema_name == 'public':
            return Agent.objects.none()

        # Get current tenant
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Agent.objects.none()

        # Return base queryset filtered by tenant
        # Permission mixin will apply additional filtering
        return Agent.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and creator on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
