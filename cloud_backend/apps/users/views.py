"""
User ViewSet - CRUD operations for users
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import connection
from apps.core.permissions import IsAdminUser
from apps.tenants.models import Tenant, TenantMembership
from .models import User
from .serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations.

    Permissions:
    - List/Retrieve: Any authenticated user (within their tenant)
    - Create/Update/Delete: Admin only

    SECURITY: Users are filtered by TenantMembership to prevent cross-tenant data leaks.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'name']
    ordering_fields = ['created_at', 'name', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter users by current tenant membership.

        CRITICAL SECURITY FIX: Prevents cross-tenant data leakage.
        Users can only see other users within their tenant.
        """
        # Get current schema from django-tenants middleware
        schema_name = connection.schema_name

        # Public schema access (superadmin only)
        if schema_name == 'public':
            if self.request.user.is_superuser:
                return User.objects.all()
            return User.objects.none()

        # Get current tenant
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return User.objects.none()

        # Get user IDs who are members of this tenant
        user_ids = TenantMembership.objects.filter(
            tenant=tenant,
            is_active=True
        ).values_list('user_id', flat=True)

        # Return only users who are members of this tenant
        return User.objects.filter(id__in=user_ids)

    def get_serializer_class(self):
        """Use different serializer for create"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Only admins can create, update, delete users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
