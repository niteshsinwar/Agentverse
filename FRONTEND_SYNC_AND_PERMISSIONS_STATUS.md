# Frontend Sync and Permissions Status

## Summary

This document addresses the current state of frontend synchronization, authentication, admin functionality, and permission systems in AgentVerse.

---

## ✅ What's Implemented (Backend)

### 1. Complete WebSocket Routing ✅

**Cloud Backend:**
- ✅ ExecutionContextMiddleware extracts device_id and execution context
- ✅ MessageViewSet broadcasts to WebSocket on create/update/delete
- ✅ WebSocket consumers track device_id and join appropriate channels
- ✅ Signal handlers broadcast CRUD operations (Agent, Tool, MCP, Group)
- ✅ Tenant isolation enforced at WebSocket level
- ✅ Messages broadcast to `messages_{group_id}` (all group members)
- ✅ CRUD updates broadcast to `sync_{tenant_id}` (all tenant members)

**Local Backend:**
- ✅ Device manager generates and persists device IDs
- ✅ Execution context tracking through agent chains
- ✅ Cloud client passes device_id and execution headers

### 2. Cloud Authentication ✅

**Backend (Django):**
- ✅ JWT authentication (Simple JWT)
- ✅ User model with tenant relationships
- ✅ Login/logout/refresh endpoints
- ✅ User profile endpoint
- ✅ Multi-tenancy with django-tenants

**Local Frontend:**
- ✅ CloudAuthService (`lib/cloud/auth.ts`) - **FUNCTIONAL**
  - ✅ Real login with email/password
  - ✅ JWT token storage (localStorage)
  - ✅ Token refresh mechanism
  - ✅ User profile fetching (`/auth/me`)
  - ✅ Logout functionality

### 3. Real-Time Synchronization ✅

**Local Frontend WebSocket Clients:**
- ✅ `chatWebSocket.ts` - **FUNCTIONAL** (connects to messages WebSocket)
- ✅ `syncWebSocket.ts` - **FUNCTIONAL** (connects to sync WebSocket)
- ⚠️ **MISSING**: device_id not passed in WebSocket URL
- ⚠️ **MISSING**: Delete event handlers (agent_deleted, tool_deleted, etc.)

---

## ⚠️ What's NOT Implemented (Frontend)

### 1. Local Frontend WebSocket - Needs Updates ⚠️

**Current State:**
```typescript
// chatWebSocket.ts (line 66)
const wsUrl = `${config.wsUrl}/ws/messages/${this.groupId}/?token=${token}`;
```

**Needs to be:**
```typescript
const deviceId = getDeviceId(); // Get from localStorage or generate
const wsUrl = `${config.wsUrl}/ws/messages/${this.groupId}/?token=${token}&device_id=${deviceId}`;
```

**Missing Event Handlers:**
```typescript
// syncWebSocket.ts needs to handle:
export type SyncEventType =
  | 'agent_updated'
  | 'agent_deleted'  // ← MISSING
  | 'tool_updated'
  | 'tool_deleted'   // ← MISSING
  | 'mcp_updated'
  | 'mcp_deleted'    // ← MISSING
  | 'group_updated'
  | 'group_deleted'; // ← MISSING
```

### 2. AdminView - NOT FUNCTIONAL ❌

**Current State:**
```typescript
// AdminView.tsx (line 9)
/**
 * NON-FUNCTIONAL: UI demonstration only
 */
```

**What's Mocked:**
- User management (mockUsers array)
- Group management (mockGroups array)
- Resource permissions (mockResources array)
- All CRUD operations are UI-only

**What Needs to be Implemented:**
1. Real API calls to cloud backend for users, groups, agents, tools, MCPs
2. Permission checks before showing create/edit/delete buttons
3. Integration with cloudAuth for role-based UI rendering
4. Real-time updates via WebSocket when admin makes changes

### 3. Permission System - NOT IMPLEMENTED ❌

**Current State:**
- ❌ No permission model in cloud backend
- ❌ No permission checks in ViewSets
- ❌ No permission serialization
- ❌ No permission enforcement in frontend

**What User Requested:**

> "Only admin able to create, update, delete any group, mcp tool, agent, add or remove humans. Other users have limited access governed by their permission set. Permission set object apply both on human and agent in similar way."

**What Needs to be Implemented:**

#### Backend (Django):

1. **Permission Model:**
```python
class Permission(models.Model):
    """
    Permission set for users and agents.

    Defines what actions a user/agent can perform on resources.
    """
    tenant = ForeignKey('tenants.Tenant')

    # Subject (who has the permission)
    subject_type = CharField(choices=[('user', 'User'), ('agent', 'Agent')])
    subject_id = UUIDField()

    # Resource (what the permission applies to)
    resource_type = CharField(choices=[
        ('agent', 'Agent'),
        ('tool', 'Tool'),
        ('mcp_server', 'MCP Server'),
        ('group', 'Group'),
        ('message', 'Message')
    ])
    resource_id = UUIDField(null=True, blank=True)  # Null = all resources of type

    # Actions
    can_view = BooleanField(default=True)
    can_create = BooleanField(default=False)
    can_update = BooleanField(default=False)
    can_delete = BooleanField(default=False)
    can_execute = BooleanField(default=False)  # For agents/tools

    class Meta:
        unique_together = [
            ['tenant', 'subject_type', 'subject_id', 'resource_type', 'resource_id']
        ]
```

2. **Permission Mixin for ViewSets:**
```python
class PermissionFilteredViewSet:
    """
    Mixin to enforce permissions on ViewSets.

    Only shows resources user has permission to access.
    Only allows actions user has permission to perform.
    """

    def get_queryset(self):
        """Filter by user permissions"""
        user = self.request.user

        # Admin sees all
        if user.is_admin():
            return super().get_queryset()

        # Non-admin: filter by permissions
        resource_type = self.get_resource_type()
        allowed_ids = Permission.objects.filter(
            tenant=user.tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=resource_type,
            can_view=True
        ).values_list('resource_id', flat=True)

        return super().get_queryset().filter(id__in=allowed_ids)

    def check_permission(self, action: str):
        """Check if user has permission for action"""
        user = self.request.user

        # Admin can do anything
        if user.is_admin():
            return True

        # Map action to permission field
        permission_map = {
            'create': 'can_create',
            'update': 'can_update',
            'delete': 'can_delete',
            'execute': 'can_execute'
        }

        if action not in permission_map:
            raise PermissionDenied(f"Unknown action: {action}")

        # Check permission
        resource_type = self.get_resource_type()
        resource_id = self.get_object().id if action != 'create' else None

        has_permission = Permission.objects.filter(
            tenant=user.tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=resource_type,
            resource_id__in=[resource_id, None],  # Specific or global
            **{permission_map[action]: True}
        ).exists()

        if not has_permission:
            raise PermissionDenied(f"You don't have permission to {action} this resource")
```

3. **Apply to All ViewSets:**
```python
class AgentViewSet(PermissionFilteredViewSet, viewsets.ModelViewSet):
    def perform_create(self, serializer):
        self.check_permission('create')
        # ... rest of create logic

    def perform_update(self, serializer):
        self.check_permission('update')
        # ... rest of update logic

    def perform_destroy(self, instance):
        self.check_permission('delete')
        # ... rest of delete logic
```

#### Frontend:

1. **Update AdminView to use Real API:**
```typescript
// Instead of mockUsers
const { data: users } = useQuery('/api/users/');
const { data: groups } = useQuery('/api/groups/');
const { data: agents } = useQuery('/api/agents/');

// Instead of mock CRUD
const createUser = useMutation((userData) =>
  api.post('/api/users/', userData)
);
```

2. **Permission-Based UI Rendering:**
```typescript
const { currentUser } = useAuthStore();
const isAdmin = currentUser?.role === 'admin';

// Only show admin features to admins
{isAdmin && (
  <>
    <CreateButton onClick={handleCreate} />
    <EditButton onClick={handleEdit} />
    <DeleteButton onClick={handleDelete} />
  </>
)}

// Non-admins see read-only view
{!isAdmin && (
  <div>Read-only access</div>
)}
```

3. **WebSocket Device ID:**
```typescript
// Add to localStorage on first run
const getOrCreateDeviceId = () => {
  let deviceId = localStorage.getItem('device_id');
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem('device_id', deviceId);
  }
  return deviceId;
};

// Use in WebSocket connections
const deviceId = getOrCreateDeviceId();
const wsUrl = `${config.wsUrl}/ws/messages/${groupId}/?token=${token}&device_id=${deviceId}`;
```

---

## Current Frontend Authentication Flow

### ✅ What Works:

1. **Real Login:**
```typescript
import { cloudAuth } from './lib/cloud/auth';

// User logs in
await cloudAuth.login({ email: 'user@example.com', password: 'password' });

// Get user profile
const profile = await cloudAuth.me();
// Returns: { id, email, name, role: 'admin' | 'user' }
```

2. **Real WebSocket Connection:**
```typescript
import { chatWebSocket } from './lib/cloud/chatWebSocket';
import { syncWebSocket } from './lib/cloud/syncWebSocket';

// Connect to chat
chatWebSocket.connect(groupId);
chatWebSocket.onMessage((event) => {
  if (event.type === 'message_created') {
    // Update UI with new message
  }
});

// Connect to sync
syncWebSocket.connect();
syncWebSocket.onSync((event) => {
  if (event.type === 'agent_updated') {
    // Update agent cache
  }
});
```

### ⚠️ What's Partially Working:

1. **Auth Store** (`lib/stores/auth.ts`):
   - Has mock login for UI demonstration
   - Should be updated to use cloudAuth instead
   - Has role checks: `isAdmin()`, `canManageUsers()`

```typescript
// Current (mock):
login: (email, password) => { /* mock user creation */ }

// Should be:
login: async (email, password) => {
  const tokens = await cloudAuth.login({ email, password });
  const profile = await cloudAuth.me();
  set({ currentUser: profile, isAuthenticated: true });
}
```

---

## Action Plan

### High Priority (Required for User's Request):

1. **Implement Permission System:**
   - ✅ Create Permission model in cloud backend
   - ✅ Add PermissionFilteredViewSet mixin
   - ✅ Apply to all ViewSets (Agent, Tool, MCP, Group, Message)
   - ✅ Add permission serializers
   - ✅ Create permission CRUD endpoints

2. **Update Local Frontend WebSocket:**
   - ✅ Add device_id to WebSocket URLs
   - ✅ Add delete event handlers to syncWebSocket
   - ✅ Update event types to include _deleted variants

3. **Implement Functional AdminView:**
   - ✅ Replace mock data with real API calls
   - ✅ Integrate with cloudAuth for role checks
   - ✅ Show/hide UI based on permissions
   - ✅ Handle real-time updates via WebSocket

4. **Update Auth Store:**
   - ✅ Replace mock login with cloudAuth.login()
   - ✅ Fetch user profile and permissions on login
   - ✅ Store permissions in auth store
   - ✅ Provide permission check helpers

### Medium Priority:

1. **Permission UI in AdminView:**
   - Show permission editor for users
   - Show permission editor for agents
   - Allow admins to grant/revoke permissions

2. **Permission Enforcement:**
   - Disable create/edit/delete buttons for non-admins
   - Show read-only views for limited users
   - Display permission errors gracefully

### Low Priority:

1. **Analytics:**
   - Query execution chains from message metadata
   - Per-user execution statistics
   - Cost attribution reports

2. **Device Management:**
   - Show active devices per user
   - Allow revoking device access
   - Device presence indicators

---

## Answer to User's Questions

### 1. Is frontend local in complete sync?

**Partially:**
- ✅ WebSocket clients exist and are functional
- ✅ Connect to cloud backend for real-time updates
- ✅ Handle agent/tool/MCP/group updates
- ⚠️ Missing device_id in WebSocket URL
- ⚠️ Missing delete event handlers

**To Complete Sync:**
```typescript
// 1. Add device_id to chatWebSocket.ts
const deviceId = getOrCreateDeviceId();
const wsUrl = `${config.wsUrl}/ws/messages/${groupId}/?token=${token}&device_id=${deviceId}`;

// 2. Add delete handlers to syncWebSocket.ts
export type SyncEventType =
  | 'agent_updated' | 'agent_deleted'
  | 'tool_updated' | 'tool_deleted'
  | 'mcp_updated' | 'mcp_deleted'
  | 'group_updated' | 'group_deleted';
```

### 2. Is auth functional?

**YES:**
- ✅ `CloudAuthService` (`lib/cloud/auth.ts`) is **FULLY FUNCTIONAL**
- ✅ Real login/logout/refresh
- ✅ JWT token management
- ✅ User profile fetching
- ⚠️ Auth Store (`lib/stores/auth.ts`) uses mock login for demo
  - Should be updated to use CloudAuthService

### 3. Is AdminView functional?

**NO:**
- ❌ AdminView is **NON-FUNCTIONAL** (UI demonstration only)
- ❌ Uses mock data (mockUsers, mockGroups, mockResources)
- ❌ No real API calls
- ❌ No permission enforcement

**To Make Functional:**
1. Replace mock data with API calls
2. Integrate with cloudAuth
3. Add permission checks
4. Handle real-time WebSocket updates

---

## Files Requiring Updates

### Cloud Backend (New Files):

```
cloud_backend/apps/core/models.py          # Add Permission model
cloud_backend/apps/core/mixins.py          # Add PermissionFilteredViewSet
cloud_backend/apps/core/serializers.py     # Add PermissionSerializer
cloud_backend/apps/agents/views.py         # Apply PermissionFilteredViewSet
cloud_backend/apps/tools/views.py          # Apply PermissionFilteredViewSet
cloud_backend/apps/mcp/views.py            # Apply PermissionFilteredViewSet
cloud_backend/apps/groups/views.py         # Apply PermissionFilteredViewSet
```

### Local Frontend (Updates):

```
local_frontend/src/lib/cloud/chatWebSocket.ts    # Add device_id
local_frontend/src/lib/cloud/syncWebSocket.ts    # Add device_id, delete events
local_frontend/src/lib/stores/auth.ts             # Use cloudAuth instead of mock
local_frontend/src/components/views/AdminView.tsx # Replace mock with real API
local_frontend/src/lib/utils/deviceId.ts          # New: Device ID manager
local_frontend/src/lib/services/permissions.ts    # New: Permission helpers
```

---

## Summary

| Feature | Backend Status | Frontend Status | Priority |
|---------|---------------|-----------------|----------|
| WebSocket Routing | ✅ Complete | ⚠️ Needs device_id | High |
| Execution Context | ✅ Complete | ⚠️ Needs integration | Medium |
| Authentication | ✅ Complete | ✅ Functional | - |
| Admin View | ✅ APIs exist | ❌ NON-FUNCTIONAL | High |
| Permission System | ❌ NOT IMPLEMENTED | ❌ NOT IMPLEMENTED | **CRITICAL** |
| Real-time Sync | ✅ Complete | ⚠️ Needs delete handlers | High |
| Tenant Isolation | ✅ Complete | ✅ Complete | - |

**Next Steps:**
1. Implement Permission model and enforcement (Backend)
2. Update WebSocket clients with device_id (Frontend)
3. Make AdminView functional with real API calls (Frontend)
4. Integrate permission checks into UI (Frontend)
