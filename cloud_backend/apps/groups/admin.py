"""
Django Admin for Groups
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import Group


@admin.register(Group)
class GroupAdmin(TenantFilteredAdmin):
    """Admin interface for Group model - SECURITY: Tenant-filtered"""

    list_display = (
        'name',
        'get_tenant_display',
        'member_count',
        'agent_count',
        'is_active',
        'created_at',
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
        ('Members & Agents', {
            'fields': ('members', 'assigned_agents'),
            'description': 'List of user IDs and agent IDs'
        }),
        ('Metadata', {
            'fields': ('created_by', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    def member_count(self, obj):
        """Display member count"""
        return len(obj.members) if obj.members else 0
    member_count.short_description = 'Members'

    def agent_count(self, obj):
        """Display agent count"""
        return len(obj.assigned_agents) if obj.assigned_agents else 0
    agent_count.short_description = 'Agents'
    # Security handled by TenantFilteredAdmin mixin
