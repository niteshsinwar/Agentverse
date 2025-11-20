from rest_framework import viewsets, permissions
from django.db import connection
from apps.core.mixins import PermissionFilteredViewSet, LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import Tool
from .serializers import ToolSerializer

class ToolViewSet(PermissionFilteredViewSet, LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for Tool CRUD operations.

    SECURITY:
    - Tools are tenant-isolated.
    - Permission enforcement: Users must have Permission to view/create/update/delete resources Explicit filtering prevents cross-tenant access.
    - License limits enforced: Free tier limited to 7 tools, Pro/Enterprise unlimited.
    """
    serializer_class = ToolSerializer
    permission_classes = [permissions.IsAuthenticated]
    license_limit_key = 'max_tools'  # Enforce license limit
    permission_resource_type = 'tool'  # Enforce permission model

    def get_queryset(self):
        """Filter tools by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Tool.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Tool.objects.none()

        return Tool.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and creator on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
