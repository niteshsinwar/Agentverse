from rest_framework import serializers
from .models import MCPServer

class MCPServerSerializer(serializers.ModelSerializer):
    """MCP Server serializer with tenant_id for local backend sync"""
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)

    class Meta:
        model = MCPServer
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'tenant_id', 'created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        # tenant and created_by set by ViewSet.perform_create()
        return super().create(validated_data)
