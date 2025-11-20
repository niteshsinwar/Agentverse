"""
Core Serializers
"""

from rest_framework import serializers
from .models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Permission serializer for API.

    Admins use this to grant/revoke permissions for users and agents.
    """

    class Meta:
        model = Permission
        fields = [
            'id',
            'tenant',
            'subject_type',
            'subject_id',
            'resource_type',
            'resource_id',
            'can_view',
            'can_create',
            'can_update',
            'can_delete',
            'can_execute',
            'granted_by',
            'reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'granted_by', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate permission data"""
        # Only admins can create permissions
        request = self.context.get('request')
        if request and hasattr(request.user, 'is_admin'):
            if not request.user.is_admin():
                raise serializers.ValidationError(
                    "Only admins can create/modify permissions"
                )

        return data
