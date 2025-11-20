# AgentVerse Cloud Backend - Complete Architecture

**Date:** 2025-11-20
**Three Critical Backend Suites**

---

## Architecture Overview

The AgentVerse cloud backend consists of **three critical suites** that work together to provide a secure, real-time, multi-tenant AI platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                   AGENTVERSE CLOUD BACKEND                      │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   SUITE 1:      │  │   SUITE 2:      │  │   SUITE 3:      │
│   WebSocket     │  │   Data Updater  │  │   Admin &       │
│   Router        │  │   & Sender      │  │   Security      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
        │                    │                    │
        │                    │                    │
        ├────────────────────┴────────────────────┤
        │                                         │
        ▼                                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Multi-Tenant Database (PostgreSQL)             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ public  │  │ tenant_ │  │ tenant_ │  │ tenant_ │       │
│  │ schema  │  │ acme    │  │ techco  │  │ startup │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## SUITE 1: WebSocket Router

**Purpose:** Real-time bidirectional communication between cloud backend and local frontends

**Technology Stack:**
- Django Channels
- Redis (Channel Layer)
- WebSocket Protocol

### Components

#### 1.1 WebSocket Consumers

**Location:** `apps/core/consumers.py` (likely)

```python
class SyncConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time synchronization.

    Handles:
    - Tenant-scoped connections
    - Group-scoped connections
    - Authentication via JWT
    - Message routing
    """

    async def connect(self):
        # Extract JWT from Authorization header
        token = self.scope['headers'].get('authorization')

        # Authenticate user and get tenant
        user, tenant = await authenticate_websocket(token)

        # Join tenant channel
        await self.channel_layer.group_add(
            f"tenant_{tenant.id}",
            self.channel_name
        )

        await self.accept()

    async def receive(self, text_data):
        # Handle incoming messages from local frontend
        data = json.loads(text_data)

        # Route to appropriate handler
        if data['type'] == 'agent_update':
            await self.handle_agent_update(data)
        elif data['type'] == 'message':
            await self.handle_message(data)

    async def disconnect(self, close_code):
        # Leave all groups
        await self.channel_layer.group_discard(
            f"tenant_{self.tenant.id}",
            self.channel_name
        )
```

#### 1.2 Channel Routing

**Location:** `config/routing.py`

```python
from django.urls import path
from apps.core.consumers import SyncConsumer

websocket_urlpatterns = [
    # Tenant-wide sync
    path('ws/sync/', SyncConsumer.as_asgi()),

    # Group-specific sync
    path('ws/group/<uuid:group_id>/', GroupSyncConsumer.as_asgi()),
]
```

#### 1.3 Channel Layers Configuration

**Location:** `config/settings.py`

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}
```

### WebSocket Message Flow

```
Local Frontend                Cloud Backend                Redis
     │                             │                         │
     │ 1. Connect WS               │                         │
     ├────────────────────────────>│                         │
     │                             │ 2. Authenticate JWT     │
     │                             │                         │
     │                             │ 3. Join tenant group    │
     │                             ├────────────────────────>│
     │                             │                         │
     │ 4. Send message             │                         │
     ├────────────────────────────>│                         │
     │                             │ 5. Process & broadcast  │
     │                             ├────────────────────────>│
     │                             │                         │
     │ 6. Receive broadcast        │                         │
     │<─────────────────────────────┤<────────────────────────┤
```

### Channels and Groups

#### Tenant-Scoped Channels
```python
# Broadcast to ALL users in a tenant
channel_layer.group_send(
    f"tenant_{tenant_id}",
    {
        'type': 'settings_updated',
        'data': settings_data
    }
)
```

#### Group-Scoped Channels
```python
# Broadcast to users in a specific group
channel_layer.group_send(
    f"group_{group_id}",
    {
        'type': 'message_created',
        'data': message_data
    }
)
```

### Security Features

1. **JWT Authentication**
   - Token validated on connect
   - User and tenant extracted from token
   - Unauthorized connections rejected

2. **Tenant Isolation**
   - Each tenant has separate channel group
   - Cross-tenant broadcasts blocked

3. **Permission Checks**
   - User must have access to group
   - Admin-only broadcasts (e.g., settings)

### Endpoints

```
# WebSocket endpoints (wss://)
wss://agentverse.com/ws/sync/
wss://agentverse.com/ws/group/{group_id}/
```

---

## SUITE 2: Data Updater & Sender

**Purpose:** Synchronize data changes across all connected clients in real-time

**Technology Stack:**
- Django Signals
- Django Channels (for broadcasting)
- Serializers (for data formatting)

### Components

#### 2.1 Signal Handlers

**Location:** `apps/core/signals.py`

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

# ============================================================================
# TENANT-SCOPED BROADCASTS (all users in tenant)
# ============================================================================

@receiver(post_save, sender='tenants.TenantSettings')
def tenant_settings_saved(sender, instance, created, **kwargs):
    """
    Broadcast tenant settings update to ALL users in tenant.

    Use case: Admin updates logo/colors, all users see changes instantly.
    """
    from apps.tenants.serializers import TenantSettingsSerializer

    settings_data = TenantSettingsSerializer(instance).data

    async_to_sync(channel_layer.group_send)(
        f"tenant_{instance.tenant_id}",
        {
            'type': 'settings_updated',
            'data': {
                'settings': settings_data,
                'event': 'updated' if not created else 'created'
            }
        }
    )

@receiver(post_save, sender='agents.Agent')
def agent_saved(sender, instance, created, **kwargs):
    """
    Broadcast agent create/update to all users in tenant.

    Use case: Admin creates agent, all users can see it immediately.
    """
    from apps.agents.serializers import AgentSerializer

    agent_data = AgentSerializer(instance).data

    async_to_sync(channel_layer.group_send)(
        f"tenant_{instance.tenant_id}",
        {
            'type': 'agent_updated',
            'data': {
                'agent': agent_data,
                'event': 'created' if created else 'updated'
            }
        }
    )

@receiver(post_delete, sender='agents.Agent')
def agent_deleted(sender, instance, **kwargs):
    """Broadcast agent deletion to tenant."""
    async_to_sync(channel_layer.group_send)(
        f"tenant_{instance.tenant_id}",
        {
            'type': 'agent_deleted',
            'data': {
                'agent_id': str(instance.id)
            }
        }
    )

# ============================================================================
# GROUP-SCOPED BROADCASTS (only group members)
# ============================================================================

@receiver(post_save, sender='messages.Message')
def message_saved(sender, instance, created, **kwargs):
    """
    Broadcast message to group members only.

    Use case: User sends message, all group members see it in real-time.
    """
    if not created:
        return  # Only broadcast new messages

    from apps.messages.serializers import MessageSerializer

    message_data = MessageSerializer(instance).data

    async_to_sync(channel_layer.group_send)(
        f"group_{instance.group_id}",
        {
            'type': 'message_created',
            'data': {
                'message': message_data
            }
        }
    )

@receiver(post_save, sender='documents.Document')
def document_saved(sender, instance, created, **kwargs):
    """
    Broadcast document upload to group members.

    Use case: User uploads document, group members notified.
    """
    from apps.documents.serializers import DocumentSerializer

    # Check visibility: tenant admin sees all, group members see group docs
    if instance.group:
        # Group-scoped document
        channel = f"group_{instance.group_id}"
    else:
        # Tenant-wide document (admin uploaded)
        channel = f"tenant_{instance.tenant_id}"

    document_data = DocumentSerializer(instance).data

    async_to_sync(channel_layer.group_send)(
        channel,
        {
            'type': 'document_updated',
            'data': {
                'document': document_data,
                'event': 'created' if created else 'updated'
            }
        }
    )
```

#### 2.2 Broadcast Helper Functions

**Location:** `apps/core/utils/broadcast.py`

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

def broadcast_to_tenant(tenant_id: str, event_type: str, data: dict):
    """
    Broadcast event to all users in a tenant.

    Args:
        tenant_id: UUID of tenant
        event_type: Event type (e.g., 'agent_updated', 'settings_updated')
        data: Event payload
    """
    async_to_sync(channel_layer.group_send)(
        f"tenant_{tenant_id}",
        {
            'type': event_type,
            'data': data
        }
    )

def broadcast_to_group(group_id: str, event_type: str, data: dict):
    """
    Broadcast event to all members of a group.

    Args:
        group_id: UUID of group
        event_type: Event type (e.g., 'message_created', 'document_updated')
        data: Event payload
    """
    async_to_sync(channel_layer.group_send)(
        f"group_{group_id}",
        {
            'type': event_type,
            'data': data
        }
    )

def broadcast_to_user(user_id: str, event_type: str, data: dict):
    """
    Broadcast event to a specific user only.

    Args:
        user_id: UUID of user
        event_type: Event type (e.g., 'notification')
        data: Event payload
    """
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            'type': event_type,
            'data': data
        }
    )
```

#### 2.3 Consumer Message Handlers

**Location:** `apps/core/consumers.py`

```python
class SyncConsumer(AsyncWebsocketConsumer):
    # ... (connect/disconnect methods)

    # ========================================================================
    # TENANT-SCOPED EVENT HANDLERS
    # ========================================================================

    async def settings_updated(self, event):
        """Handle tenant settings update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'settings_updated',
            'data': event['data']
        }))

    async def agent_updated(self, event):
        """Handle agent create/update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'agent_updated',
            'data': event['data']
        }))

    async def agent_deleted(self, event):
        """Handle agent deletion broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'agent_deleted',
            'data': event['data']
        }))

    # ========================================================================
    # GROUP-SCOPED EVENT HANDLERS
    # ========================================================================

    async def message_created(self, event):
        """Handle new message broadcast (group members only)."""
        # Verify user is member of group
        if await self.user_in_group(event['data']['message']['group_id']):
            await self.send(text_data=json.dumps({
                'type': 'message_created',
                'data': event['data']
            }))

    async def document_updated(self, event):
        """Handle document upload broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'document_updated',
            'data': event['data']
        }))
```

### Data Update Flow

```
User Action (API)        Django Backend             Redis Channel Layer        Connected Clients
      │                        │                            │                         │
      │ 1. POST /agents/       │                            │                         │
      ├───────────────────────>│                            │                         │
      │                        │ 2. Create Agent            │                         │
      │                        │    (DB write)              │                         │
      │                        │                            │                         │
      │                        │ 3. post_save signal        │                         │
      │                        │    triggers                │                         │
      │                        │                            │                         │
      │                        │ 4. Serialize Agent         │                         │
      │                        │                            │                         │
      │                        │ 5. group_send()            │                         │
      │                        ├───────────────────────────>│                         │
      │                        │                            │                         │
      │                        │                            │ 6. Broadcast to all     │
      │                        │                            ├────────────────────────>│
      │                        │                            │                         │
      │<───────────────────────┤                            │                         │
      │ 7. HTTP 201 Created    │                            │                         │
      │                        │                            │                         │
      │                        │                            │ 8. WS: agent_updated    │
      │                        │                            │                         │
      All clients receive agent_updated event in real-time ─────────────────────────>│
```

### Broadcast Scopes

| Event | Scope | Recipients | Use Case |
|-------|-------|------------|----------|
| `settings_updated` | Tenant | All users in tenant | Admin updates logo |
| `agent_updated` | Tenant | All users in tenant | Admin creates agent |
| `tool_updated` | Tenant | All users in tenant | Admin adds tool |
| `mcp_updated` | Tenant | All users in tenant | Admin adds MCP server |
| `message_created` | Group | Group members only | User sends message |
| `document_updated` | Group | Group members only | User uploads doc |
| `notification` | User | Single user | Personal notification |

### Signal Registration

**Location:** Each app's `apps.py`

```python
# apps/agents/apps.py
class AgentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.agents'

    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.core.signals  # noqa: F401
```

---

## SUITE 3: Admin & Security

**Purpose:** Superadmin management, authentication, authorization, permissions, and license enforcement

**Technology Stack:**
- Django Admin
- Django REST Framework
- JWT Authentication
- Custom Permissions
- Multi-Tenancy (django-tenants)

### Components

#### 3.1 Authentication System

**Location:** `apps/users/views_auth.py`

```python
class LoginView(APIView):
    """
    3-field login: tenant_id, email, password

    Returns JWT with tenant_id and user_role in claims.
    """

    def post(self, request):
        # Extract fields
        tenant_slug = request.data.get('tenant_id')
        email = request.data.get('email')
        password = request.data.get('password')

        # 1. Validate tenant exists
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=401)

        # 2. Get user by email (users are in SHARED_APPS)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=401)

        # 3. Verify password
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=401)

        # 4. Verify user has access to this tenant via TenantMembership
        try:
            membership = TenantMembership.objects.get(
                user=user,
                tenant=tenant,
                is_active=True
            )
            user_role = membership.role
        except TenantMembership.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=401)

        # 5. Generate JWT with tenant_id and user_role
        refresh = RefreshToken.for_user(user)
        refresh['tenant_id'] = str(tenant.id)
        refresh['tenant_slug'] = tenant.slug
        refresh['user_role'] = user_role

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'tenant': TenantSerializer(tenant).data
        })
```

#### 3.2 Permission System

**Location:** `apps/core/permissions.py`

```python
# ============================================================================
# TENANT-LEVEL PERMISSIONS
# ============================================================================

class IsAdminUser(permissions.BasePermission):
    """Only tenant admins can perform action."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'admin'
        )

class IsTenantMember(permissions.BasePermission):
    """User must belong to current tenant."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check tenant from connection (django-tenants)
        from django.db import connection
        current_schema = connection.schema_name

        if current_schema == 'public':
            return request.user.is_superuser

        return request.user.tenant.schema_name == current_schema

# ============================================================================
# RESOURCE-LEVEL PERMISSIONS (Permission Model)
# ============================================================================

class HasPermission(permissions.BasePermission):
    """
    Check Permission model for fine-grained access control.

    Usage:
        class AgentViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, HasPermission]

            def get_permissions(self):
                if self.action == 'execute':
                    return [HasPermission('execute', 'agent')]
                return super().get_permissions()
    """

    def __init__(self, action, resource_type):
        self.action = action
        self.resource_type = resource_type

    def has_object_permission(self, request, view, obj):
        from apps.permissions.models import Permission

        # Admin bypass
        if request.user.role == 'admin':
            return True

        # Check user permission
        user_perm = Permission.objects.filter(
            tenant=obj.tenant,
            subject='user',
            subject_id=request.user.id,
            resource=self.resource_type,
            resource_id=obj.id,
            action=self.action,
            granted=True
        ).exists()

        if user_perm:
            return True

        # Check group permissions
        user_groups = request.user.groups.values_list('id', flat=True)
        group_perm = Permission.objects.filter(
            tenant=obj.tenant,
            subject='group',
            subject_id__in=user_groups,
            resource=self.resource_type,
            resource_id=obj.id,
            action=self.action,
            granted=True
        ).exists()

        return group_perm

# ============================================================================
# SUPERADMIN PERMISSIONS
# ============================================================================

class IsSuperAdmin(permissions.BasePermission):
    """
    Superadmin-only access.

    Requirements:
    1. is_superuser=True
    2. Connection on 'public' schema
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.is_superuser:
            return False

        # Must be on public schema
        from django.db import connection
        return connection.schema_name == 'public'
```

#### 3.3 License Enforcement

**Location:** `apps/tenants/middleware.py`

```python
class LicenseEnforcementMiddleware:
    """
    Enforce license limits on API requests.

    Checks:
    - Storage limit
    - Message limit
    - User limit
    - Agent limit
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for superadmin
        if request.user.is_superuser:
            return self.get_response(request)

        # Skip for non-authenticated requests
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Get tenant
        tenant = request.user.tenant
        if not tenant:
            return self.get_response(request)

        # Check if tenant is active
        if not tenant.is_active:
            return JsonResponse(
                {'error': 'Tenant account is suspended'},
                status=403
            )

        # Check trial expiry
        if tenant.is_trial and tenant.trial_end_date:
            if timezone.now() > tenant.trial_end_date:
                return JsonResponse(
                    {'error': 'Trial period expired'},
                    status=403
                )

        # Check storage limit
        if request.method == 'POST' and 'document' in request.path:
            if not tenant.is_within_storage_limit():
                return JsonResponse(
                    {'error': 'Storage limit exceeded'},
                    status=403
                )

        # Check message limit
        if request.method == 'POST' and 'message' in request.path:
            if not tenant.is_within_message_limit():
                return JsonResponse(
                    {'error': 'Monthly message limit exceeded'},
                    status=403
                )

        return self.get_response(request)
```

#### 3.4 Superadmin Management

**Django Admin Panels:**

1. **Tenant Management** (`apps/tenants/admin.py`)
   - View all tenants
   - Update subscriptions
   - Suspend/activate tenants
   - View usage stats

2. **Analytics** (`apps/analytics/admin.py`)
   - Tenant Daily Stats (aggregate metrics)
   - Global Platform Stats (business reporting)
   - Support Tickets (customer support)

3. **User Management** (tenant-scoped)
   - Create/edit users within tenant
   - Assign roles (admin/user)
   - Deactivate users

**Superadmin API Endpoints:**

```python
# Tenant Management
POST   /api/v1/tenants/admin/tenants/                    # Create tenant
PATCH  /api/v1/tenants/admin/tenants/{id}/               # Update tenant
POST   /api/v1/tenants/admin/tenants/{id}/suspend/       # Suspend
POST   /api/v1/tenants/admin/tenants/{id}/activate/      # Activate

# Analytics
GET    /api/v1/analytics/admin/tenant-stats/             # All tenant stats
GET    /api/v1/analytics/admin/platform-stats/latest/    # Platform metrics
GET    /api/v1/analytics/admin/tenants/                  # Tenant overview
GET    /api/v1/analytics/admin/tenants/at_risk/          # At-risk tenants

# Support
GET    /api/v1/analytics/admin/tickets/                  # All tickets
POST   /api/v1/analytics/admin/tickets/                  # Create ticket
POST   /api/v1/analytics/admin/tickets/{id}/assign/      # Assign ticket
POST   /api/v1/analytics/admin/tickets/{id}/resolve/     # Resolve ticket
```

#### 3.5 Multi-Tenancy Architecture

**Django-Tenants Configuration:**

```python
# config/settings.py

SHARED_APPS = [
    'django_tenants',  # Must be first
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    # Shared across all tenants
    'apps.users',      # Users can belong to multiple tenants
    'apps.tenants',    # Tenant management
    'apps.analytics',  # Superadmin analytics
]

TENANT_APPS = [
    # Isolated per tenant
    'apps.agents',
    'apps.groups',
    'apps.messages',
    'apps.documents',
    'apps.tools',
    'apps.mcp',
    'apps.permissions',
]

INSTALLED_APPS = SHARED_APPS + TENANT_APPS

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"
```

**Database Schema Structure:**

```
PostgreSQL Database: agentverse_db
│
├── public schema (shared across all tenants)
│   ├── tenants_tenant
│   ├── tenants_domain
│   ├── tenants_tenantmembership
│   ├── users_user
│   ├── analytics_usagelog
│   ├── analytics_tenantstats
│   ├── analytics_globalplatformstats
│   └── analytics_supportticket
│
├── tenant_acme schema (Acme Corp's data)
│   ├── agents_agent
│   ├── groups_group
│   ├── messages_message
│   ├── documents_document
│   ├── tools_tool
│   ├── mcp_mcpserver
│   └── permissions_permission
│
└── tenant_techco schema (TechCo's data)
    ├── agents_agent
    ├── groups_group
    ├── messages_message
    ├── documents_document
    ├── tools_tool
    ├── mcp_mcpserver
    └── permissions_permission
```

---

## How the Three Suites Work Together

### Example: User Sends Message

```
1. User types message in local frontend
   │
   ▼
2. Local frontend sends via WebSocket (SUITE 1)
   │
   ▼
3. Cloud backend receives in SyncConsumer
   │
   ▼
4. Authentication checked (SUITE 3: JWT validation)
   │
   ▼
5. Permission checked (SUITE 3: User in group?)
   │
   ▼
6. License checked (SUITE 3: Message limit?)
   │
   ▼
7. Message saved to database (tenant schema)
   │
   ▼
8. post_save signal triggers (SUITE 2)
   │
   ▼
9. Broadcast to group members (SUITE 1 + 2)
   │
   ▼
10. All connected group members receive message instantly
```

### Example: Admin Updates Tenant Settings

```
1. Tenant admin updates logo in settings
   │
   ▼
2. HTTP POST /api/v1/tenants/settings/update_current/ (SUITE 3)
   │
   ▼
3. Permission check (SUITE 3: Is admin?)
   │
   ▼
4. TenantSettings saved to database
   │
   ▼
5. post_save signal triggers (SUITE 2)
   │
   ▼
6. Broadcast to ALL users in tenant (SUITE 1 + 2)
   │
   ▼
7. All users see new logo without refresh
```

### Example: Superadmin Views Platform Stats

```
1. Superadmin visits Django admin
   │
   ▼
2. Authentication (SUITE 3: is_superuser check)
   │
   ▼
3. Views GlobalPlatformStats (SUITE 3: IsSuperAdmin permission)
   │
   ▼
4. Sees aggregate metrics (counts, revenue, MRR)
   │
   ▼
5. CANNOT see message content or documents (SUITE 3: privacy enforcement)
```

---

## Security Architecture

### Authentication Flow

```
1. User submits: { tenant_id, email, password }
   │
   ▼
2. Validate tenant exists and is active
   │
   ▼
3. Get user by email (SHARED_APPS)
   │
   ▼
4. Verify password
   │
   ▼
5. Check TenantMembership (user belongs to tenant?)
   │
   ▼
6. Generate JWT with claims:
   - user_id
   - tenant_id
   - user_role (admin/user)
   - tenant_slug
   │
   ▼
7. Return JWT + user info + tenant info
```

### Authorization Levels

| Level | Check | Enforced By |
|-------|-------|-------------|
| **Authentication** | Is user logged in? | IsAuthenticated |
| **Tenant Membership** | Does user belong to tenant? | IsTenantMember |
| **Role-Based** | Is user admin? | IsAdminUser |
| **Resource-Based** | Does user have permission? | HasPermission |
| **License** | Is tenant within limits? | LicenseEnforcementMiddleware |
| **Superadmin** | Is superuser on public schema? | IsSuperAdmin |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer (Nginx)                   │
└────────────────────┬────────────────────────┬───────────────────┘
                     │                        │
         ┌───────────▼──────────┐  ┌──────────▼──────────┐
         │  Django App Server   │  │  Django App Server  │
         │  (Gunicorn + ASGI)   │  │  (Gunicorn + ASGI)  │
         └───────────┬──────────┘  └──────────┬──────────┘
                     │                        │
         ┌───────────┴────────────────────────┴───────────┐
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐                             ┌─────────────────┐
│   PostgreSQL    │                             │      Redis      │
│  Multi-Tenant   │                             │  Channel Layer  │
│   + pgvector    │                             │   + Cache       │
└─────────────────┘                             └─────────────────┘
```

---

## File Structure

```
cloud_backend/
├── config/
│   ├── settings.py              # Django settings
│   ├── routing.py               # WebSocket routing (SUITE 1)
│   ├── asgi.py                  # ASGI application
│   └── urls.py                  # HTTP routing
│
├── apps/
│   ├── core/
│   │   ├── consumers.py         # WebSocket consumers (SUITE 1)
│   │   ├── signals.py           # Signal handlers (SUITE 2)
│   │   ├── permissions.py       # Permission classes (SUITE 3)
│   │   └── admin.py             # Base admin classes
│   │
│   ├── users/
│   │   ├── models.py            # User model (SHARED_APPS)
│   │   ├── views_auth.py        # Login/logout (SUITE 3)
│   │   └── serializers.py
│   │
│   ├── tenants/
│   │   ├── models.py            # Tenant, TenantSettings (SUITE 3)
│   │   ├── views_admin.py       # Superadmin tenant mgmt (SUITE 3)
│   │   ├── middleware.py        # License enforcement (SUITE 3)
│   │   └── admin.py             # Django admin
│   │
│   ├── analytics/
│   │   ├── models.py            # TenantStats, GlobalPlatformStats (SUITE 3)
│   │   ├── views.py             # Analytics endpoints (SUITE 3)
│   │   └── admin.py             # Superadmin analytics (SUITE 3)
│   │
│   ├── agents/
│   │   ├── models.py            # Agent model (TENANT_APPS)
│   │   └── apps.py              # Signal registration (SUITE 2)
│   │
│   ├── groups/
│   │   └── models.py            # Group model (TENANT_APPS)
│   │
│   ├── messages/
│   │   └── models.py            # Message model (TENANT_APPS)
│   │
│   ├── documents/
│   │   └── models.py            # Document model (TENANT_APPS)
│   │
│   ├── tools/
│   │   └── models.py            # Tool model (TENANT_APPS)
│   │
│   ├── mcp/
│   │   └── models.py            # MCP server model (TENANT_APPS)
│   │
│   └── permissions/
│       └── models.py            # Permission model (TENANT_APPS)
│
└── docs/
    ├── BACKEND_ARCHITECTURE.md  # This file
    ├── SUPERADMIN_ANALYTICS_GUIDE.md
    ├── TENANT_CREATION_FLOW.md
    └── DATA_CLASSIFICATION_MATRIX.md
```

---

## Summary

The AgentVerse cloud backend consists of **three critical suites**:

### SUITE 1: WebSocket Router
- **Purpose:** Real-time bidirectional communication
- **Components:** Django Channels, Redis, WebSocket consumers
- **Responsibility:** Connect local frontends, route messages, broadcast updates

### SUITE 2: Data Updater & Sender
- **Purpose:** Synchronize data changes across all clients
- **Components:** Django signals, channel layers, serializers
- **Responsibility:** Detect changes, serialize data, broadcast to appropriate channels

### SUITE 3: Admin & Security
- **Purpose:** Authentication, authorization, superadmin management, license enforcement
- **Components:** Django Admin, JWT auth, permissions, multi-tenancy
- **Responsibility:** Secure access, manage tenants, enforce limits, provide analytics

**These three suites work together** to provide a secure, real-time, multi-tenant AI platform where:
- Data is isolated per tenant (multi-tenancy)
- Changes sync instantly (WebSocket + signals)
- Access is controlled (auth + permissions + licenses)
- Superadmin can manage without seeing content (privacy-first)

---

**Version:** 1.0
**Last Updated:** 2025-11-20
**Status:** ✅ Complete Architecture Guide
