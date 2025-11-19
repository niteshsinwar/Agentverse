"""
Django Admin for Agents
"""

from django.contrib import admin
from django.db import connection
from apps.tenants.models import Tenant
from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
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

    def get_queryset(self, request):
        """
        Filter agents by current tenant.

        CRITICAL SECURITY FIX: Prevents viewing/editing cross-tenant data.
        """
        qs = super().get_queryset(request)
        schema_name = connection.schema_name

        # Superadmin in public schema can see all
        if schema_name == 'public' and request.user.is_superuser:
            return qs

        # Filter by current tenant
        if schema_name != 'public':
            try:
                tenant = Tenant.objects.get(schema_name=schema_name)
                return qs.filter(tenant=tenant)
            except Tenant.DoesNotExist:
                return qs.none()

        return qs.none()

    def save_model(self, request, obj, form, change):
        """Auto-set tenant and created_by on create"""
        if not change:  # Creating new object
            schema_name = connection.schema_name
            if schema_name != 'public':
                tenant = Tenant.objects.get(schema_name=schema_name)
                obj.tenant = tenant
            if not obj.created_by:
                obj.created_by = request.user.id
        super().save_model(request, obj, form, change)
