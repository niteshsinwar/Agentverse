from rest_framework import viewsets
from django.db import connection
from apps.core.permissions import IsAdminOrReadOnly
from apps.core.mixins import LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import Tool
from .serializers import ToolSerializer

class ToolViewSet(LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for Tool CRUD operations.

    SECURITY:
    - Tools are tenant-isolated. Explicit filtering prevents cross-tenant access.
    - License limits enforced: Free tier limited to 7 tools, Pro/Enterprise unlimited.
    """
    serializer_class = ToolSerializer
    permission_classes = [IsAdminOrReadOnly]
    license_limit_key = 'max_tools'  # Enforce license limit

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
