"""
Django Admin for Documents
"""

from django.contrib import admin
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
        'tenant',
        'embeddings_indexed',
        'created_at',
    )

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
