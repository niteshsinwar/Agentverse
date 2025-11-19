"""
Django Admin for Documents
"""

from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""

    list_display = (
        'filename',
        'file_type',
        'file_size_display',
        'group',
        'embeddings_indexed',
        'created_at',
    )

    list_filter = (
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
        'file_size_display',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Document Info', {
            'fields': ('filename', 'file_type', 'file_size_display', 'group')
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
