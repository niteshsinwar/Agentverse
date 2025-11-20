"""
Analytics Views

SECURITY ARCHITECTURE:
======================
This module contains TWO types of viewsets with DIFFERENT access controls:

1. TENANT-SCOPED (for tenant admins):
   - UsageLogViewSet: Tenant admins can view their own tenant's usage logs
   - Permission: IsAuthenticated
   - Filtering: Automatic tenant isolation via get_queryset()

2. SUPERADMIN-ONLY (for platform admins):
   - TenantStatsViewSet: View all tenants' aggregate statistics
   - GlobalPlatformStatsViewSet: View platform-wide metrics
   - SupportTicketViewSet: Manage support tickets
   - TenantOverviewViewSet: View tenant overview dashboard
   - Permission: IsSuperAdmin
   - Access: ONLY aggregate stats, NO tenant content

CRITICAL: Superadmin can see "how much" but NOT "what" (no messages, documents, etc.)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Max
from datetime import timedelta, date
from django.utils import timezone
from django.db import connection

from apps.core.permissions import IsSuperAdmin
from apps.tenants.models import Tenant

from .models import UsageLog, TenantStats, GlobalPlatformStats, SupportTicket
from .serializers import (
    UsageLogSerializer,
    TenantStatsSerializer,
    GlobalPlatformStatsSerializer,
    SupportTicketSerializer,
    TenantOverviewSerializer,
)


# ============================================================================
# TENANT-SCOPED VIEWSETS (for tenant admins)
# ============================================================================

class UsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Usage logs for current tenant.

    PERMISSION: Tenant admin/user (IsAuthenticated)
    SCOPE: Current tenant only (automatic filtering)
    ACCESS: Read-only

    Tenant admins can view usage logs for their own tenant to track
    activity and billing. Cannot see other tenants' logs.
    """

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
        return UsageLog.objects.filter(tenant=tenant.id)

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
            tenant=tenant.id,  # Use current tenant, not from query params
            created_at__gte=thirty_days_ago
        ).values('action').annotate(count=Count('id'))

        return Response({'stats': list(stats), 'tenant_id': str(tenant.id)})


# ============================================================================
# SUPERADMIN-ONLY VIEWSETS (for platform admins)
# ============================================================================

class TenantStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tenant statistics for superadmin analytics.

    PERMISSION: Superadmin ONLY (IsSuperAdmin)
    SCOPE: All tenants
    ACCESS: Read-only, aggregate stats only

    SUPERADMIN CAN SEE:
    - Daily counts (users, agents, messages, documents, etc.)
    - Storage usage metrics
    - Revenue estimates

    SUPERADMIN CANNOT SEE:
    - Actual message content
    - Document content
    - Agent configurations
    - User data
    """

    queryset = TenantStats.objects.all().select_related('tenant')
    serializer_class = TenantStatsSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'date']

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest stats for all tenants.

        Returns the most recent stats snapshot for each tenant.
        """
        # Get latest date for each tenant
        latest_stats = TenantStats.objects.filter(
            date=TenantStats.objects.filter(
                tenant=connection.tenant
            ).values('tenant').annotate(
                max_date=Max('date')
            ).values('max_date')
        ).select_related('tenant')

        serializer = self.get_serializer(latest_stats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary statistics across all tenants.

        Aggregates latest stats for quick dashboard view.
        """
        today = date.today()
        latest_stats = TenantStats.objects.filter(date=today)

        summary = {
            'date': today,
            'total_tenants': Tenant.objects.count(),
            'active_tenants_today': latest_stats.filter(active_users_today__gt=0).count(),
            'total_users': latest_stats.aggregate(total=Count('total_users'))['total'] or 0,
            'total_agents': latest_stats.aggregate(total=Count('total_agents'))['total'] or 0,
            'messages_today': latest_stats.aggregate(total=Count('messages_sent_today'))['total'] or 0,
            'total_storage_mb': latest_stats.aggregate(total=Count('storage_used_mb'))['total'] or 0,
        }

        return Response(summary)


class GlobalPlatformStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Global platform statistics for business reporting.

    PERMISSION: Superadmin ONLY (IsSuperAdmin)
    SCOPE: Platform-wide aggregate data
    ACCESS: Read-only

    USED FOR:
    - Marketing ("X active tenants, Y messages/day")
    - Business reporting (MRR, revenue, growth)
    - Executive dashboard

    CONTAINS:
    - Aggregate counts across all tenants
    - Revenue metrics
    - Growth metrics
    - Support metrics

    DOES NOT CONTAIN:
    - Any tenant-specific content
    """

    queryset = GlobalPlatformStats.objects.all()
    serializer_class = GlobalPlatformStatsSerializer
    permission_classes = [IsSuperAdmin]

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the most recent platform stats snapshot."""
        latest = GlobalPlatformStats.objects.order_by('-date').first()
        if not latest:
            return Response({'error': 'No stats available'}, status=404)

        serializer = self.get_serializer(latest)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get platform trends over time.

        Returns stats for last 30 days to show growth trends.
        """
        days = int(request.query_params.get('days', 30))
        start_date = date.today() - timedelta(days=days)

        stats = GlobalPlatformStats.objects.filter(
            date__gte=start_date
        ).order_by('date')

        serializer = self.get_serializer(stats, many=True)
        return Response(serializer.data)


class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    Support ticket management for superadmin.

    PERMISSION: Superadmin ONLY (IsSuperAdmin)
    SCOPE: All support tickets across all tenants
    ACCESS: Full CRUD (create, read, update, delete)

    SUPERADMIN CAN:
    - View all tickets
    - Update ticket status/priority
    - Assign tickets to team members
    - Add resolution notes
    - Close tickets

    CONTAINS:
    - Tenant contact info
    - Issue description
    - Priority and status

    DOES NOT CONTAIN:
    - Tenant data (messages, documents, etc.)
    """

    queryset = SupportTicket.objects.all().select_related('tenant')
    serializer_class = SupportTicketSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tenant', 'status', 'priority', 'category', 'assigned_to']

    @action(detail=False, methods=['get'])
    def open(self, request):
        """Get all open tickets."""
        open_tickets = self.queryset.filter(
            status__in=['open', 'in_progress', 'waiting_customer']
        ).order_by('-priority', 'created_at')

        serializer = self.get_serializer(open_tickets, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def critical(self, request):
        """Get all critical priority tickets."""
        critical_tickets = self.queryset.filter(
            priority='critical',
            status__in=['open', 'in_progress']
        ).order_by('created_at')

        serializer = self.get_serializer(critical_tickets, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to a team member."""
        ticket = self.get_object()
        assigned_to = request.data.get('assigned_to')

        if not assigned_to:
            return Response(
                {'error': 'assigned_to email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.assigned_to = assigned_to
        ticket.status = 'in_progress'
        ticket.save()

        serializer = self.get_serializer(ticket)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a ticket."""
        ticket = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')

        ticket.status = 'resolved'
        ticket.resolved_at = timezone.now()
        ticket.resolution_notes = resolution_notes
        ticket.save()

        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


class TenantOverviewViewSet(viewsets.ViewSet):
    """
    Tenant overview dashboard for superadmin.

    PERMISSION: Superadmin ONLY (IsSuperAdmin)
    SCOPE: All tenants with aggregated stats
    ACCESS: Read-only

    Provides a comprehensive overview of all tenants including:
    - Tenant metadata (name, contact, subscription)
    - Latest stats snapshot
    - Support ticket counts
    - Activity status

    PERFECT FOR:
    - Superadmin dashboard
    - Tenant health monitoring
    - Identifying at-risk tenants
    """

    permission_classes = [IsSuperAdmin]

    def list(self, request):
        """
        Get overview of all tenants.

        Returns tenant info + latest stats + ticket counts.
        """
        tenants = Tenant.objects.all().prefetch_related(
            'daily_stats',
            'support_tickets'
        )

        overview_data = []
        for tenant in tenants:
            # Get latest stats
            latest_stats = tenant.daily_stats.order_by('-date').first()

            # Count open and critical tickets
            open_tickets = tenant.support_tickets.filter(
                status__in=['open', 'in_progress', 'waiting_customer']
            ).count()

            critical_tickets = tenant.support_tickets.filter(
                priority='critical',
                status__in=['open', 'in_progress']
            ).count()

            # Get last activity date
            last_activity_at = tenant.updated_at

            overview_data.append({
                'id': tenant.id,
                'name': tenant.name,
                'slug': tenant.slug,
                'email': tenant.email,
                'admin_name': tenant.admin_name,
                'company_size': tenant.company_size,
                'industry': tenant.industry,
                'license_type': tenant.license_type,
                'subscription_status': tenant.subscription_status,
                'subscription_current_period_end': tenant.subscription_current_period_end,
                'is_trial': tenant.is_trial,
                'trial_end_date': tenant.trial_end_date,
                'storage_used_mb': tenant.storage_used_mb,
                'messages_this_month': tenant.messages_this_month,
                'latest_stats': TenantStatsSerializer(latest_stats).data if latest_stats else None,
                'open_tickets': open_tickets,
                'critical_tickets': critical_tickets,
                'is_active': tenant.is_active,
                'created_at': tenant.created_at,
                'last_activity_at': last_activity_at,
            })

        serializer = TenantOverviewSerializer(overview_data, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Get detailed overview for a specific tenant.
        """
        try:
            tenant = Tenant.objects.prefetch_related(
                'daily_stats',
                'support_tickets'
            ).get(pk=pk)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=404)

        # Get last 30 days of stats
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_stats = tenant.daily_stats.filter(
            date__gte=thirty_days_ago
        ).order_by('-date')

        # Get latest stats
        latest_stats = recent_stats.first()

        # Get support tickets
        open_tickets_list = tenant.support_tickets.filter(
            status__in=['open', 'in_progress', 'waiting_customer']
        ).order_by('-priority', 'created_at')

        data = {
            'id': tenant.id,
            'name': tenant.name,
            'slug': tenant.slug,
            'email': tenant.email,
            'admin_name': tenant.admin_name,
            'company_size': tenant.company_size,
            'industry': tenant.industry,
            'license_type': tenant.license_type,
            'subscription_status': tenant.subscription_status,
            'subscription_current_period_end': tenant.subscription_current_period_end,
            'is_trial': tenant.is_trial,
            'trial_end_date': tenant.trial_end_date,
            'storage_used_mb': tenant.storage_used_mb,
            'messages_this_month': tenant.messages_this_month,
            'latest_stats': TenantStatsSerializer(latest_stats).data if latest_stats else None,
            'recent_stats': TenantStatsSerializer(recent_stats, many=True).data,
            'open_tickets': open_tickets_list.count(),
            'critical_tickets': open_tickets_list.filter(priority='critical').count(),
            'open_tickets_list': SupportTicketSerializer(open_tickets_list[:5], many=True).data,
            'is_active': tenant.is_active,
            'created_at': tenant.created_at,
            'last_activity_at': tenant.updated_at,
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def at_risk(self, request):
        """
        Get tenants that might be at risk (for proactive support).

        Criteria for "at-risk":
        - Trial ending soon
        - No activity in last 7 days
        - Critical tickets open
        - Past due subscriptions
        """
        today = date.today()
        seven_days_from_now = today + timedelta(days=7)
        seven_days_ago = today - timedelta(days=7)

        at_risk_tenants = []

        for tenant in Tenant.objects.all():
            risk_reasons = []

            # Trial ending soon
            if tenant.is_trial and tenant.trial_end_date and tenant.trial_end_date <= seven_days_from_now:
                risk_reasons.append('Trial ending soon')

            # Past due subscription
            if tenant.subscription_status == 'past_due':
                risk_reasons.append('Payment past due')

            # Critical tickets
            critical_tickets = tenant.support_tickets.filter(
                priority='critical',
                status__in=['open', 'in_progress']
            ).count()
            if critical_tickets > 0:
                risk_reasons.append(f'{critical_tickets} critical tickets')

            # No recent activity
            latest_stats = tenant.daily_stats.order_by('-date').first()
            if latest_stats and latest_stats.date < seven_days_ago:
                risk_reasons.append('No activity in 7+ days')

            if risk_reasons:
                at_risk_tenants.append({
                    'id': tenant.id,
                    'name': tenant.name,
                    'email': tenant.email,
                    'admin_name': tenant.admin_name,
                    'risk_reasons': risk_reasons,
                    'license_type': tenant.license_type,
                    'subscription_status': tenant.subscription_status,
                })

        return Response(at_risk_tenants)
