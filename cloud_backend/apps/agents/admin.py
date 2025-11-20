"""
Django Admin for Agents
"""

from django.contrib import admin
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
        'tenant',
        'is_active',
        'created_at',
        'updated_at',
    )

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
