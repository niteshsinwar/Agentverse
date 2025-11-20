"""
Management command to create initial tenant data for development/testing.

Creates 2 tenants with users:
1. Acme Corp - 1 admin + 2 users
2. Bharat Tech Pvt Ltd - 1 admin + 2 users
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django_tenants.utils import schema_context
from apps.tenants.models import Tenant, Domain
from apps.users.models import User


class Command(BaseCommand):
    help = 'Create initial tenant data for development/testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip creation if tenants already exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating initial tenant data...\n'))

        # Tenant 1: Acme Corp
        tenant1_slug = 'acme-corp'
        if options['skip_existing'] and Tenant.objects.filter(slug=tenant1_slug).exists():
            self.stdout.write(self.style.WARNING(f'Tenant "{tenant1_slug}" already exists, skipping...'))
        else:
            tenant1 = self.create_tenant(
                name='acme corp',
                slug=tenant1_slug,
                email='contact@acmecorp.com',
                domain='acme.localhost',
                license_type='free'
            )
            self.create_users_for_tenant(
                tenant1,
                admin_email='admin@acmecorp.com',
                admin_name='Acme Admin',
                users=[
                    ('user1@acmecorp.com', 'Alice Johnson'),
                    ('user2@acmecorp.com', 'Bob Smith'),
                ]
            )

        # Tenant 2: Bharat Tech Pvt Ltd
        tenant2_slug = 'bharat-tech'
        if options['skip_existing'] and Tenant.objects.filter(slug=tenant2_slug).exists():
            self.stdout.write(self.style.WARNING(f'Tenant "{tenant2_slug}" already exists, skipping...'))
        else:
            tenant2 = self.create_tenant(
                name='bharat tech pvt ltd',
                slug=tenant2_slug,
                email='contact@bharattech.com',
                domain='bharat.localhost',
                license_type='free'
            )
            self.create_users_for_tenant(
                tenant2,
                admin_email='admin@bharattech.com',
                admin_name='Bharat Admin',
                users=[
                    ('user1@bharattech.com', 'Raj Kumar'),
                    ('user2@bharattech.com', 'Priya Sharma'),
                ]
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Initial tenant data created successfully!\n'))
        self.display_login_info()

    def create_tenant(self, name, slug, email, domain, license_type='free'):
        """Create a tenant with domain"""
        self.stdout.write(f'\n📦 Creating tenant: {name}')

        # Create tenant
        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            email=email,
            license_type=license_type,
            schema_name=f'tenant_{slug.replace("-", "_")}',
            is_active=True,
            is_trial=True,
        )

        # Create domain
        Domain.objects.create(
            domain=domain,
            tenant=tenant,
            is_primary=True
        )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Tenant created: {tenant.name}'))
        self.stdout.write(f'    - ID: {tenant.id}')
        self.stdout.write(f'    - Schema: {tenant.schema_name}')
        self.stdout.write(f'    - Domain: {domain}')

        return tenant

    def create_users_for_tenant(self, tenant, admin_email, admin_name, users):
        """Create users within a tenant's schema"""
        self.stdout.write(f'\n👥 Creating users for {tenant.name}:')

        # Switch to tenant schema
        with schema_context(tenant.schema_name):
            # Create admin user
            admin = User.objects.create_user(
                email=admin_email,
                name=admin_name,
                password='Admin@123456',  # Default password
                role='admin',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Admin: {admin.email} (password: Admin@123456)'))

            # Create regular users
            for email, name in users:
                user = User.objects.create_user(
                    email=email,
                    name=name,
                    password='User@123456',  # Default password
                    role='user',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ User: {user.email} (password: User@123456)'))

    def display_login_info(self):
        """Display login information for created tenants"""
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('LOGIN INFORMATION'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        tenants = Tenant.objects.filter(slug__in=['acme-corp', 'bharat-tech'])

        for tenant in tenants:
            self.stdout.write(f'\n🏢 {tenant.name.upper()}')
            self.stdout.write(f'   Tenant ID: {tenant.id}')
            self.stdout.write(f'   Domain: {tenant.domains.first().domain}')

            with schema_context(tenant.schema_name):
                users = User.objects.all().order_by('-role', 'email')
                self.stdout.write('\n   Users:')
                for user in users:
                    password = 'Admin@123456' if user.role == 'admin' else 'User@123456'
                    role_badge = '👑 Admin' if user.role == 'admin' else '👤 User'
                    self.stdout.write(f'     {role_badge} {user.email} / {password}')

        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('\n📝 To login, use these 3 fields:'))
        self.stdout.write('   - tenant_id: (shown above)')
        self.stdout.write('   - email: (shown above)')
        self.stdout.write('   - password: (shown above)\n')
