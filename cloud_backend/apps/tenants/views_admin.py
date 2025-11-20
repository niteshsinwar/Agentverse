"""
Tenant Management Views for Superadmin

SECURITY: These endpoints are ONLY accessible to superadmin.

Purpose:
- Create new tenants with initial admin user
- Manage tenant subscriptions
- Update tenant information

Architecture:
- Superadmin creates tenant + tenant admin (cloud backend)
- Tenant admin creates other users
- NO signup in local frontend (login only)
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth.hashers import make_password

from apps.core.permissions import IsSuperAdmin
from apps.users.models import User
from .models import Tenant, TenantMembership, Domain
from .serializers import TenantSerializer


class TenantManagementViewSet(viewsets.ModelViewSet):
    """
    Tenant management for superadmin.

    PERMISSION: Superadmin ONLY (IsSuperAdmin)
    SCOPE: All tenants
    ACCESS: Full CRUD

    ENDPOINTS:
    - GET /api/v1/tenants/admin/tenants/ - List all tenants
    - POST /api/v1/tenants/admin/tenants/ - Create tenant with admin user
    - PATCH /api/v1/tenants/admin/tenants/{id}/ - Update tenant
    - DELETE /api/v1/tenants/admin/tenants/{id}/ - Delete tenant

    TENANT CREATION FLOW:
    1. Superadmin calls POST /api/v1/tenants/admin/tenants/ with:
       - Tenant info (name, email, license_type, etc.)
       - Admin user info (admin_email, admin_password, admin_name)
    2. Backend creates:
       - Tenant record
       - Tenant schema (database)
       - Primary domain (subdomain)
       - Admin user
       - TenantMembership linking admin to tenant
    3. Tenant admin can now login and create other users
    """

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsSuperAdmin]

    @transaction.atomic
    def create(self, request):
        """
        Create a new tenant with initial admin user.

        Request Body:
        {
          "name": "Acme Corp",
          "slug": "acme",  # Optional, auto-generated from name
          "email": "admin@acme.com",  # Primary contact
          "admin_name": "John Doe",  # Admin user's name
          "admin_email": "john@acme.com",  # Admin user's login email
          "admin_password": "secure_password",  # Admin user's password
          "license_type": "pro",  # free/pro/enterprise
          "company_size": "51-200",  # Optional
          "industry": "Technology",  # Optional
          "phone": "+1234567890"  # Optional
        }

        Response:
        {
          "tenant": { ... },
          "admin_user": { ... },
          "domain": "acme.agentverse.com"
        }
        """
        # Extract tenant and admin data
        tenant_data = {
            'name': request.data.get('name'),
            'slug': request.data.get('slug'),
            'email': request.data.get('email'),
            'admin_name': request.data.get('admin_name'),
            'company_size': request.data.get('company_size'),
            'industry': request.data.get('industry'),
            'phone': request.data.get('phone'),
            'license_type': request.data.get('license_type', 'free'),
            'is_trial': request.data.get('is_trial', True),
        }

        admin_data = {
            'name': request.data.get('admin_name'),
            'email': request.data.get('admin_email'),
            'password': request.data.get('admin_password'),
        }

        # Validation
        if not tenant_data['name']:
            return Response(
                {'error': 'Tenant name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not admin_data['email'] or not admin_data['password']:
            return Response(
                {'error': 'Admin email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Auto-generate slug if not provided
        if not tenant_data['slug']:
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', tenant_data['name'].lower())
            slug = slug.strip('-')
            tenant_data['slug'] = slug

        # Auto-generate schema name
        schema_name = f"tenant_{tenant_data['slug']}"

        try:
            # Create tenant (this creates the schema automatically via TenantMixin)
            tenant = Tenant.objects.create(
                schema_name=schema_name,
                **tenant_data
            )

            # Create primary domain
            domain_name = f"{tenant_data['slug']}.agentverse.com"
            domain = Domain.objects.create(
                domain=domain_name,
                tenant=tenant,
                is_primary=True
            )

            # Switch to tenant schema to create admin user
            from django.db import connection as db_connection
            db_connection.set_tenant(tenant)

            # Create admin user in tenant schema
            admin_user = User.objects.create(
                email=admin_data['email'],
                name=admin_data['name'],
                password=make_password(admin_data['password']),
                role='admin',
                is_active=True,
            )

            # Create TenantMembership (in public schema)
            db_connection.set_schema_to_public()
            membership = TenantMembership.objects.create(
                tenant=tenant,
                user=admin_user,
                role='admin',
                is_active=True
            )

            # Return to public schema
            db_connection.set_schema_to_public()

            return Response({
                'tenant': TenantSerializer(tenant).data,
                'admin_user': {
                    'id': str(admin_user.id),
                    'email': admin_user.email,
                    'name': admin_user.name,
                    'role': admin_user.role,
                },
                'domain': domain_name,
                'message': 'Tenant and admin user created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to create tenant: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        Suspend a tenant (set is_active=False).

        This prevents users from logging in and accessing the tenant.
        """
        tenant = self.get_object()
        tenant.is_active = False
        tenant.subscription_status = 'canceled'
        tenant.save()

        return Response({
            'message': f'Tenant {tenant.name} has been suspended',
            'tenant_id': str(tenant.id),
            'is_active': tenant.is_active
        })

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a suspended tenant.
        """
        tenant = self.get_object()
        tenant.is_active = True
        tenant.subscription_status = 'active'
        tenant.save()

        return Response({
            'message': f'Tenant {tenant.name} has been activated',
            'tenant_id': str(tenant.id),
            'is_active': tenant.is_active
        })

    @action(detail=True, methods=['patch'])
    def update_subscription(self, request, pk=None):
        """
        Update tenant subscription.

        Request Body:
        {
          "license_type": "enterprise",
          "subscription_status": "active",
          "is_trial": false
        }
        """
        tenant = self.get_object()

        if 'license_type' in request.data:
            tenant.license_type = request.data['license_type']

        if 'subscription_status' in request.data:
            tenant.subscription_status = request.data['subscription_status']

        if 'is_trial' in request.data:
            tenant.is_trial = request.data['is_trial']

        tenant.save()

        return Response({
            'message': 'Subscription updated successfully',
            'tenant': TenantSerializer(tenant).data
        })
