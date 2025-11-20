from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import connection
from apps.core.mixins import LicenseEnforcedViewSet
from apps.tenants.models import Tenant
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(LicenseEnforcedViewSet, viewsets.ModelViewSet):
    """
    ViewSet for Document CRUD operations.

    SECURITY:
    - Documents are tenant-isolated. Explicit filtering prevents cross-tenant access.
    - License limits enforced: Free tier limited to 10 documents, Pro limited to 1000, Enterprise unlimited.
    """
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'uploaded_by', 'file_type']
    license_limit_key = 'max_documents'  # Enforce license limit

    def get_queryset(self):
        """Filter documents by current tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Document.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Document.objects.none()

        return Document.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant and uploader on create"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            uploaded_by=self.request.user.id
        )

    @action(detail=False, methods=['post'])
    def upload(self, request):
        # TODO: Implement MinIO/S3 upload
        return Response({'message': 'Upload endpoint - implement MinIO integration'}, status=status.HTTP_501_NOT_IMPLEMENTED)
