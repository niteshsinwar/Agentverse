"""
Django Admin for MCP Servers
"""

from django.contrib import admin
from .models import MCPServer


@admin.register(MCPServer)
class MCPServerAdmin(admin.ModelAdmin):
    """Admin interface for MCP Server model"""

    list_display = (
        'name',
        'command',
        'is_active',
        'created_at',
        'updated_at',
    )

    list_filter = (
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
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'is_active')
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

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user if not set"""
        if not obj.created_by:
            obj.created_by = request.user.id
        super().save_model(request, obj, form, change)
