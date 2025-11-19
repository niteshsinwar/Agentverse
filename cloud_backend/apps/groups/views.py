from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from apps.tenants.models import Tenant
from .models import Group
from .serializers import GroupSerializer

class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Group CRUD operations.

    SECURITY: Groups are tenant-isolated. Explicit filtering prevents cross-tenant access.
    User confirmed: "group object also come under tenant"
    """
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter groups by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Group.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Group.objects.none()

        return Group.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and creator on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
