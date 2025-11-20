"""
Django Admin for Documents
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import Document


@admin.register(Document)
class DocumentAdmin(TenantFilteredAdmin):
    """Admin interface for Document model - SECURITY: Tenant-filtered"""

    list_display = (
        'filename',
        'file_type',
        'file_size_display',
        'group',
        'get_tenant_display',
        'embeddings_indexed',
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
        'file_type',
        'embeddings_indexed',
        'created_at',
    )

    search_fields = (
        'filename',
        'storage_path',
        'group',
    )

    readonly_fields = (
        'id',
        'tenant',
        'file_size_display',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Document Info', {
            'fields': ('tenant', 'filename', 'file_type', 'file_size_display', 'group')
        }),
        ('Storage', {
            'fields': ('storage_path',)
        }),
        ('Vector Embeddings', {
            'fields': ('embeddings_indexed', 'qdrant_collection')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'metadata', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size_bytes = obj.file_size

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    file_size_display.short_description = 'File Size'
    # Security handled by TenantFilteredAdmin mixin
