"""
Tenant Models - Multi-tenancy foundation

Each tenant represents a separate organization/company using AgentVerse.
Tenants have their own:
- Database schema (data isolation)
- Users, groups, agents, tools, MCP servers
- License limits
- Storage quotas
- Billing information

Based on django-tenants for schema-based multi-tenancy.
"""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.conf import settings
import uuid


class Tenant(TenantMixin):
    """
    Tenant model - Each tenant gets its own database schema.

    Schema-based multi-tenancy ensures complete data isolation between tenants.

    Example:
        Tenant A: schema "tenant_acme_corp"
        Tenant B: schema "tenant_tech_startup"

    Each schema contains separate tables for users, agents, tools, etc.
    """

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant information
    name = models.CharField(max_length=255, help_text="Organization name")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-safe identifier")

    # Contact information (Admin/Point of Contact)
    email = models.EmailField(help_text="Primary admin contact email (visible to superadmin)")
    admin_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Name of primary admin/point of contact (visible to superadmin)"
    )
    phone = models.CharField(max_length=50, blank=True, null=True)

    # Company information (for superadmin analytics)
    company_size = models.CharField(
        max_length=20,
        choices=[
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('201-1000', '201-1000 employees'),
            ('1001+', '1001+ employees'),
        ],
        blank=True,
        null=True,
        help_text="Company size (for analytics)"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Industry/sector (for analytics)"
    )

    # License information
    license_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free Tier'),
            ('pro', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='free',
        help_text="Current license tier"
    )

    # License limits (JSON field for flexibility)
    license_limits = models.JSONField(
        default=dict,
        help_text="License limits based on tier",
        blank=True
    )

    # Subscription information
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('trialing', 'Trialing'),
            ('past_due', 'Past Due'),
            ('canceled', 'Canceled'),
            ('unpaid', 'Unpaid'),
        ],
        default='active'
    )
    subscription_current_period_end = models.DateTimeField(blank=True, null=True)

    # Usage tracking
    storage_used_mb = models.IntegerField(default=0, help_text="Storage used in MB")
    messages_this_month = models.IntegerField(default=0, help_text="Messages sent this billing period")
    last_usage_reset = models.DateTimeField(auto_now_add=True)

    # Status
    is_active = models.BooleanField(default=True, help_text="Tenant is active")
    is_trial = models.BooleanField(default=True, help_text="Tenant is in trial period")
    trial_end_date = models.DateTimeField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Auto-generated fields from TenantMixin
    # schema_name: Database schema name (auto-generated)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['license_type']),
            models.Index(fields=['subscription_status']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.license_type})"

    def save(self, *args, **kwargs):
        """Override save to set license limits based on tier"""
        if not self.license_limits:
            self.license_limits = settings.LICENSE_TIERS.get(
                self.license_type,
                settings.LICENSE_TIERS['free']
            )
        super().save(*args, **kwargs)

    def get_limit(self, limit_name):
        """Get a specific license limit"""
        return self.license_limits.get(limit_name, 0)

    def check_limit(self, limit_name, current_count=None):
        """
        Check if tenant has reached a limit.

        Args:
            limit_name: Name of the limit (e.g., 'max_users', 'max_agents')
            current_count: Current count (optional, will query if not provided)

        Returns:
            bool: True if under limit, False if limit reached
        """
        limit = self.get_limit(limit_name)

        # -1 means unlimited
        if limit == -1:
            return True

        # If current_count not provided, check based on limit_name
        # (This would need to be implemented based on actual model counts)
        if current_count is None:
            # TODO: Implement actual count queries
            return True

        return current_count < limit

    def is_within_storage_limit(self):
        """Check if tenant is within storage limit"""
        max_storage = self.get_limit('max_storage_mb')
        if max_storage == -1:
            return True
        return self.storage_used_mb < max_storage

    def is_within_message_limit(self):
        """Check if tenant is within monthly message limit"""
        max_messages = self.get_limit('max_messages_per_month')
        if max_messages == -1:
            return True
        return self.messages_this_month < max_messages

    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.messages_this_month = 0
        self.last_usage_reset = models.functions.Now()
        self.save(update_fields=['messages_this_month', 'last_usage_reset'])


class Domain(DomainMixin):
    """
    Domain model - Maps domains/subdomains to tenants.

    Each tenant can have multiple domains:
    - Primary domain: acme.agentverse.com
    - Custom domain: agents.acme.com

    The middleware uses the domain to identify which tenant's schema to use.
    """

    # Foreign key to tenant
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains'
    )

    # Auto-generated fields from DomainMixin:
    # domain: Domain name (e.g., "acme.agentverse.com")
    # is_primary: Whether this is the primary domain

    class Meta:
        ordering = ['-is_primary', 'domain']

    def __str__(self):
        return f"{self.domain} ({'primary' if self.is_primary else 'secondary'})"


class TenantSettings(models.Model):
    """
    Tenant-specific settings.

    Stores customizable settings for each tenant:
    - Branding (logo, colors)
    - Feature flags
    - Integrations
    - Notifications preferences
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # Branding
    logo_url = models.URLField(blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#6366f1')  # Hex color
    company_website = models.URLField(blank=True, null=True)

    # Feature flags
    features_enabled = models.JSONField(
        default=dict,
        help_text="Feature toggles for this tenant",
        blank=True
    )

    # Notification settings
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    weekly_reports = models.BooleanField(default=True)

    # Integration settings
    integrations = models.JSONField(
        default=dict,
        help_text="Third-party integration configurations",
        blank=True
    )

    # Custom settings (flexible JSON field)
    custom_settings = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.tenant.name}"


class TenantMembership(models.Model):
    """
    Tenant Membership - Links users to tenants.

    Since users are now shared across all tenants (in SHARED_APPS),
    this model tracks which tenants a user has access to and their role
    within each tenant.

    A user can belong to multiple tenants with different roles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_memberships'
    )

    role = models.CharField(
        max_length=20,
        choices=[
            ('owner', 'Owner'),
            ('admin', 'Admin'),
            ('user', 'User'),
            ('viewer', 'Viewer'),
        ],
        default='user',
        help_text="User's role within this tenant"
    )

    is_active = models.BooleanField(default=True, help_text="Membership is active")
    joined_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-joined_at']
        unique_together = [['tenant', 'user']]  # User can only have one role per tenant
        indexes = [
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"


class TenantInvitation(models.Model):
    """
    Tenant invitations - Invite users to join a tenant.

    When a new user is invited to a tenant, an invitation is created
    with a unique token. The user can accept the invitation to join.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    # Invitation details
    email = models.EmailField(help_text="Email to send invitation to")
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('user', 'User'),
        ],
        default='user'
    )

    # Token for accepting invitation
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('expired', 'Expired'),
            ('revoked', 'Revoked'),
        ],
        default='pending'
    )

    # Metadata
    invited_by = models.UUIDField(help_text="User ID who sent invitation")
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(help_text="Invitation expiry")

    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Invitation to {self.email} for {self.tenant.name}"

    def is_valid(self):
        """Check if invitation is still valid"""
        from django.utils import timezone
        return (
            self.status == 'pending' and
            self.expires_at > timezone.now()
        )
