"""
User ViewSet - CRUD operations for users
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.permissions import IsAdminUser
from .models import User
from .serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations.

    Permissions:
    - List/Retrieve: Any authenticated user
    - Create/Update/Delete: Admin only
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'name']
    ordering_fields = ['created_at', 'name', 'email']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Use different serializer for create"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """Only admins can create, update, delete users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
