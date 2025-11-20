"""
Analytics URLs

Contains two types of routes:
1. Tenant-scoped: /api/v1/analytics/logs/ (for tenant admins)
2. Superadmin-only: /api/v1/analytics/admin/* (for superadmin only)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Tenant-scoped router (for tenant admins)
tenant_router = DefaultRouter()
tenant_router.register(r'logs', views.UsageLogViewSet, basename='usagelog')

# Superadmin-only router (for platform admins)
superadmin_router = DefaultRouter()
superadmin_router.register(r'tenant-stats', views.TenantStatsViewSet, basename='tenant-stats')
superadmin_router.register(r'platform-stats', views.GlobalPlatformStatsViewSet, basename='platform-stats')
superadmin_router.register(r'tickets', views.SupportTicketViewSet, basename='support-tickets')
superadmin_router.register(r'tenants', views.TenantOverviewViewSet, basename='tenant-overview')

urlpatterns = [
    # Tenant-scoped endpoints (regular users/admins)
    path('', include(tenant_router.urls)),

    # Superadmin-only endpoints (IsSuperAdmin permission required)
    # Accessible only on public schema by Django superusers
    path('admin/', include(superadmin_router.urls)),
]
