from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    """
    Agent serializer with tenant_id for local backend synchronization.

    CRITICAL: tenant_id field is required for cloud-local sync architecture.
    """
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)

    class Meta:
        model = Agent
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'tenant_id', 'created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        # created_by and tenant are set by ViewSet.perform_create()
        return super().create(validated_data)
