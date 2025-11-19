"""
Django Admin for Groups
"""

from django.contrib import admin
from .models import Group


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin interface for Group model"""

    list_display = (
        'name',
        'member_count',
        'agent_count',
        'is_active',
        'created_at',
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

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user if not set"""
        if not obj.created_by:
            obj.created_by = request.user.id
        super().save_model(request, obj, form, change)
