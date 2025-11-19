from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    """Message serializer with tenant_id for local backend sync"""
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'tenant_id', 'created_at', 'updated_at']
