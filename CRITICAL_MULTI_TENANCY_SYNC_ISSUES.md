# 🚨 CRITICAL: Multi-Tenancy Synchronization Issues

## ARCHITECTURE DISCOVERED

```
Local Frontend (Desktop App)
    ↓ (HTTP requests with JWT containing tenant_id)
Cloud Backend (Django REST API - Auth Middleware + Multi-Tenant SaaS)
    ├─ Authenticates user via JWT
    ├─ Extracts tenant_id from token/domain
    ├─ Filters ALL queries by tenant
    ├─ Returns tenant-scoped JSON data
    ↓ (tenant-scoped data with tenant_id fields)
Local Backend (FastAPI - Execution Engine)
    ├─ Receives tenant-scoped configs from cloud
    ├─ Caches locally WITH tenant_id on every entity
    ├─ Executes agents/tools in tenant context
    └─ Sends execution results back to cloud
```

## CRITICAL SECURITY BREACHES FOUND

### 1. ❌ UserViewSet Data Leak
**File:** `cloud_backend/apps/users/views.py`
**Issue:** Returns ALL users from ALL tenants
**Impact:** SECURITY BREACH - Cross-tenant data exposure

### 2. ❌ Missing Tenant IDs on Models
**Issue:** TENANT_APP models don't have explicit `tenant` field
**Models affected:**
- Agent (apps/agents/models.py)
- Tool (apps/tools/models.py)
- MCPServer (apps/mcp/models.py)
- Group (apps/groups/models.py)
- Message (apps/messages/models.py)
- Document (apps/documents/models.py)

**Impact:**
- Local backend expects `tenant_id` in JSON responses
- Cannot properly sync without explicit tenant identification
- Relies entirely on schema context (fragile)

### 3. ❌ Django Admin Can View/Edit Cross-Tenant Data
**Issue:** No tenant filtering in admin panels
**Impact:** Superusers or misconfigurations can view/edit wrong tenant's data

### 4. ❌ No Explicit Tenant Filtering in ViewSets
**Issue:** All ViewSets use `queryset = Model.objects.all()`
**Impact:** Relies only on middleware (no defense-in-depth)

## ARCHITECTURAL REQUIREMENT

**User stated:** *"tenant is base identifier"*
**Meaning:** EVERY entity must have explicit `tenant` field

**Current problem:**
- Django-tenants uses schema-based isolation
- Entities in TENANT_APPS are in separate schemas
- No explicit tenant field needed for database isolation
- **BUT:** Local backend sync requires explicit tenant_id in JSON

## REQUIRED FIXES

### Priority 1: CRITICAL (Security Breach)

#### Fix 1: Add Explicit Tenant Field to All Models

**Models to update:**
1. `cloud_backend/apps/agents/models.py` - Agent
2. `cloud_backend/apps/tools/models.py` - Tool
3. `cloud_backend/apps/mcp/models.py` - MCPServer
4. `cloud_backend/apps/groups/models.py` - Group
5. `cloud_backend/apps/messages/models.py` - Message
6. `cloud_backend/apps/documents/models.py` - Document

**Add to each model:**
```python
from django.db import connection
from apps.tenants.models import Tenant

class Agent(TimeStampedModel):
    # Add tenant field
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='agents',
        help_text="Tenant this agent belongs to",
        db_index=True
    )

    # Existing fields...
    name = models.CharField(...)

    def save(self, *args, **kwargs):
        """Auto-set tenant from current schema context"""
        if not self.tenant_id:
            schema_name = connection.schema_name
            if schema_name != 'public':
                self.tenant = Tenant.objects.get(schema_name=schema_name)
        super().save(*args, **kwargs)
```

#### Fix 2: Fix UserViewSet Data Leak

**File:** `cloud_backend/apps/users/views.py`

```python
from django.db import connection
from apps.tenants.models import TenantMembership, Tenant

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        """Filter users by current tenant membership"""
        # Get current tenant from schema
        if connection.schema_name == 'public':
            # Superadmin in public schema can see all users
            if self.request.user.is_superuser:
                return User.objects.all()
            return User.objects.none()

        # Get tenant from schema
        tenant = Tenant.objects.get(schema_name=connection.schema_name)

        # Filter users who are members of this tenant
        user_ids = TenantMembership.objects.filter(
            tenant=tenant,
            is_active=True
        ).values_list('user_id', flat=True)

        return User.objects.filter(id__in=user_ids)
```

#### Fix 3: Add Tenant Filtering to All ViewSets

**Add to ALL ViewSets in:**
- `cloud_backend/apps/agents/views.py`
- `cloud_backend/apps/tools/views.py`
- `cloud_backend/apps/mcp/views.py`
- `cloud_backend/apps/groups/views.py`
- `cloud_backend/apps/messages/views.py`

```python
from django.db import connection

class AgentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AgentSerializer

    def get_queryset(self):
        """Explicit tenant scoping (defense-in-depth)"""
        # Prevent access from public schema
        if connection.schema_name == 'public':
            return self.queryset.none()

        # Get current tenant
        tenant = Tenant.objects.get(schema_name=connection.schema_name)

        # Filter by tenant (explicit check even though middleware handles it)
        return Agent.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        """Auto-set tenant on create"""
        tenant = Tenant.objects.get(schema_name=connection.schema_name)
        serializer.save(
            tenant=tenant,
            created_by=self.request.user.id
        )
```

#### Fix 4: Update Serializers to Include Tenant ID

**Update ALL serializers to include tenant_id in response:**

```python
class AgentSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)

    class Meta:
        model = Agent
        fields = [
            'id',
            'tenant_id',  # ← CRITICAL for local backend sync
            'name',
            'description',
            # ... other fields
        ]
        read_only_fields = ['id', 'tenant_id', 'created_at', 'updated_at']
```

#### Fix 5: Secure Django Admin

**Add tenant filtering to ALL admin classes:**

```python
from django.db import connection
from apps.tenants.models import Tenant

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'llm_provider', 'created_by', 'is_active')

    def get_queryset(self, request):
        """Filter by current tenant"""
        qs = super().get_queryset(request)

        # Superuser in public schema can see all
        if connection.schema_name == 'public' and request.user.is_superuser:
            return qs

        # Filter by current tenant
        if connection.schema_name != 'public':
            tenant = Tenant.objects.get(schema_name=connection.schema_name)
            return qs.filter(tenant=tenant)

        return qs.none()

    def save_model(self, request, obj, form, change):
        """Auto-set tenant on create"""
        if not change:  # Creating new object
            tenant = Tenant.objects.get(schema_name=connection.schema_name)
            obj.tenant = tenant
        super().save_model(request, obj, form, change)
```

### Priority 2: Synchronization

#### Fix 6: Update Cloud API Authentication Response

**File:** `cloud_backend/apps/users/views_auth.py`

**Ensure login response includes tenant_id:**
```python
def login(request):
    # ... existing auth logic ...

    # Get current tenant
    tenant = user.tenant  # Property reads from connection.schema_name

    return Response({
        'access_token': str(access_token),
        'refresh_token': str(refresh_token),
        'token_type': 'Bearer',
        'expires_in': 3600,
        'user_id': str(user.id),
        'tenant_id': str(tenant.id),  # ← CRITICAL for local backend
        'user_role': user.role,
    })
```

## LOCAL BACKEND EXPECTATIONS

**From:** `local_backend/src/api/cloud_client.py`

The local backend expects:

### 1. AuthToken with tenant_id
```python
@dataclass
class AuthToken:
    tenant_id: Optional[str] = None  # ← MUST be populated
```

### 2. All API responses include tenant context
```python
async def fetch_agents(self) -> List[Dict[str, Any]]:
    """
    Expected response format:
    [
        {
            "id": "agent-uuid",
            "tenant_id": "tenant-uuid",  # ← MUST be present
            "name": "Research Assistant",
            "llm_provider": "anthropic",
            ...
        }
    ]
    """
```

### 3. Tenant-scoped data fetching
```python
async def sync_all_tenant_data(self) -> Dict[str, Any]:
    """
    Fetches ALL tenant data:
    - Agents (filtered by tenant)
    - Tools (filtered by tenant)
    - MCP servers (filtered by tenant)
    - Groups (filtered by tenant)
    - Users (filtered by TenantMembership)

    Cloud backend MUST filter by tenant automatically!
    """
```

## MIGRATION STRATEGY

### Step 1: Add Tenant Fields to Models

1. Add `tenant` ForeignKey to each TENANT_APP model
2. Create migrations: `python manage.py makemigrations`
3. **Before running migrate:** Populate tenant field for existing data
4. Run migrations: `python manage.py migrate`

### Step 2: Update ViewSets

1. Add `get_queryset()` with tenant filtering to ALL ViewSets
2. Add `perform_create()` to auto-set tenant on create
3. Test each endpoint with authenticated requests

### Step 3: Update Serializers

1. Add `tenant_id` field to ALL serializers (read-only)
2. Verify JSON responses include tenant_id

### Step 4: Secure Admin

1. Add `get_queryset()` tenant filtering to ALL admin classes
2. Add `save_model()` to auto-set tenant on create
3. Test admin panel in different tenant contexts

### Step 5: Update Authentication

1. Ensure login response includes tenant_id
2. Ensure JWT token payload includes tenant context
3. Test local backend can extract tenant from auth

## VERIFICATION CHECKLIST

After fixes:

- [ ] Agent model has `tenant` field
- [ ] Tool model has `tenant` field
- [ ] MCPServer model has `tenant` field
- [ ] Group model has `tenant` field (user confirmed: "group object also come under tenant")
- [ ] Message model has `tenant` field
- [ ] Document model has `tenant` field
- [ ] All ViewSets filter by tenant in `get_queryset()`
- [ ] All ViewSets set tenant in `perform_create()`
- [ ] All Serializers include `tenant_id` in response
- [ ] UserViewSet filters by TenantMembership (security fix)
- [ ] All Admin classes filter by tenant
- [ ] Login response includes `tenant_id`
- [ ] Local backend can sync all tenant data
- [ ] No cross-tenant data leaks in API
- [ ] No cross-tenant data leaks in Admin

## SECURITY IMPLICATIONS

**Current state:** ❌ **PRODUCTION UNSAFE**
- Cross-tenant data exposure in UserViewSet
- Admin can view/edit wrong tenant's data
- No explicit tenant checks (relies only on middleware)

**After fixes:** ✅ **PRODUCTION READY**
- All entities have explicit tenant identification
- Defense-in-depth with explicit tenant filtering
- Admin restricted to current tenant
- Local backend gets tenant_id in all responses
- Full sync compatibility with local backend

## ESTIMATED EFFORT

- **Models + Migrations:** 2 hours
- **ViewSets:** 1 hour
- **Serializers:** 1 hour
- **Admin classes:** 1 hour
- **Authentication:** 30 minutes
- **Testing:** 2 hours
- **Total:** ~7-8 hours

## CRITICAL NOTES

1. **"tenant is base identifier"** - User is correct, every entity needs tenant
2. **"cloud is mandatory auth middleware"** - Cloud is auth gateway for local
3. **Security breach** - Current admin/API allows cross-tenant access
4. **Groups are tenant-specific** - User confirmed: "group object also come under tenant"
5. **Local backend relies on tenant_id** - Must be in ALL JSON responses

---

**STATUS:** ❌ CRITICAL FIXES REQUIRED BEFORE PRODUCTION
**NEXT ACTION:** Implement fixes in order of priority
