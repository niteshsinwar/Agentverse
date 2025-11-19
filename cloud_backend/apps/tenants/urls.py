"""
Tenants URLs - Tenant management (super admin only)
"""

from django.urls import path
from django.http import JsonResponse

def tenant_list(request):
    """Placeholder for tenant list - implement later"""
    return JsonResponse({'message': 'Tenant management - implement ViewSet'})

urlpatterns = [
    path('', tenant_list, name='tenant-list'),
]
