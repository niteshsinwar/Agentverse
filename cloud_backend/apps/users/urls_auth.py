"""
Authentication URLs
"""

from django.urls import path
from . import views_auth

urlpatterns = [
    path('login', views_auth.login, name='auth-login'),
    path('logout', views_auth.logout, name='auth-logout'),
    path('refresh', views_auth.refresh_token, name='auth-refresh'),
    path('validate-token', views_auth.validate_token, name='auth-validate'),
    path('me', views_auth.me, name='auth-me'),
]
