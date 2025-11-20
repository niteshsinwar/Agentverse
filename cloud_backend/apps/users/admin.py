"""
Django Admin for Users - Tenant-aware user management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""

    list_display = (
        'email',
        'name',
        'role',
        'get_tenants',
        'is_active',
        'is_staff',
        'last_login_at',
        'created_at',
    )

    def get_tenants(self, obj):
        """Display all tenants the user belongs to"""
        from apps.tenants.models import TenantMembership
        memberships = TenantMembership.objects.filter(user=obj, is_active=True).select_related('tenant')

        if not memberships.exists():
            return format_html('<span style="color: gray;">No tenants</span>')

        tenant_badges = []
        for membership in memberships:
            color = '#28a745' if membership.role == 'admin' else '#007bff'
            tenant_badges.append(
                f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
                f'border-radius: 3px; margin-right: 5px; font-size: 11px;">'
                f'{membership.tenant.name} ({membership.role})</span>'
            )

        return format_html(''.join(tenant_badges))

    get_tenants.short_description = 'Tenant Memberships'

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
