"""
Django Admin for Tools
"""

from django.contrib import admin
from apps.core.admin import TenantFilteredAdmin
from .models import Tool


@admin.register(Tool)
class ToolAdmin(TenantFilteredAdmin):
    """Admin interface for Tool model - SECURITY: Tenant-filtered"""

    list_display = (
        'name',
        'tenant',
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
        ('Code', {
            'fields': ('code', 'dependencies'),
            'classes': ('wide',)
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
