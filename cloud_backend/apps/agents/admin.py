"""
Django Admin for Agents
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(TenantFilteredAdmin):
    """
    Admin interface for Agent model

    SECURITY: Tenant-filtered to prevent cross-tenant data access
    """

    list_display = (
        'emoji',
        'name',
        'llm_provider',
        'llm_model',
        'get_tenant_display',
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
        'llm_provider',
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'llm_model',
    )

    readonly_fields = (
        'id',
        'tenant',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('tenant', 'name', 'description', 'emoji', 'is_active')
        }),
        ('LLM Configuration', {
            'fields': ('llm_provider', 'llm_model', 'system_prompt', 'config')
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
