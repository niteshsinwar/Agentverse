from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import connection
from apps.tenants.models import Tenant
from .models import Message
from .serializers import MessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message CRUD operations.

    SECURITY: Messages are tenant-isolated. Explicit filtering prevents cross-tenant access.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'sender_type', 'sender_id']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """Filter messages by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Message.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Message.objects.none()

        return Message.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(tenant=tenant)
