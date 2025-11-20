from rest_framework import viewsets
from django.db import connection
from apps.core.permissions import IsAdminOrReadOnly
from apps.core.mixins import LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import Agent
from .serializers import AgentSerializer

class AgentViewSet(LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for Agent CRUD operations.

    SECURITY:
    - Agents are tenant-isolated. Explicit filtering prevents cross-tenant access.
    - License limits enforced: Free tier limited to 4 agents, Pro/Enterprise unlimited.
    """
    serializer_class = AgentSerializer
    permission_classes = [IsAdminOrReadOnly]
    license_limit_key = 'max_agents'  # Enforce license limit

    def get_queryset(self):
        """
        Filter agents by current tenant.

        Defense-in-depth: Explicit tenant filtering even though middleware handles schema isolation.
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

        # Filter by tenant (explicit check)
        return Agent.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and creator on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
