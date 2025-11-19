from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    """Document serializer with tenant_id for local backend sync"""
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'tenant_id', 'created_at', 'updated_at', 'uploaded_by', 'storage_path']

    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2)
