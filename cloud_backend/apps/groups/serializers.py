from rest_framework import serializers
from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    """Group serializer with tenant_id for local backend sync"""
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)
    member_count = serializers.SerializerMethodField()
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'tenant_id', 'created_at', 'updated_at', 'created_by']

    def get_member_count(self, obj):
        return len(obj.members)

    def get_agent_count(self, obj):
        return len(obj.assigned_agents)

    def create(self, validated_data):
        # tenant and created_by set by ViewSet.perform_create()
        return super().create(validated_data)
