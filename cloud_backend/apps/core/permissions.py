"""
Custom Permissions for Multi-Tenant System
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission that only allows admin users to perform actions.

    Used for create, update, delete operations on agents, tools, MCP servers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows admins to edit, but everyone can read.

    Used for resources that normal users need to view but only admins can modify.
    """

    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions only for admins
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsTenantMember(permissions.BasePermission):
    """
    Permission that checks if user belongs to the current tenant.

    This is automatically handled by django-tenants middleware,
    but this permission provides explicit checking.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user's tenant matches request tenant
        from django.db import connection
        current_schema = connection.schema_name

        # Public schema is for super admin
        if current_schema == 'public':
            return request.user.is_superuser

        # User must belong to current tenant
        return request.user.tenant.schema_name == current_schema


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows owners to edit their own objects, or admins to edit anything.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Admin can edit anything
        if request.user.role == 'admin':
            return True

        # User can edit their own objects
        return obj.created_by == request.user.id
