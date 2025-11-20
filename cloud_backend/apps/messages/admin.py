"""
Django Admin for Messages
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import Message


@admin.register(Message)
class MessageAdmin(TenantFilteredAdmin):
    """Admin interface for Message model - SECURITY: Tenant-filtered"""

    list_display = (
        'sender_type',
        'sender_id',
        'content_preview',
        'group',
        'get_tenant_display',
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
        'sender_type',
        'created_at',
    )

    search_fields = (
        'content',
        'sender_id',
    )

    readonly_fields = (
        'id',
        'tenant',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Message Info', {
            'fields': ('tenant', 'group', 'sender_type', 'sender_id', 'content')
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
    # Security handled by TenantFilteredAdmin mixin
