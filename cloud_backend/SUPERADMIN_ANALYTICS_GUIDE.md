# Superadmin Analytics System - Complete Guide

**Date:** 2025-11-20
**Purpose:** Business analytics and tenant management for platform superadmins
**Security Model:** Privacy-first - Superadmin sees "HOW MUCH" but NOT "WHAT"

---

## Table of Contents

1. [Overview](#overview)
2. [Security Architecture](#security-architecture)
3. [Models](#models)
4. [API Endpoints](#api-endpoints)
5. [Django Admin Interface](#django-admin-interface)
6. [Usage Examples](#usage-examples)
7. [Deployment](#deployment)

---

## Overview

The Superadmin Analytics System provides platform-wide business metrics and tenant management capabilities while maintaining strict privacy boundaries. Superadmins can:

✅ **CAN ACCESS:**
- Aggregate statistics (user counts, message counts, etc.)
- Subscription and billing information
- Tenant contact details (admin email, company info)
- Resource utilization metrics (storage, API calls)
- Support tickets
- Revenue metrics

❌ **CANNOT ACCESS:**
- Actual message content
- Document content
- Agent configurations
- User personal data
- Group conversations
- Any tenant-created content

---

## Security Architecture

### Two-Tier Access Control

#### 1. Tenant-Scoped Data
- **Who:** Tenant admins and users
- **Access:** Only their own tenant's data
- **Filtering:** Automatic via `TenantFilteredAdmin` and `get_queryset()`
- **Examples:** UsageLog (for their tenant)

#### 2. Superadmin-Only Data
- **Who:** Platform superadmins ONLY
- **Access:** Aggregate stats across all tenants
- **Permission:** `IsSuperAdmin` (requires `is_superuser=True` + on `public` schema)
- **Examples:** TenantStats, GlobalPlatformStats, SupportTicket

### Permission Class: `IsSuperAdmin`

```python
class IsSuperAdmin(permissions.BasePermission):
    """
    Enforces superadmin-only access.

    Requirements:
    1. User must be authenticated
    2. User must have is_superuser=True
    3. Connection must be on 'public' schema (not a tenant schema)
    """
```

**Location:** `apps/core/permissions.py:77-125`

---

## Models

### 1. TenantStats

**Purpose:** Daily aggregated statistics per tenant

**Fields:**
- `tenant`: ForeignKey to Tenant
- `date`: Date of this snapshot
- User metrics: `total_users`, `active_users_today`, `new_users_today`
- Agent metrics: `total_agents`, `new_agents_today`
- MCP/Tool metrics: `total_mcp_servers`, `total_tools`
- Group metrics: `total_groups`, `active_groups_today`
- Message metrics: `messages_sent_today`, `total_messages` (counts only, NO content)
- Document metrics: `documents_uploaded_today`, `total_documents` (counts only, NO content)
- Storage metrics: `storage_used_mb`, `storage_delta_mb`
- Revenue: `estimated_revenue_today`

**Unique Constraint:** One record per tenant per day

**Use Cases:**
- Daily reports: "Acme Corp sent 1,234 messages today"
- Trend analysis: "Tenant X's usage growing 20% week-over-week"
- Resource planning: "Storage increasing by 100MB/day"

**Location:** `apps/analytics/models.py:40-126`

---

### 2. GlobalPlatformStats

**Purpose:** Platform-wide statistics for business reporting

**Fields:**
- `date`: Date of this snapshot
- Tenant metrics: `total_tenants`, `active_tenants`, `new_tenants_today`, `paying_tenants`, `trial_tenants`
- User metrics: `total_users`, `active_users_today`, `new_users_today`
- Resource metrics: `total_agents`, `total_groups`, `total_mcp_servers`, `total_tools`
- Activity: `messages_today`, `total_messages`, `api_calls_today`
- Storage: `total_storage_used_gb`
- Revenue: `total_revenue_today`, `monthly_recurring_revenue`
- Support: `open_tickets`, `tickets_created_today`, `tickets_resolved_today`

**Unique Constraint:** One record per day

**Use Cases:**
- Marketing: "1,000+ active tenants, processing 1M+ messages/day"
- Executive dashboard: Revenue, growth, churn
- Capacity planning: Storage, API load

**Location:** `apps/analytics/models.py:129-200`

---

### 3. SupportTicket

**Purpose:** Support ticket management

**Fields:**
- `tenant`: ForeignKey to Tenant
- `subject`, `description`: Ticket details
- `raised_by_email`, `raised_by_name`: Contact info
- `priority`: low/medium/high/critical
- `status`: open/in_progress/waiting_customer/resolved/closed
- `category`: billing/technical/feature_request/bug/account/other
- `assigned_to`: Superadmin email
- `resolved_at`, `resolution_notes`: Resolution tracking
- `response_time_hours`: Time to first response

**Use Cases:**
- Support queue management
- SLA tracking (response time)
- Tenant health monitoring

**Location:** `apps/analytics/models.py:203-298`

---

### 4. Tenant Model Updates

Added fields for superadmin visibility:

```python
# Contact information
admin_name = models.CharField(max_length=255, blank=True)

# Company information (for analytics)
company_size = models.CharField(max_length=20, choices=[...])
industry = models.CharField(max_length=100, blank=True)
```

**Purpose:** Segment tenants, personalize outreach

**Location:** `apps/tenants/models.py:43-69`

---

## API Endpoints

All superadmin endpoints require `IsSuperAdmin` permission.

### Base URL Structure

- **Tenant-scoped:** `/api/v1/analytics/logs/` (for tenant admins)
- **Superadmin-only:** `/api/v1/analytics/admin/*` (for superadmin)

### Superadmin Endpoints

#### TenantStatsViewSet

```
GET /api/v1/analytics/admin/tenant-stats/
GET /api/v1/analytics/admin/tenant-stats/{id}/
GET /api/v1/analytics/admin/tenant-stats/latest/
GET /api/v1/analytics/admin/tenant-stats/summary/
```

**Query Params:**
- `tenant`: Filter by tenant ID
- `date`: Filter by date

**Example Response:**
```json
{
  "id": "uuid",
  "tenant": "uuid",
  "tenant_name": "Acme Corp",
  "tenant_email": "admin@acme.com",
  "date": "2025-11-20",
  "total_users": 25,
  "active_users_today": 18,
  "total_agents": 10,
  "messages_sent_today": 1234,
  "storage_used_mb": 5678.90
}
```

---

#### GlobalPlatformStatsViewSet

```
GET /api/v1/analytics/admin/platform-stats/
GET /api/v1/analytics/admin/platform-stats/{id}/
GET /api/v1/analytics/admin/platform-stats/latest/
GET /api/v1/analytics/admin/platform-stats/trends/?days=30
```

**Example Response (`/latest/`):**
```json
{
  "date": "2025-11-20",
  "total_tenants": 150,
  "active_tenants": 120,
  "paying_tenants": 80,
  "total_users": 3500,
  "messages_today": 125000,
  "monthly_recurring_revenue": 50000.00
}
```

---

#### SupportTicketViewSet

```
GET    /api/v1/analytics/admin/tickets/
POST   /api/v1/analytics/admin/tickets/
GET    /api/v1/analytics/admin/tickets/{id}/
PATCH  /api/v1/analytics/admin/tickets/{id}/
DELETE /api/v1/analytics/admin/tickets/{id}/

GET  /api/v1/analytics/admin/tickets/open/
GET  /api/v1/analytics/admin/tickets/critical/
POST /api/v1/analytics/admin/tickets/{id}/assign/
POST /api/v1/analytics/admin/tickets/{id}/resolve/
```

**Example: Assign Ticket**
```bash
POST /api/v1/analytics/admin/tickets/{id}/assign/
{
  "assigned_to": "support@company.com"
}
```

**Example: Resolve Ticket**
```bash
POST /api/v1/analytics/admin/tickets/{id}/resolve/
{
  "resolution_notes": "Fixed billing issue, credited account $50"
}
```

---

#### TenantOverviewViewSet

```
GET /api/v1/analytics/admin/tenants/
GET /api/v1/analytics/admin/tenants/{id}/
GET /api/v1/analytics/admin/tenants/at_risk/
```

**Purpose:** Comprehensive tenant dashboard

**Example Response:**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "email": "admin@acme.com",
  "admin_name": "John Doe",
  "company_size": "51-200",
  "industry": "Technology",
  "license_type": "pro",
  "subscription_status": "active",
  "storage_used_mb": 5678,
  "messages_this_month": 45000,
  "latest_stats": { ... },
  "open_tickets": 2,
  "critical_tickets": 0,
  "is_active": true
}
```

**`/at_risk/` Endpoint:**
Returns tenants that need attention:
- Trial ending soon (< 7 days)
- Payment past due
- Critical tickets open
- No activity in 7+ days

---

## Django Admin Interface

Access: `http://localhost:8000/admin/` (requires `is_superuser=True`)

### Available Admin Panels

#### 1. **Tenant Daily Stats**
- **Model:** TenantStats
- **Features:**
  - View all tenant stats
  - Filter by date, license type, subscription status
  - Search by tenant name/email
  - Date hierarchy navigation
- **Actions:** Read-only (stats auto-generated)

#### 2. **Global Platform Stats**
- **Model:** GlobalPlatformStats
- **Features:**
  - View platform-wide metrics
  - Date-based filtering
  - Quick dashboard view
- **Actions:** Read-only (stats auto-generated)

#### 3. **Support Tickets**
- **Model:** SupportTicket
- **Features:**
  - Color-coded priority badges (critical=red, high=orange, etc.)
  - Status badges (open=red, in_progress=yellow, resolved=green)
  - Tenant contact info inline
  - Assignment and resolution tracking
  - Auto-calculated response times
- **Actions:** Full CRUD (create, edit, delete tickets)

#### 4. **Usage Logs** (Tenant-Scoped)
- **Model:** UsageLog
- **Features:**
  - Tenant-filtered (admins see only their tenant)
  - Action and resource type filtering
- **Actions:** Read-only

---

## Usage Examples

### Example 1: Get Today's Platform Metrics

```python
# API call (requires superadmin auth)
import requests

response = requests.get(
    'http://localhost:8000/api/v1/analytics/admin/platform-stats/latest/',
    headers={'Authorization': 'Bearer {superadmin_token}'}
)

stats = response.json()
print(f"Active tenants today: {stats['active_tenants']}")
print(f"Messages processed: {stats['messages_today']}")
print(f"MRR: ${stats['monthly_recurring_revenue']}")
```

---

### Example 2: Find At-Risk Tenants

```python
response = requests.get(
    'http://localhost:8000/api/v1/analytics/admin/tenants/at_risk/',
    headers={'Authorization': 'Bearer {superadmin_token}'}
)

at_risk = response.json()
for tenant in at_risk:
    print(f"{tenant['name']}: {', '.join(tenant['risk_reasons'])}")

# Output:
# Acme Corp: Trial ending soon, 1 critical tickets
# TechStart: No activity in 7+ days
```

---

### Example 3: Create Support Ticket (via API)

```python
import requests

ticket_data = {
    "tenant": "uuid-of-tenant",
    "subject": "Billing discrepancy",
    "description": "Customer reports being charged twice",
    "raised_by_email": "admin@customer.com",
    "raised_by_name": "Jane Admin",
    "priority": "high",
    "category": "billing"
}

response = requests.post(
    'http://localhost:8000/api/v1/analytics/admin/tickets/',
    json=ticket_data,
    headers={'Authorization': 'Bearer {superadmin_token}'}
)

ticket = response.json()
print(f"Ticket created: {ticket['id']}")
```

---

### Example 4: View Tenant's Monthly Trend

```python
import requests
from datetime import date, timedelta

tenant_id = "uuid-of-tenant"
thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()

response = requests.get(
    f'http://localhost:8000/api/v1/analytics/admin/tenant-stats/',
    params={
        'tenant': tenant_id,
        'date__gte': thirty_days_ago
    },
    headers={'Authorization': 'Bearer {superadmin_token}'}
)

stats = response.json()
for day in stats:
    print(f"{day['date']}: {day['messages_sent_today']} messages, {day['active_users_today']} active users")
```

---

## Deployment

### 1. Run Migrations

```bash
# Create migrations for new models
python manage.py makemigrations analytics tenants

# Apply migrations
python manage.py migrate
```

### 2. Create Superuser

```bash
python manage.py createsuperuser
# Email: superadmin@company.com
# Password: ********
```

### 3. Calculate Initial Stats (Optional)

Create a management command or cron job to calculate daily stats:

```python
# management/commands/calculate_daily_stats.py
from django.core.management.base import BaseCommand
from apps.analytics.models import TenantStats, GlobalPlatformStats
from apps.tenants.models import Tenant
from datetime import date

class Command(BaseCommand):
    def handle(self, *args, **options):
        today = date.today()

        for tenant in Tenant.objects.all():
            # Calculate tenant stats
            # ... (count users, agents, messages, etc.)

            TenantStats.objects.update_or_create(
                tenant=tenant,
                date=today,
                defaults={...}
            )

        # Calculate global stats
        # ... (aggregate across all tenants)

        GlobalPlatformStats.objects.update_or_create(
            date=today,
            defaults={...}
        )
```

**Run daily via cron:**
```bash
0 2 * * * cd /path/to/project && python manage.py calculate_daily_stats
```

### 4. Security Checklist

- ✅ Only superusers can access superadmin endpoints
- ✅ Superadmin must be on `public` schema (not tenant schema)
- ✅ Analytics models contain NO tenant content
- ✅ Tenant-scoped models use `TenantFilteredAdmin`
- ✅ API responses validated by serializers
- ✅ Support tickets contain contact info only, not tenant data

---

## Marketing Use Cases

### "Boast in Market" Metrics

Use `GlobalPlatformStats` to generate marketing copy:

```python
latest_stats = GlobalPlatformStats.objects.order_by('-date').first()

marketing_copy = f"""
AgentVerse Platform Stats:
- {latest_stats.total_tenants}+ organizations trust AgentVerse
- {latest_stats.total_users:,} users worldwide
- {latest_stats.messages_today:,} AI messages processed daily
- {latest_stats.total_agents} AI agents deployed
- {latest_stats.total_groups} collaborative groups
"""
```

**Example Output:**
> "1,000+ organizations trust AgentVerse
> 50,000 users worldwide
> 500,000+ AI messages processed daily
> 10,000+ AI agents deployed
> 5,000+ collaborative groups"

---

## Support

For issues or questions:
- **Email:** dev-team@agentverse.com
- **Docs:** `cloud_backend/SUPERADMIN_ANALYTICS_GUIDE.md` (this file)
- **Code Reference:**
  - Models: `apps/analytics/models.py`
  - Views: `apps/analytics/views.py`
  - Permissions: `apps/core/permissions.py`
  - Admin: `apps/analytics/admin.py`

---

## Future Enhancements

1. **Automated Stats Calculation:** Background task (Celery) to calculate daily stats
2. **Alerts:** Email notifications for at-risk tenants
3. **Data Export:** CSV/Excel export for reports
4. **Dashboard UI:** React dashboard for superadmin
5. **Audit Logging:** Track superadmin actions (who viewed what)
6. **Revenue Calculation:** Automated revenue calculation based on usage

---

**Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** ✅ Ready for Production
