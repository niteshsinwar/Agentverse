"""
User Models - Tenant-aware user management
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Custom user manager for tenant-aware users"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user"""
        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User model for multi-tenant system.

    Each user belongs to a tenant (via tenant schema).
    Users have roles: admin (can create/edit agents/tools) or user (can only use agents).
    """

    # Authentication
    email = models.EmailField(unique=True, help_text="User email (login)")
    password = models.CharField(max_length=128, help_text="Hashed password")

    # Profile
    name = models.CharField(max_length=255, help_text="Full name")
    avatar_url = models.URLField(blank=True, null=True)

    # Role
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('user', 'User'),
        ],
        default='user',
        help_text="User role within tenant"
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access

    # Metadata
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    @property
    def tenant(self):
        """Get current tenant from database connection"""
        from django.db import connection
        from apps.tenants.models import Tenant

        schema_name = connection.schema_name
        if schema_name == 'public':
            return None

        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return None
