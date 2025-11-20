from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from django.db import connection
from .models import UsageLog
from .serializers import UsageLogSerializer

class UsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UsageLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'action', 'resource_type']  # Removed 'tenant' from filters

    def get_queryset(self):
        """
        SECURITY: Filter usage logs by current user's tenant only.
        Prevents cross-tenant data leakage.
        """
        user = self.request.user

        # Get current tenant from connection (schema-based multi-tenancy)
        if hasattr(connection, 'tenant') and connection.tenant:
            tenant = connection.tenant
        elif hasattr(user, 'tenant') and user.tenant:
            tenant = user.tenant
        else:
            # No tenant context - return empty queryset
            return UsageLog.objects.none()

        # Filter by current user's tenant
        return UsageLog.objects.filter(tenant=tenant)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get usage statistics for current user's tenant.

        SECURITY: No longer accepts tenant_id from query params to prevent
        cross-tenant data access. Uses current user's tenant instead.
        """
        user = request.user

        # Get current tenant
        if hasattr(connection, 'tenant') and connection.tenant:
            tenant = connection.tenant
        elif hasattr(user, 'tenant') and user.tenant:
            tenant = user.tenant
        else:
            return Response(
                {'error': 'No tenant context available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Last 30 days stats for CURRENT TENANT only
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stats = UsageLog.objects.filter(
            tenant=tenant,  # Use current tenant, not from query params
            created_at__gte=thirty_days_ago
        ).values('action').annotate(count=Count('id'))

        return Response({'stats': list(stats), 'tenant_id': str(tenant.id)})
