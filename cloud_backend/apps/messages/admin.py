"""
Django Admin for Messages
"""

from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model"""

    list_display = (
        'sender_type',
        'sender_id',
        'content_preview',
        'group',
        'created_at',
    )

    list_filter = (
        'sender_type',
        'created_at',
    )

    search_fields = (
        'content',
        'sender_id',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Message Info', {
            'fields': ('group', 'sender_type', 'sender_id', 'content')
        }),
        ('Metadata', {
            'fields': ('metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def content_preview(self, obj):
        """Display content preview"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'
