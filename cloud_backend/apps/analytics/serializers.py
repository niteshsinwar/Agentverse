"""
Analytics Serializers

IMPORTANT: These serializers are safe for superadmin access.
They expose ONLY aggregated statistics and metadata, NO tenant content.
"""

from rest_framework import serializers
from .models import UsageLog, TenantStats, GlobalPlatformStats, SupportTicket


class UsageLogSerializer(serializers.ModelSerializer):
    """
    Usage log serializer.

    SUPERADMIN ACCESS: YES (read-only)
    Contains only action metadata, no sensitive content.
    """

    class Meta:
        model = UsageLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantStatsSerializer(serializers.ModelSerializer):
    """
    Tenant statistics serializer for superadmin analytics.

    SUPERADMIN ACCESS: YES (read-only)
    Shows aggregate counts and metrics per tenant, NO actual content.
    """

    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_email = serializers.EmailField(source='tenant.email', read_only=True)
    tenant_admin_name = serializers.CharField(source='tenant.admin_name', read_only=True)
    license_type = serializers.CharField(source='tenant.license_type', read_only=True)
    subscription_status = serializers.CharField(source='tenant.subscription_status', read_only=True)

    class Meta:
        model = TenantStats
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'tenant_email',
            'tenant_admin_name',
            'license_type',
            'subscription_status',
            'date',
            # User metrics (counts only)
            'total_users',
            'active_users_today',
            'new_users_today',
            # Agent metrics (counts only)
            'total_agents',
            'new_agents_today',
            # MCP/Tool metrics (counts only)
            'total_mcp_servers',
            'total_tools',
            # Group metrics (counts only)
            'total_groups',
            'active_groups_today',
            # Message metrics (counts only, NO content)
            'messages_sent_today',
            'total_messages',
            # Document metrics (counts only, NO content)
            'documents_uploaded_today',
            'total_documents',
            # Storage metrics (sizes only, NO content)
            'storage_used_mb',
            'storage_delta_mb',
            # API usage
            'api_calls_today',
            # Revenue
            'estimated_revenue_today',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GlobalPlatformStatsSerializer(serializers.ModelSerializer):
    """
    Global platform statistics serializer for business reporting.

    SUPERADMIN ACCESS: YES (read-only)
    Aggregate data across all tenants for marketing and reporting.
    """

    class Meta:
        model = GlobalPlatformStats
        fields = [
            'id',
            'date',
            # Tenant metrics
            'total_tenants',
            'active_tenants',
            'new_tenants_today',
            'paying_tenants',
            'trial_tenants',
            # User metrics (across all tenants)
            'total_users',
            'active_users_today',
            'new_users_today',
            # Resource metrics
            'total_agents',
            'total_groups',
            'total_mcp_servers',
            'total_tools',
            # Activity metrics
            'messages_today',
            'total_messages',
            'api_calls_today',
            # Storage metrics
            'total_storage_used_gb',
            # Revenue metrics
            'total_revenue_today',
            'monthly_recurring_revenue',
            # Support metrics
            'open_tickets',
            'tickets_created_today',
            'tickets_resolved_today',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    """
    Support ticket serializer.

    SUPERADMIN ACCESS: YES (read/write for ticket management)
    Contains tenant contact info and issue description, NO tenant data.
    """

    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_email = serializers.EmailField(source='tenant.email', read_only=True)
    tenant_license = serializers.CharField(source='tenant.license_type', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'tenant_email',
            'tenant_license',
            'subject',
            'description',
            'raised_by_email',
            'raised_by_name',
            'priority',
            'status',
            'category',
            'assigned_to',
            'resolved_at',
            'resolution_notes',
            'last_response_at',
            'response_time_hours',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'response_time_hours']


class TenantOverviewSerializer(serializers.Serializer):
    """
    Tenant overview serializer for superadmin dashboard.

    SUPERADMIN ACCESS: YES (read-only)
    Combines tenant metadata with latest stats, NO tenant content.
    """

    # Tenant info
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    email = serializers.EmailField()
    admin_name = serializers.CharField()
    company_size = serializers.CharField()
    industry = serializers.CharField()

    # Subscription info
    license_type = serializers.CharField()
    subscription_status = serializers.CharField()
    subscription_current_period_end = serializers.DateTimeField()
    is_trial = serializers.BooleanField()
    trial_end_date = serializers.DateTimeField()

    # Current usage (from Tenant model)
    storage_used_mb = serializers.IntegerField()
    messages_this_month = serializers.IntegerField()

    # Latest stats (from TenantStats)
    latest_stats = TenantStatsSerializer(allow_null=True)

    # Support ticket count
    open_tickets = serializers.IntegerField()
    critical_tickets = serializers.IntegerField()

    # Status
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    last_activity_at = serializers.DateTimeField()
