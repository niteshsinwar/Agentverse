from rest_framework import serializers
from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_member_count(self, obj):
        return len(obj.members)

    def get_agent_count(self, obj):
        return len(obj.assigned_agents)

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.id
        return super().create(validated_data)
