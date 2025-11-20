"""
Django Admin for MCP Servers
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import MCPServer


@admin.register(MCPServer)
class MCPServerAdmin(TenantFilteredAdmin):
    """Admin interface for MCP Server model - SECURITY: Tenant-filtered"""

    list_display = (
        'name',
        'get_tenant_display',
        'command',
        'is_active',
        'created_at',
        'updated_at',
    )

    def get_tenant_display(self, obj):
        """Display tenant with colored badge"""
        if not obj.tenant:
            return format_html('<span style="color: gray;">No tenant</span>')

        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.tenant.name
        )
    get_tenant_display.short_description = 'Tenant'
    get_tenant_display.admin_order_field = 'tenant'

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
