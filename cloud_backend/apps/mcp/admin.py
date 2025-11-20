"""
Django Admin for MCP Servers
"""

from django.contrib import admin
from apps.core.admin import TenantFilteredAdmin
from .models import MCPServer


@admin.register(MCPServer)
class MCPServerAdmin(TenantFilteredAdmin):
    """Admin interface for MCP Server model - SECURITY: Tenant-filtered"""

    list_display = (
        'name',
        'tenant',
        'command',
        'is_active',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'tenant',
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'command',
    )

    readonly_fields = (
        'id',
        'tenant',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('tenant', 'name', 'description', 'is_active')
        }),
        ('Command Configuration', {
            'fields': ('command', 'args', 'env'),
            'description': 'Command to run and its arguments/environment'
        }),
        ('Metadata', {
            'fields': ('created_by', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    # Security handled by TenantFilteredAdmin mixin
