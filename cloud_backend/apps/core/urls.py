"""
Core App URLs - Health check and system status
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health-check'),
    path('status/', views.system_status, name='system-status'),
]
