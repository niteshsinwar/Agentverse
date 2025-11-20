"""
Tenants URLs - Tenant management and settings
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantSettingsViewSet

router = DefaultRouter()
router.register(r'info', TenantViewSet, basename='tenant')
router.register(r'settings', TenantSettingsViewSet, basename='tenant-settings')

urlpatterns = [
    path('', include(router.urls)),
]
