from rest_framework import serializers
from .models import MCPServer

class MCPServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCPServer
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.id
        return super().create(validated_data)
