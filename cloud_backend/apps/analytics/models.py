"""
Analytics Models - Usage tracking and tenant statistics

IMPORTANT: These models store ONLY aggregated statistics and metadata.
Superadmin can access these models to see business metrics but CANNOT
access actual tenant content (messages, documents, etc.).
"""

from django.db import models
from apps.core.models import TimeStampedModel
import uuid


class UsageLog(TimeStampedModel):
    """
    Usage log entries for audit trail.

    Tracks individual actions but stores NO sensitive content.
    Used for billing, analytics, and debugging.
    """
    tenant = models.UUIDField(help_text="Tenant ID")
    user = models.UUIDField(help_text="User ID", blank=True, null=True)
    action = models.CharField(max_length=100, help_text="Action type (e.g., 'message_sent', 'agent_created')")
    resource_type = models.CharField(max_length=50, help_text="Resource type (e.g., 'agent', 'message')", blank=True, null=True)
    resource_id = models.UUIDField(help_text="Resource ID", blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional metadata (NO sensitive content)")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.action} at {self.created_at}"


class TenantStats(TimeStampedModel):
    """
    Daily aggregated statistics per tenant.

    SUPERADMIN ACCESS: YES - Contains only counts and metrics, NO content.
    This model stores aggregate data that superadmin can use for:
    - Business analytics
    - Resource planning
    - Market reporting

    Does NOT contain any tenant-created content (messages, documents, etc.)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='daily_stats',
        help_text="Tenant these stats belong to"
    )

    # Date for this stats snapshot
    date = models.DateField(help_text="Date of this stats snapshot", db_index=True)

    # User metrics (counts only, no user data)
    total_users = models.IntegerField(default=0, help_text="Total users in tenant")
    active_users_today = models.IntegerField(default=0, help_text="Users who logged in today")
    new_users_today = models.IntegerField(default=0, help_text="Users created today")

    # Agent metrics (counts only, no agent configurations)
    total_agents = models.IntegerField(default=0, help_text="Total agents created")
    new_agents_today = models.IntegerField(default=0, help_text="Agents created today")

    # MCP/Tool metrics (counts only, no configurations)
    total_mcp_servers = models.IntegerField(default=0, help_text="Total MCP servers")
    total_tools = models.IntegerField(default=0, help_text="Total tools")

    # Group metrics (counts only, no group data)
    total_groups = models.IntegerField(default=0, help_text="Total groups")
    active_groups_today = models.IntegerField(default=0, help_text="Groups with activity today")

    # Message metrics (counts only, NO message content)
    messages_sent_today = models.IntegerField(default=0, help_text="Messages sent today")
    total_messages = models.IntegerField(default=0, help_text="Total messages (cumulative)")

    # Document metrics (counts only, NO document content)
    documents_uploaded_today = models.IntegerField(default=0, help_text="Documents uploaded today")
    total_documents = models.IntegerField(default=0, help_text="Total documents")

    # Storage metrics (sizes only, NO content)
    storage_used_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Storage used in MB"
    )
    storage_delta_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Storage change today (MB)"
    )

    # API usage metrics (counts only)
    api_calls_today = models.IntegerField(default=0, help_text="Total API calls today")

    # Revenue metrics (if applicable)
    estimated_revenue_today = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Estimated revenue for today (based on usage)"
    )

    class Meta:
        ordering = ['-date', 'tenant']
        unique_together = [['tenant', 'date']]  # One stats record per tenant per day
        indexes = [
            models.Index(fields=['tenant', 'date']),
            models.Index(fields=['date']),
        ]
        verbose_name = "Tenant Daily Stats"
        verbose_name_plural = "Tenant Daily Stats"

    def __str__(self):
        return f"{self.tenant.name} - {self.date}"


class GlobalPlatformStats(TimeStampedModel):
    """
    Platform-wide statistics for marketing and business reporting.

    SUPERADMIN ACCESS: YES - Aggregate data across all tenants.
    Used for market reporting: "X active tenants, Y messages processed daily"

    Does NOT contain any tenant-specific content.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Date for this stats snapshot
    date = models.DateField(unique=True, help_text="Date of this stats snapshot", db_index=True)

    # Tenant metrics
    total_tenants = models.IntegerField(default=0, help_text="Total tenants on platform")
    active_tenants = models.IntegerField(default=0, help_text="Tenants active today")
    new_tenants_today = models.IntegerField(default=0, help_text="Tenants created today")
    paying_tenants = models.IntegerField(default=0, help_text="Tenants with paid subscriptions")
    trial_tenants = models.IntegerField(default=0, help_text="Tenants in trial")

    # User metrics (across all tenants)
    total_users = models.IntegerField(default=0, help_text="Total users across all tenants")
    active_users_today = models.IntegerField(default=0, help_text="Active users today")
    new_users_today = models.IntegerField(default=0, help_text="New users today")

    # Resource metrics (across all tenants)
    total_agents = models.IntegerField(default=0, help_text="Total agents created")
    total_groups = models.IntegerField(default=0, help_text="Total groups")
    total_mcp_servers = models.IntegerField(default=0, help_text="Total MCP servers")
    total_tools = models.IntegerField(default=0, help_text="Total tools")

    # Activity metrics
    messages_today = models.IntegerField(default=0, help_text="Messages processed today")
    total_messages = models.BigIntegerField(default=0, help_text="Total messages (cumulative)")
    api_calls_today = models.IntegerField(default=0, help_text="API calls today")

    # Storage metrics
    total_storage_used_gb = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total storage used across all tenants (GB)"
    )

    # Revenue metrics
    total_revenue_today = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total revenue today"
    )
    monthly_recurring_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Monthly Recurring Revenue (MRR)"
    )

    # Support metrics
    open_tickets = models.IntegerField(default=0, help_text="Open support tickets")
    tickets_created_today = models.IntegerField(default=0, help_text="Tickets created today")
    tickets_resolved_today = models.IntegerField(default=0, help_text="Tickets resolved today")

    class Meta:
        ordering = ['-date']
        verbose_name = "Global Platform Stats"
        verbose_name_plural = "Global Platform Stats"

    def __str__(self):
        return f"Platform Stats - {self.date}"


class SupportTicket(TimeStampedModel):
    """
    Support tickets from tenants.

    SUPERADMIN ACCESS: YES - Tickets are for superadmin to manage support.
    Contains tenant contact info and issue description, but NOT tenant data.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='support_tickets',
        help_text="Tenant that raised this ticket"
    )

    # Ticket details
    subject = models.CharField(max_length=255, help_text="Ticket subject")
    description = models.TextField(help_text="Issue description")

    # Contact info (tenant admin who raised the ticket)
    raised_by_email = models.EmailField(help_text="Email of user who raised ticket")
    raised_by_name = models.CharField(max_length=255, help_text="Name of user who raised ticket")

    # Priority and status
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('waiting_customer', 'Waiting on Customer'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        default='open'
    )

    # Category
    category = models.CharField(
        max_length=50,
        choices=[
            ('billing', 'Billing'),
            ('technical', 'Technical Issue'),
            ('feature_request', 'Feature Request'),
            ('bug', 'Bug Report'),
            ('account', 'Account Management'),
            ('other', 'Other'),
        ],
        default='other'
    )

    # Assignment
    assigned_to = models.EmailField(
        blank=True,
        null=True,
        help_text="Superadmin email assigned to this ticket"
    )

    # Resolution
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, help_text="Internal resolution notes")

    # Metadata
    last_response_at = models.DateTimeField(blank=True, null=True)
    response_time_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Time to first response (hours)"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def __str__(self):
        return f"[{self.status.upper()}] {self.subject} - {self.tenant.name}"
