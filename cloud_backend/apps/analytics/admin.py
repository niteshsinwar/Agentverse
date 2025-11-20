"""
Django Admin for Analytics & Usage Logs
"""

from django.contrib import admin
from apps.core.admin import TenantFilteredAdmin
from .models import UsageLog


@admin.register(UsageLog)
class UsageLogAdmin(TenantFilteredAdmin):
    """
    Admin interface for Usage Log model.

    SECURITY: Inherits from TenantFilteredAdmin to enforce tenant isolation.
    Admins can only view usage logs for their own tenant.
    """

    list_display = (
        'action',
        'resource_type',
        'tenant',
        'user',
        'created_at',
    )

    list_filter = (
        'action',
        'resource_type',
        'created_at',
    )

    search_fields = (
        'action',
        'tenant',
        'user',
        'resource_id',
    )

    readonly_fields = (
        'id',
        'tenant',
        'user',
        'action',
        'resource_type',
        'resource_id',
        'metadata',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Event Info', {
            'fields': ('action', 'resource_type', 'resource_id')
        }),
        ('User & Tenant', {
            'fields': ('tenant', 'user')
        }),
        ('Metadata', {
            'fields': ('metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 100

    def has_add_permission(self, request):
        """Disable manual creation of usage logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of usage logs"""
        return False
