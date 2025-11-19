from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from .models import UsageLog
from .serializers import UsageLogSerializer

class UsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsageLog.objects.all()
    serializer_class = UsageLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'user', 'action', 'resource_type']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        tenant_id = request.query_params.get('tenant')
        if not tenant_id:
            return Response({'error': 'tenant parameter required'}, status=400)

        # Last 30 days stats
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stats = UsageLog.objects.filter(
            tenant=tenant_id,
            created_at__gte=thirty_days_ago
        ).values('action').annotate(count=Count('id'))

        return Response({'stats': list(stats)})
