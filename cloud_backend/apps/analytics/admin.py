"""
Django Admin for Analytics & Usage Logs

SECURITY: Contains TWO types of admin classes:
1. TenantFilteredAdmin: For tenant-scoped data (UsageLog)
2. Regular ModelAdmin: For superadmin-only data (TenantStats, SupportTicket, etc.)

Superadmin-only models are NOT tenant-filtered because superadmin needs
to see data across all tenants for business analytics.
"""

from django.contrib import admin
from django.utils.html import format_html
from apps.core.admin import TenantFilteredAdmin
from .models import UsageLog, TenantStats, GlobalPlatformStats, SupportTicket


# ============================================================================
# TENANT-SCOPED ADMIN (filtered by tenant)
# ============================================================================

@admin.register(UsageLog)
class UsageLogAdmin(TenantFilteredAdmin):
    """
    Admin interface for Usage Log model.

    SECURITY: Inherits from TenantFilteredAdmin to enforce tenant isolation.
    Admins can only view usage logs for their own tenant.
    """

    list_display = (
        'action',
        'resource_type',
        'tenant',
        'user',
        'created_at',
    )

    list_filter = (
        'action',
        'resource_type',
        'created_at',
    )

    search_fields = (
        'action',
        'resource_type',
        'tenant',
        'user',
    )

    readonly_fields = (
        'id',
        'tenant',
        'user',
        'action',
        'resource_type',
        'resource_id',
        'metadata',
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # Limit to 100 entries per page for performance
    list_per_page = 100

    def has_add_permission(self, request):
        """Disable manual creation of usage logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing of usage logs"""
        return False


# ============================================================================
# SUPERADMIN-ONLY ADMIN (not tenant-filtered)
# ============================================================================

@admin.register(TenantStats)
class TenantStatsAdmin(admin.ModelAdmin):
    """
    Admin interface for Tenant Statistics.

    SUPERADMIN ONLY: Shows aggregate stats for all tenants.
    NOT tenant-filtered - superadmin can see all tenant stats.

    CONTAINS: Only counts and metrics, NO tenant content.
    """

    list_display = (
        'tenant_name',
        'date',
        'total_users',
        'active_users_today',
        'total_agents',
        'messages_sent_today',
        'storage_used_mb',
        'estimated_revenue_today',
    )

    list_filter = (
        'date',
        'tenant__license_type',
        'tenant__subscription_status',
    )

    search_fields = (
        'tenant__name',
        'tenant__email',
    )

    readonly_fields = (
        'id',
        'tenant',
        'date',
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'date'
    ordering = ('-date', 'tenant')

    list_per_page = 50

    def tenant_name(self, obj):
        """Display tenant name with link to tenant admin"""
        return obj.tenant.name
    tenant_name.short_description = 'Tenant'
    tenant_name.admin_order_field = 'tenant__name'

    def has_add_permission(self, request):
        """Stats are auto-generated, not manually created"""
        return False


@admin.register(GlobalPlatformStats)
class GlobalPlatformStatsAdmin(admin.ModelAdmin):
    """
    Admin interface for Global Platform Statistics.

    SUPERADMIN ONLY: Platform-wide aggregate metrics.
    Used for business reporting and marketing.

    CONTAINS: Aggregate data across ALL tenants.
    """

    list_display = (
        'date',
        'total_tenants',
        'active_tenants',
        'total_users',
        'messages_today',
        'monthly_recurring_revenue',
        'open_tickets',
    )

    list_filter = (
        'date',
    )

    readonly_fields = (
        'id',
        'date',
        'created_at',
        'updated_at',
    )

    date_hierarchy = 'date'
    ordering = ('-date',)

    list_per_page = 50

    def has_add_permission(self, request):
        """Stats are auto-generated, not manually created"""
        return False


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """
    Admin interface for Support Tickets.

    SUPERADMIN ONLY: Manage support tickets from all tenants.
    Allows ticket assignment, resolution, and tracking.

    CONTAINS: Tenant contact info and issue description.
    DOES NOT CONTAIN: Actual tenant data.
    """

    list_display = (
        'subject',
        'tenant_name_link',
        'status_badge',
        'priority_badge',
        'category',
        'assigned_to',
        'created_at',
    )

    list_filter = (
        'status',
        'priority',
        'category',
        'assigned_to',
        'created_at',
    )

    search_fields = (
        'subject',
        'description',
        'tenant__name',
        'tenant__email',
        'raised_by_email',
        'raised_by_name',
    )

    readonly_fields = (
        'id',
        'tenant',
        'raised_by_email',
        'raised_by_name',
        'created_at',
        'updated_at',
        'response_time_hours',
    )

    fieldsets = (
        ('Ticket Information', {
            'fields': (
                'id',
                'tenant',
                'subject',
                'description',
            )
        }),
        ('Contact Information', {
            'fields': (
                'raised_by_email',
                'raised_by_name',
            )
        }),
        ('Classification', {
            'fields': (
                'priority',
                'status',
                'category',
            )
        }),
        ('Assignment & Resolution', {
            'fields': (
                'assigned_to',
                'resolved_at',
                'resolution_notes',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'last_response_at',
                'response_time_hours',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'created_at'
    ordering = ('-priority', '-created_at')

    list_per_page = 50

    def tenant_name_link(self, obj):
        """Display tenant name with admin link and contact info"""
        return format_html(
            '<strong>{}</strong><br/>'
            '<small>📧 {}</small>',
            obj.tenant.name,
            obj.tenant.email
        )
    tenant_name_link.short_description = 'Tenant'
    tenant_name_link.admin_order_field = 'tenant__name'

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'open': '#dc3545',  # red
            'in_progress': '#ffc107',  # yellow
            'waiting_customer': '#17a2b8',  # cyan
            'resolved': '#28a745',  # green
            'closed': '#6c757d',  # gray
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def priority_badge(self, obj):
        """Display priority with color coding"""
        colors = {
            'critical': '#dc3545',  # red
            'high': '#fd7e14',  # orange
            'medium': '#ffc107',  # yellow
            'low': '#28a745',  # green
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.priority.upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'

    def save_model(self, request, obj, form, change):
        """Auto-update response time on first response"""
        if not obj.last_response_at and obj.status != 'open':
            obj.last_response_at = obj.updated_at
            if obj.created_at:
                time_diff = obj.updated_at - obj.created_at
                obj.response_time_hours = time_diff.total_seconds() / 3600

        super().save_model(request, obj, form, change)
