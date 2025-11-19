"""
User Serializers
"""

from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'avatar_url', 'role',
            'is_active', 'tenant_id', 'tenant_name',
            'last_login_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login_at']

    def get_tenant_id(self, obj):
        """Get tenant ID"""
        tenant = obj.tenant
        return str(tenant.id) if tenant else None

    def get_tenant_name(self, obj):
        """Get tenant name"""
        tenant = obj.tenant
        return tenant.name if tenant else None


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""

    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password_confirm', 'role', 'avatar_url']

    def validate(self, data):
        """Validate passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login request"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenSerializer(serializers.Serializer):
    """Serializer for token response"""

    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()  # seconds
    user = UserSerializer()
    tenant_id = serializers.UUIDField()
    user_role = serializers.CharField()
