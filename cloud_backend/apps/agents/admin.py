"""
Django Admin for Agents
"""

from django.contrib import admin
from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin interface for Agent model"""

    list_display = (
        'emoji',
        'name',
        'llm_provider',
        'llm_model',
        'is_active',
        'created_at',
        'updated_at',
    )

    list_filter = (
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
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'emoji', 'is_active')
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

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user if not set"""
        if not obj.created_by:
            obj.created_by = request.user.id
        super().save_model(request, obj, form, change)
