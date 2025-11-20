"""
Tenants URLs - Tenant management and settings

Contains two types of routes:
1. Tenant-scoped: /api/v1/tenants/* (for tenant users)
2. Superadmin-only: /api/v1/tenants/admin/* (for superadmin)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantSettingsViewSet
from .views_admin import TenantManagementViewSet

# Tenant-scoped router (for regular users)
tenant_router = DefaultRouter()
tenant_router.register(r'info', TenantViewSet, basename='tenant')
tenant_router.register(r'settings', TenantSettingsViewSet, basename='tenant-settings')

# Superadmin router (for platform admins)
superadmin_router = DefaultRouter()
superadmin_router.register(r'tenants', TenantManagementViewSet, basename='tenant-management')

urlpatterns = [
    # Tenant-scoped endpoints
    path('', include(tenant_router.urls)),

    # Superadmin-only endpoints
    # POST /api/v1/tenants/admin/tenants/ - Create tenant with admin
    # PATCH /api/v1/tenants/admin/tenants/{id}/ - Update tenant
    # POST /api/v1/tenants/admin/tenants/{id}/suspend/ - Suspend tenant
    # POST /api/v1/tenants/admin/tenants/{id}/activate/ - Activate tenant
    path('admin/', include(superadmin_router.urls)),
]
