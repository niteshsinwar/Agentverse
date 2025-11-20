"""
Authentication Views - JWT login, logout, refresh, validate
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.utils import timezone
from apps.tenants.models import Tenant
from .models import User
from .serializers import LoginSerializer, TokenSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint - Returns JWT tokens.

    POST /api/v1/auth/login
    Body: {
        "tenant_id": "uuid",
        "email": "user@example.com",
        "password": "password123"
    }

    Returns:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 900,
            "user": {...},
            "tenant_id": "uuid",
            "user_role": "admin"
        }
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    tenant_id = serializer.validated_data['tenant_id']
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    # Verify tenant exists
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return Response(
            {'error': 'Invalid tenant'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Get user by email (users are in SHARED_APPS, not tenant-specific)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check password
    if not user.check_password(password):
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Verify user has access to this tenant via TenantMembership
    from apps.tenants.models import TenantMembership
    try:
        membership = TenantMembership.objects.get(
            user=user,
            tenant=tenant,
            is_active=True
        )
        # Update user's role from membership (tenant-specific role)
        user_role = membership.role
    except TenantMembership.DoesNotExist:
        return Response(
            {'error': 'User does not have access to this tenant'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    # Add tenant_id to JWT claims for multi-tenant support
    refresh['tenant_id'] = str(tenant.id)
    refresh['user_role'] = user_role

    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Update last login
    user.last_login_at = timezone.now()
    user.last_login_ip = get_client_ip(request)
    user.save(update_fields=['last_login_at', 'last_login_ip'])

    # Prepare response
    response_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900,  # 15 minutes (from settings.SIMPLE_JWT)
        'user': UserSerializer(user).data,
        'tenant_id': str(tenant.id),
        'user_role': user_role,  # Use role from TenantMembership (tenant-specific)
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint - Blacklists refresh token.

    POST /api/v1/auth/logout
    Headers: Authorization: Bearer <access_token>
    Body: {"refresh_token": "eyJ..."}

    Returns:
        {"message": "Logged out successfully"}
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken(refresh_token)
        token.blacklist()  # Requires BLACKLIST_AFTER_ROTATION = True in settings

        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )
    except TokenError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token.

    POST /api/v1/auth/refresh
    Body: {"refresh_token": "eyJ..."}

    Returns:
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",  # New refresh token if rotation enabled
            "token_type": "Bearer",
            "expires_in": 900
        }
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)

        response_data = {
            'access_token': access_token,
            'refresh_token': str(refresh),  # New refresh token (rotated)
            'token_type': 'Bearer',
            'expires_in': 900,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except TokenError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_token(request):
    """
    Validate access token and return user info.

    POST /api/v1/auth/validate-token
    Headers: Authorization: Bearer <access_token>

    Returns:
        {
            "valid": true,
            "user": {...},
            "tenant_id": "uuid",
            "user_role": "admin"
        }
    """
    user = request.user
    tenant = user.tenant

    return Response({
        'valid': True,
        'user': UserSerializer(user).data,
        'tenant_id': str(tenant.id) if tenant else None,
        'user_role': user.role,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get current user info.

    GET /api/v1/auth/me
    Headers: Authorization: Bearer <access_token>

    Returns:
        {
            "id": "uuid",
            "email": "user@example.com",
            "name": "John Doe",
            "role": "admin",
            "tenant_id": "uuid",
            "tenant_name": "Acme Corp"
        }
    """
    user = request.user
    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
