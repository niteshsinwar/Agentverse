"""
Django Admin for Users - Tenant-aware user management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""

    list_display = (
        'email',
        'name',
        'role',
        'is_active',
        'is_staff',
        'last_login_at',
        'created_at',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
    )

    search_fields = (
        'email',
        'name',
    )

    readonly_fields = (
        'id',
        'last_login',
        'last_login_at',
        'last_login_ip',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Profile', {
            'fields': ('name', 'avatar_url')
        }),
        ('Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Login History', {
            'fields': ('last_login', 'last_login_at', 'last_login_ip'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'role'),
        }),
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 50

    # Use email as username field
    filter_horizontal = ('groups', 'user_permissions')
