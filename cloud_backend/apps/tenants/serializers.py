"""
Tenant Serializers
"""

from rest_framework import serializers
from .models import Tenant, TenantSettings


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'email',
            'phone',
            'license_type',
            'license_limits',
            'subscription_status',
            'storage_used_mb',
            'messages_this_month',
            'is_active',
            'is_trial',
            'trial_end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'storage_used_mb',
            'messages_this_month',
        ]


class TenantSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for TenantSettings model.

    Admin-only access for modifications.
    All tenant users can view settings.
    """

    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantSettings
        fields = [
            'id',
            'tenant_id',
            'tenant_name',
            'logo_url',
            'primary_color',
            'company_website',
            'features_enabled',
            'notifications_enabled',
            'email_notifications',
            'weekly_reports',
            'integrations',
            'custom_settings',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant_id',
            'tenant_name',
            'created_at',
            'updated_at',
        ]

    def validate_primary_color(self, value):
        """Validate hex color format"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("Color must be in hex format (e.g., #6366f1)")
        if value and len(value) != 7:
            raise serializers.ValidationError("Color must be 7 characters (#RRGGBB)")
        return value
