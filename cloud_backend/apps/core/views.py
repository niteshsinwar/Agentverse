"""
Core ViewSets and Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db import connection
from django.http import HttpResponse
from apps.tenants.models import Tenant
from .models import Permission
from .serializers import PermissionSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def landing_page(request):
    """Landing page for AgentVerse Cloud"""
    return HttpResponse("""
        <html>
            <head><title>AgentVerse Cloud</title></head>
            <body style="font-family: sans-serif; padding: 50px; text-align: center;">
                <h1>🚀 AgentVerse Cloud Backend</h1>
                <p>Multi-tenant AI agent collaboration platform</p>
                <p><a href="/admin/">Admin Panel</a> | <a href="/health/">Health Check</a></p>
            </body>
        </html>
    """)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'service': 'agentverse-cloud',
        'database': 'connected'
    }, status=status.HTTP_200_OK)


class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Permission CRUD.

    Only admins can create/update/delete permissions.
    Users can view their own permissions.
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter permissions by tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Permission.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Permission.objects.none()

        queryset = Permission.objects.filter(tenant=tenant)

        # Non-admins can only see their own permissions
        if hasattr(self.request.user, 'is_admin') and not self.request.user.is_admin():
            queryset = queryset.filter(
                subject_type='user',
                subject_id=self.request.user.id
            )

        return queryset

    def perform_create(self, serializer):
        """Auto-set tenant and granted_by"""
        # Check if user is admin
        if hasattr(self.request.user, 'is_admin') and not self.request.user.is_admin():
            raise PermissionDenied("Only admins can create permissions")

        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            granted_by=self.request.user.id
        )

    def perform_update(self, serializer):
        """Check admin permission"""
        if hasattr(self.request.user, 'is_admin') and not self.request.user.is_admin():
            raise PermissionDenied("Only admins can update permissions")
        serializer.save()

    def perform_destroy(self, instance):
        """Check admin permission"""
        if hasattr(self.request.user, 'is_admin') and not self.request.user.is_admin():
            raise PermissionDenied("Only admins can delete permissions")
        instance.delete()
