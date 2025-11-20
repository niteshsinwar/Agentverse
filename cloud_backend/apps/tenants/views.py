"""
Tenant Views
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_tenants.utils import get_tenant_model, get_public_schema_name
from django.db import connection

from .models import Tenant, TenantSettings
from .serializers import TenantSerializer, TenantSettingsSerializer


def get_current_tenant():
    """Get the current tenant from the request context"""
    if hasattr(connection, 'tenant'):
        return connection.tenant
    return None


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.

    Checks if user has 'admin' role in the current tenant.
    """

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has admin role
        return hasattr(request.user, 'role') and request.user.role == 'admin'


class TenantSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TenantSettings.

    PERMISSIONS:
    - Read (GET): All authenticated users in tenant
    - Create/Update/Delete: Admin users only

    REAL-TIME SYNC:
    - All changes broadcast to sync_{tenant_id} channel
    - All users in tenant receive settings updates immediately

    SCOPING:
    - Tenant-specific only (OneToOneField with Tenant)
    - Not group-specific
    """

    serializer_class = TenantSettingsSerializer

    def get_permissions(self):
        """
        Admin-only for write operations.
        All authenticated users can read.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Return settings for current tenant only.

        Each tenant has exactly one TenantSettings object (OneToOneField).
        """
        tenant = get_current_tenant()
        if not tenant:
            return TenantSettings.objects.none()

        return TenantSettings.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant when creating settings"""
        tenant = get_current_tenant()
        if not tenant:
            raise ValueError("No tenant context available")

        serializer.save(tenant=tenant)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get settings for current tenant.

        GET /api/v1/tenants/settings/current/

        Returns the TenantSettings for the current tenant.
        Creates default settings if none exist.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {'error': 'No tenant context'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create settings for this tenant
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)

        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAdminUser])
    def update_current(self, request):
        """
        Update settings for current tenant (admin-only).

        PATCH /api/v1/tenants/settings/update_current/

        Allows partial updates to tenant settings.
        Only admin users can modify settings.
        Changes are broadcast to all users in tenant.
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {'error': 'No tenant context'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create settings
        settings, created = TenantSettings.objects.get_or_create(tenant=tenant)

        # Partial update
        serializer = self.get_serializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Tenant information.

    Read-only for regular users.
    Only shows information about the current tenant.
    """

    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the current tenant"""
        tenant = get_current_tenant()
        if not tenant:
            return Tenant.objects.none()

        return Tenant.objects.filter(id=tenant.id)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get information about current tenant.

        GET /api/v1/tenants/current/
        """
        tenant = get_current_tenant()
        if not tenant:
            return Response(
                {'error': 'No tenant context'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(tenant)
        return Response(serializer.data)
