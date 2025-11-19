"""
Django Admin for Tools
"""

from django.contrib import admin
from .models import Tool


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    """Admin interface for Tool model"""

    list_display = (
        'name',
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

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user if not set"""
        if not obj.created_by:
            obj.created_by = request.user.id
        super().save_model(request, obj, form, change)
