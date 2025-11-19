"""
URL Configuration for AgentVerse Cloud Backend

Multi-tenant URL routing:
- Public URLs (authentication, landing page)
- Tenant-specific URLs (APIs for each tenant)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

# Public URLs (no tenant context required)
urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Health check
    path('health/', include('apps.core.urls')),

    # Authentication (public)
    path('api/v1/auth/', include('apps.users.urls_auth')),

    # Tenant management (super admin only)
    path('api/v1/tenants/', include('apps.tenants.urls')),
]

# Tenant-specific URLs (require tenant context)
tenant_patterns = [
    # Agents API
    path('api/v1/agents/', include('apps.agents.urls')),

    # Tools API
    path('api/v1/tools/', include('apps.tools.urls')),

    # MCP Servers API
    path('api/v1/mcp-servers/', include('apps.mcp.urls')),

    # Groups API
    path('api/v1/groups/', include('apps.groups.urls')),

    # Users API
    path('api/v1/users/', include('apps.users.urls')),

    # Messages API
    path('api/v1/messages/', include('apps.messages.urls')),

    # Documents API
    path('api/v1/documents/', include('apps.documents.urls')),

    # Analytics API
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

# Add tenant patterns to main URLs
urlpatterns += tenant_patterns

# Serve static/media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
