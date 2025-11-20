"""
Django Admin for Tenants - Multi-tenancy Management
"""

from django.contrib import admin
from .models import Tenant, Domain, TenantSettings, TenantMembership, TenantInvitation


class DomainInline(admin.TabularInline):
    """Inline admin for domains"""
    model = Domain
    extra = 1
    fields = ('domain', 'is_primary')


class TenantSettingsInline(admin.StackedInline):
    """Inline admin for tenant settings"""
    model = TenantSettings
    can_delete = False
    fields = (
        'logo_url',
        'primary_color',
        'company_website',
        'notifications_enabled',
        'email_notifications',
        'weekly_reports',
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model - Multi-tenant management"""

    list_display = (
        'name',
        'slug',
        'get_user_count',
        'license_type',
        'subscription_status',
        'is_active',
        'is_trial',
        'storage_usage',
        'created_at',
    )

    def get_user_count(self, obj):
        """Display number of users in this tenant"""
        from django.utils.html import format_html
        count = obj.memberships.filter(is_active=True).count()

        if count == 0:
            return format_html('<span style="color: gray;">0 users</span>')

        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{} users</span>',
            count
        )
    get_user_count.short_description = 'Users'
    get_user_count.admin_order_field = 'memberships__count'

    list_filter = (
        'license_type',
        'subscription_status',
        'is_active',
        'is_trial',
        'created_at',
    )

    search_fields = (
        'name',
        'slug',
        'email',
        'schema_name',
    )

    readonly_fields = (
        'id',
        'schema_name',
        'created_at',
        'updated_at',
        'storage_usage',
        'message_usage',
    )

    fieldsets = (
        ('Organization Info', {
            'fields': ('name', 'slug', 'email', 'phone')
        }),
        ('Schema', {
            'fields': ('schema_name',),
            'classes': ('collapse',),
            'description': 'Database schema for this tenant (auto-generated)'
        }),
        ('License & Subscription', {
            'fields': (
                'license_type',
                'license_limits',
                'subscription_status',
                'stripe_customer_id',
                'stripe_subscription_id',
                'subscription_current_period_end',
            )
        }),
        ('Usage & Limits', {
            'fields': (
                'storage_usage',
                'message_usage',
                'last_usage_reset',
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_trial',
                'trial_end_date',
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [DomainInline, TenantSettingsInline]
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    def storage_usage(self, obj):
        """Display storage usage"""
        max_storage = obj.get_limit('max_storage_mb')
        if max_storage == -1:
            return f"{obj.storage_used_mb} MB (unlimited)"
        percentage = (obj.storage_used_mb / max_storage * 100) if max_storage > 0 else 0
        return f"{obj.storage_used_mb} MB / {max_storage} MB ({percentage:.1f}%)"
    storage_usage.short_description = 'Storage Usage'

    def message_usage(self, obj):
        """Display message usage"""
        max_messages = obj.get_limit('max_messages_per_month')
        if max_messages == -1:
            return f"{obj.messages_this_month} (unlimited)"
        percentage = (obj.messages_this_month / max_messages * 100) if max_messages > 0 else 0
        return f"{obj.messages_this_month} / {max_messages} ({percentage:.1f}%)"
    message_usage.short_description = 'Message Usage (This Month)'

    actions = ['reset_monthly_usage', 'activate_tenants', 'deactivate_tenants']

    def reset_monthly_usage(self, request, queryset):
        """Reset monthly usage for selected tenants"""
        for tenant in queryset:
            tenant.reset_monthly_usage()
        self.message_user(request, f"Reset monthly usage for {queryset.count()} tenants")
    reset_monthly_usage.short_description = "Reset monthly usage"

    def activate_tenants(self, request, queryset):
        """Activate selected tenants"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} tenants")
    activate_tenants.short_description = "Activate selected tenants"

    def deactivate_tenants(self, request, queryset):
        """Deactivate selected tenants"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} tenants")
    deactivate_tenants.short_description = "Deactivate selected tenants"


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model"""

    list_display = (
        'domain',
        'tenant',
        'is_primary',
    )

    list_filter = (
        'is_primary',
    )

    search_fields = (
        'domain',
        'tenant__name',
    )

    ordering = ('domain',)


@admin.register(TenantSettings)
class TenantSettingsAdmin(admin.ModelAdmin):
    """Admin interface for Tenant Settings"""

    list_display = (
        'tenant',
        'notifications_enabled',
        'email_notifications',
        'weekly_reports',
    )

    list_filter = (
        'notifications_enabled',
        'email_notifications',
        'weekly_reports',
    )

    search_fields = (
        'tenant__name',
    )

    fieldsets = (
        ('Tenant', {
            'fields': ('tenant',)
        }),
        ('Branding', {
            'fields': ('logo_url', 'primary_color', 'company_website')
        }),
        ('Notifications', {
            'fields': ('notifications_enabled', 'email_notifications', 'weekly_reports')
        }),
        ('Features', {
            'fields': ('features_enabled',),
            'classes': ('collapse',)
        }),
        ('Integrations', {
            'fields': ('integrations',),
            'classes': ('collapse',)
        }),
        ('Custom Settings', {
            'fields': ('custom_settings',),
            'classes': ('collapse',)
        }),
    )


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    """Admin interface for Tenant Memberships"""

    list_display = (
        'user',
        'tenant',
        'role',
        'is_active',
        'joined_at',
        'last_accessed_at',
    )

    list_filter = (
        'role',
        'is_active',
        'joined_at',
    )

    search_fields = (
        'user__email',
        'user__name',
        'tenant__name',
    )

    readonly_fields = (
        'id',
        'joined_at',
        'last_accessed_at',
    )

    fieldsets = (
        ('Membership', {
            'fields': ('tenant', 'user', 'role', 'is_active')
        }),
        ('Metadata', {
            'fields': ('id', 'joined_at', 'last_accessed_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-joined_at',)
    date_hierarchy = 'joined_at'
    list_per_page = 50

    actions = ['activate_memberships', 'deactivate_memberships']

    def activate_memberships(self, request, queryset):
        """Activate selected memberships"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} memberships")
    activate_memberships.short_description = "Activate selected memberships"

    def deactivate_memberships(self, request, queryset):
        """Deactivate selected memberships"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} memberships")
    deactivate_memberships.short_description = "Deactivate selected memberships"


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    """Admin interface for Tenant Invitations"""

    list_display = (
        'email',
        'tenant',
        'role',
        'status',
        'sent_at',
        'expires_at',
    )

    list_filter = (
        'status',
        'role',
        'sent_at',
    )

    search_fields = (
        'email',
        'tenant__name',
    )

    readonly_fields = (
        'id',
        'token',
        'sent_at',
        'accepted_at',
    )

    fieldsets = (
        ('Invitation Details', {
            'fields': ('tenant', 'email', 'role')
        }),
        ('Status', {
            'fields': ('status', 'token')
        }),
        ('Metadata', {
            'fields': ('invited_by', 'sent_at', 'accepted_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    ordering = ('-sent_at',)
    date_hierarchy = 'sent_at'
    list_per_page = 50

    actions = ['revoke_invitations']

    def revoke_invitations(self, request, queryset):
        """Revoke selected invitations"""
        count = queryset.filter(status='pending').update(status='revoked')
        self.message_user(request, f"Revoked {count} invitations")
    revoke_invitations.short_description = "Revoke selected invitations"
