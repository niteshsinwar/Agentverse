from rest_framework import viewsets, permissions
from django.db import connection
from apps.core.mixins import PermissionFilteredViewSet, LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import MCPServer
from .serializers import MCPServerSerializer

class MCPServerViewSet(PermissionFilteredViewSet, LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for MCP Server CRUD operations.

    SECURITY:
    - MCP servers are tenant-isolated. Explicit filtering prevents cross-tenant access.
    - License limits enforced: Free tier limited to 3 MCP servers, Pro/Enterprise unlimited.
    """
    serializer_class = MCPServerSerializer
    permission_classes = [permissions.IsAuthenticated]
    license_limit_key = 'max_mcp_servers'  # Enforce license limit
    permission_resource_type = 'mcp_server'  # Enforce permission model

    def get_queryset(self):
        """Filter MCP servers by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return MCPServer.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return MCPServer.objects.none()

        return MCPServer.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and creator on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
