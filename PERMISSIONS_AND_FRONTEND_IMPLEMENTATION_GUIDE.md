# Permissions and Frontend Implementation Guide

## Status: Permission Model Created ✅

The Permission model has been created in `/cloud_backend/apps/core/models.py`.

**What's Done:**
- ✅ Permission model with tenant isolation
- ✅ Supports both users and agents as subjects
- ✅ CRUD + Execute actions
- ✅ Resource-specific or global permissions

---

## Remaining Implementation Tasks

### TASK 1: Create Permission Serializer and ViewSet ⏳

#### File: `/cloud_backend/apps/core/serializers.py` (CREATE)

```python
"""
Core Serializers
"""

from rest_framework import serializers
from .models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Permission serializer for API.

    Admins use this to grant/revoke permissions for users and agents.
    """

    class Meta:
        model = Permission
        fields = [
            'id',
            'tenant',
            'subject_type',
            'subject_id',
            'resource_type',
            'resource_id',
            'can_view',
            'can_create',
            'can_update',
            'can_delete',
            'can_execute',
            'granted_by',
            'reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate permission data"""
        # Only admins can create permissions
        request = self.context.get('request')
        if request and not request.user.is_admin():
            raise serializers.ValidationError(
                "Only admins can create/modify permissions"
            )

        # Validate resource_id exists if specified
        resource_type = data.get('resource_type')
        resource_id = data.get('resource_id')

        if resource_id:
            # TODO: Validate resource_id exists based on resource_type
            pass

        return data
```

#### File: `/cloud_backend/apps/core/views.py` (CREATE)

```python
"""
Core ViewSets
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from apps.tenants.models import Tenant
from .models import Permission
from .serializers import PermissionSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Permission CRUD.

    Only admins can create/update/delete permissions.
    Users can view their own permissions.
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter permissions by tenant"""
        schema_name = connection.schema_name

        if schema_name == 'public':
            return Permission.objects.none()

        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return Permission.objects.none()

        queryset = Permission.objects.filter(tenant=tenant)

        # Non-admins can only see their own permissions
        if not self.request.user.is_admin():
            queryset = queryset.filter(
                subject_type='user',
                subject_id=self.request.user.id
            )

        return queryset

    def perform_create(self, serializer):
        """Auto-set tenant and granted_by"""
        schema_name = connection.schema_name
        tenant = Tenant.objects.get(schema_name=schema_name)
        serializer.save(
            tenant=tenant,
            granted_by=self.request.user.id
        )
```

#### File: `/cloud_backend/config/urls.py` (UPDATE)

Add to urlpatterns:
```python
from apps.core.views import PermissionViewSet

router.register(r'permissions', PermissionViewSet, basename='permission')
```

---

### TASK 2: Create Permission Enforcement Mixins ⏳

#### File: `/cloud_backend/apps/core/mixins.py` (CREATE)

```python
"""
ViewSet Mixins for Permission and License Enforcement
"""

from rest_framework.exceptions import PermissionDenied
from django.db import connection
from apps.tenants.models import Tenant
from .models import Permission


class PermissionFilteredViewSet:
    """
    Mixin to enforce fine-grained permissions on ViewSets.

    Only shows resources user has permission to access.
    Only allows actions user has permission to perform.

    Define `permission_resource_type` in ViewSet.
    """

    permission_resource_type = None  # Override in ViewSet (e.g., 'agent')

    def get_queryset(self):
        """Filter by user permissions"""
        queryset = super().get_queryset()
        user = self.request.user

        # Admin sees all
        if user.is_admin():
            return queryset

        # Non-admin: filter by permissions
        if not self.permission_resource_type:
            return queryset  # No permission filtering

        # Get resources user has view permission for
        schema_name = connection.schema_name
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            return queryset.none()

        # Get permissions for this user and resource type
        permissions = Permission.objects.filter(
            tenant=tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=self.permission_resource_type,
            can_view=True
        )

        # Get allowed resource IDs
        allowed_ids = []
        for perm in permissions:
            if perm.resource_id is None:
                # Global permission - return all
                return queryset
            allowed_ids.append(perm.resource_id)

        # Filter queryset
        if not allowed_ids:
            return queryset.none()

        return queryset.filter(id__in=allowed_ids)

    def check_permission(self, action: str, obj=None):
        """
        Check if user has permission for action.

        Args:
            action: 'create', 'update', 'delete', 'execute'
            obj: Object being acted upon (for update/delete)
        """
        user = self.request.user

        # Admin can do anything
        if user.is_admin():
            return True

        if not self.permission_resource_type:
            raise PermissionDenied("Permission checking not configured")

        # Map action to permission field
        permission_map = {
            'create': 'can_create',
            'update': 'can_update',
            'delete': 'can_delete',
            'execute': 'can_execute'
        }

        if action not in permission_map:
            raise PermissionDenied(f"Unknown action: {action}")

        # Get tenant
        schema_name = connection.schema_name
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            raise PermissionDenied("Tenant not found")

        # Check permission
        resource_id = obj.id if obj else None

        has_permission = Permission.objects.filter(
            tenant=tenant,
            subject_type='user',
            subject_id=user.id,
            resource_type=self.permission_resource_type,
            resource_id__in=[resource_id, None],  # Specific or global
            **{permission_map[action]: True}
        ).exists()

        if not has_permission:
            raise PermissionDenied(
                f"You don't have permission to {action} this {self.permission_resource_type}"
            )

        return True

    def perform_create(self, serializer):
        """Check create permission before creating"""
        self.check_permission('create')
        super().perform_create(serializer)

    def perform_update(self, serializer):
        """Check update permission before updating"""
        self.check_permission('update', obj=self.get_object())
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        """Check delete permission before deleting"""
        self.check_permission('delete', obj=instance)
        super().perform_destroy(instance)


class LicenseEnforcedViewSet:
    """
    Mixin to enforce license limits on resource creation.

    Define `license_limit_key` in ViewSet to specify which limit to check.
    """

    license_limit_key = None  # Override in ViewSet (e.g., 'max_agents')

    def check_license_limit(self):
        """Check if tenant has reached license limit"""
        if not self.license_limit_key:
            return  # No limit to check

        schema_name = connection.schema_name
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            raise PermissionDenied("Tenant not found")

        # Get current count
        current_count = self.get_queryset().count()

        # Check limit
        limit = tenant.get_limit(self.license_limit_key)
        if limit == -1:
            return  # Unlimited

        if current_count >= limit:
            raise PermissionDenied(
                f"License limit reached: {self.license_limit_key.replace('max_', '').replace('_', ' ').title()} "
                f"(max: {limit}, current: {current_count}). "
                f"Please upgrade your plan to create more."
            )

    def perform_create(self, serializer):
        """Check license limit before creating"""
        self.check_license_limit()
        super().perform_create(serializer)
```

---

### TASK 3: Apply Mixins to ViewSets ⏳

Update ALL resource ViewSets to use both mixins:

#### Example: `/cloud_backend/apps/agents/views.py`

```python
from apps.core.mixins import PermissionFilteredViewSet, LicenseEnforcedViewSet

class AgentViewSet(
    PermissionFilteredViewSet,      # Permission enforcement
    LicenseEnforcedViewSet,          # License limit enforcement
    viewsets.ModelViewSet
):
    """ViewSet for Agent CRUD with permission and license enforcement"""

    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    # Permission filtering
    permission_resource_type = 'agent'

    # License enforcement
    license_limit_key = 'max_agents'

    # ... rest of ViewSet methods
```

Apply to:
- ✅ `/cloud_backend/apps/agents/views.py` → `permission_resource_type='agent'`, `license_limit_key='max_agents'`
- ✅ `/cloud_backend/apps/tools/views.py` → `permission_resource_type='tool'`, `license_limit_key='max_tools'`
- ✅ `/cloud_backend/apps/mcp/views.py` → `permission_resource_type='mcp_server'`, `license_limit_key='max_mcp_servers'`
- ✅ `/cloud_backend/apps/groups/views.py` → `permission_resource_type='group'`, `license_limit_key='max_groups'`
- ✅ `/cloud_backend/apps/documents/views.py` → `permission_resource_type='document'`, `license_limit_key='max_documents'`

---

### TASK 4: Create Django Migrations ⏳

```bash
cd /home/user/Agentverse/cloud_backend
python manage.py makemigrations core
python manage.py migrate --fake-initial
```

**Expected Migration:**
- Creates `core_permission` table
- Adds indexes
- Adds unique_together constraint

---

### TASK 5: Update Frontend WebSocket Clients with device_id ⏳

#### File: `/local_frontend/src/lib/utils/deviceId.ts` (CREATE)

```typescript
/**
 * Device ID Management
 *
 * Generates and persists unique device ID for WebSocket routing.
 */

const DEVICE_ID_KEY = 'agentverse_device_id';

export function getOrCreateDeviceId(): string {
  // Try to get existing device ID
  let deviceId = localStorage.getItem(DEVICE_ID_KEY);

  if (!deviceId) {
    // Generate new device ID
    deviceId = crypto.randomUUID();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
    console.log('Generated new device ID:', deviceId);
  }

  return deviceId;
}

export function getDeviceId(): string | null {
  return localStorage.getItem(DEVICE_ID_KEY);
}

export function clearDeviceId(): void {
  localStorage.removeItem(DEVICE_ID_KEY);
}
```

#### File: `/local_frontend/src/lib/cloud/chatWebSocket.ts` (UPDATE)

```typescript
import { getOrCreateDeviceId } from '../utils/deviceId';

private createConnection(): void {
  const token = cloudAuth.getAccessToken();
  if (!token) {
    console.error('Cannot connect to chat: No access token');
    return;
  }

  const config = cloudConfig();
  const deviceId = getOrCreateDeviceId();  // ← ADD THIS
  const wsUrl = `${config.wsUrl}/ws/messages/${this.groupId}/?token=${token}&device_id=${deviceId}`;  // ← UPDATE THIS

  // ... rest of method
}
```

#### File: `/local_frontend/src/lib/cloud/syncWebSocket.ts` (UPDATE)

```typescript
import { getOrCreateDeviceId } from '../utils/deviceId';

connect(): void {
  const token = cloudAuth.getAccessToken();
  if (!token) {
    console.error('Cannot connect to sync: No access token');
    return;
  }

  const config = cloudConfig();
  const deviceId = getOrCreateDeviceId();  // ← ADD THIS
  const wsUrl = `${config.wsUrl}/ws/sync/?token=${token}&device_id=${deviceId}`;  // ← UPDATE THIS

  // ... rest of method
}
```

#### Add Delete Event Handlers to `syncWebSocket.ts`:

```typescript
export type SyncEventType =
  | 'agent_updated'
  | 'agent_deleted'      // ← ADD
  | 'tool_updated'
  | 'tool_deleted'       // ← ADD
  | 'mcp_updated'
  | 'mcp_deleted'        // ← ADD
  | 'group_updated'
  | 'group_deleted';     // ← ADD

export interface SyncEvent {
  type: SyncEventType;
  agent?: any;
  agent_id?: string;     // ← ADD for delete events
  agent_name?: string;   // ← ADD
  tool?: any;
  tool_id?: string;      // ← ADD for delete events
  tool_name?: string;    // ← ADD
  mcp_server?: any;
  mcp_id?: string;       // ← ADD for delete events
  mcp_name?: string;     // ← ADD
  group?: any;
  group_id?: string;     // ← ADD for delete events
  group_name?: string;   // ← ADD
}
```

---

### TASK 6: Make AdminView Functional ⏳

#### File: `/local_frontend/src/lib/cloud/api.ts` (CREATE)

```typescript
/**
 * Cloud API Service
 *
 * Real API calls for admin operations.
 */

import { cloudConfig } from './config';
import { cloudAuth } from './auth';

class CloudAPIService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = cloudAuth.getAccessToken();
    const config = cloudConfig();
    const url = `${config.baseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `Request failed with status ${response.status}`
      }));
      throw new Error(error.detail || error.message || 'Request failed');
    }

    return response.json();
  }

  // User Management
  async getUsers() {
    return this.request('/api/users/');
  }

  async createUser(userData: any) {
    return this.request('/api/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId: string, userData: any) {
    return this.request(`/api/users/${userId}/`, {
      method: 'PATCH',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId: string) {
    return this.request(`/api/users/${userId}/`, {
      method: 'DELETE',
    });
  }

  // Group Management
  async getGroups() {
    return this.request('/api/groups/');
  }

  async createGroup(groupData: any) {
    return this.request('/api/groups/', {
      method: 'POST',
      body: JSON.stringify(groupData),
    });
  }

  async updateGroup(groupId: string, groupData: any) {
    return this.request(`/api/groups/${groupId}/`, {
      method: 'PATCH',
      body: JSON.stringify(groupData),
    });
  }

  async deleteGroup(groupId: string) {
    return this.request(`/api/groups/${groupId}/`, {
      method: 'DELETE',
    });
  }

  // Agent Management
  async getAgents() {
    return this.request('/api/agents/');
  }

  async createAgent(agentData: any) {
    return this.request('/api/agents/', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async updateAgent(agentId: string, agentData: any) {
    return this.request(`/api/agents/${agentId}/`, {
      method: 'PATCH',
      body: JSON.stringify(agentData),
    });
  }

  async deleteAgent(agentId: string) {
    return this.request(`/api/agents/${agentId}/`, {
      method: 'DELETE',
    });
  }

  // Tool Management
  async getTools() {
    return this.request('/api/tools/');
  }

  async createTool(toolData: any) {
    return this.request('/api/tools/', {
      method: 'POST',
      body: JSON.stringify(toolData),
    });
  }

  async updateTool(toolId: string, toolData: any) {
    return this.request(`/api/tools/${toolId}/`, {
      method: 'PATCH',
      body: JSON.stringify(toolData),
    });
  }

  async deleteTool(toolId: string) {
    return this.request(`/api/tools/${toolId}/`, {
      method: 'DELETE',
    });
  }

  // MCP Management
  async getMCPServers() {
    return this.request('/api/mcp/');
  }

  async createMCPServer(mcpData: any) {
    return this.request('/api/mcp/', {
      method: 'POST',
      body: JSON.stringify(mcpData),
    });
  }

  async updateMCPServer(mcpId: string, mcpData: any) {
    return this.request(`/api/mcp/${mcpId}/`, {
      method: 'PATCH',
      body: JSON.stringify(mcpData),
    });
  }

  async deleteMCPServer(mcpId: string) {
    return this.request(`/api/mcp/${mcpId}/`, {
      method: 'DELETE',
    });
  }

  // Permission Management
  async getPermissions() {
    return this.request('/api/permissions/');
  }

  async createPermission(permissionData: any) {
    return this.request('/api/permissions/', {
      method: 'POST',
      body: JSON.stringify(permissionData),
    });
  }

  async updatePermission(permissionId: string, permissionData: any) {
    return this.request(`/api/permissions/${permissionId}/`, {
      method: 'PATCH',
      body: JSON.stringify(permissionData),
    });
  }

  async deletePermission(permissionId: string) {
    return this.request(`/api/permissions/${permissionId}/`, {
      method: 'DELETE',
    });
  }
}

// Singleton
export const cloudAPI = new CloudAPIService();
```

#### File: `/local_frontend/src/components/views/AdminView.tsx` (UPDATE)

Replace mock data with real API calls:

```typescript
import { useEffect, useState } from 'react';
import { cloudAPI } from '../../lib/cloud/api';
import { syncWebSocket } from '../../lib/cloud/syncWebSocket';

export const AdminView: React.FC<AdminViewProps> = ({ adminTab, onTabChange }) => {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = syncWebSocket.onSync((event) => {
      if (event.type === 'agent_updated' && event.agent) {
        setAgents(prev => {
          const index = prev.findIndex(a => a.id === event.agent.id);
          if (index >= 0) {
            // Update existing
            const newAgents = [...prev];
            newAgents[index] = event.agent;
            return newAgents;
          } else {
            // Add new
            return [...prev, event.agent];
          }
        });
      } else if (event.type === 'agent_deleted' && event.agent_id) {
        setAgents(prev => prev.filter(a => a.id !== event.agent_id));
      }

      // Similar handlers for tools, MCPs, groups...
    });

    return unsubscribe;
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);

    try {
      const [usersData, groupsData, agentsData] = await Promise.all([
        cloudAPI.getUsers(),
        cloudAPI.getGroups(),
        cloudAPI.getAgents(),
      ]);

      setUsers(usersData);
      setGroups(groupsData);
      setAgents(agentsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAgent(agentData: any) {
    try {
      await cloudAPI.createAgent(agentData);
      // WebSocket will update the UI
    } catch (err: any) {
      alert(err.message || 'Failed to create agent');
    }
  }

  // ... render UI with real data
}
```

---

### TASK 7: Integrate Permission Checks into UI ⏳

#### File: `/local_frontend/src/lib/stores/auth.ts` (UPDATE)

```typescript
// Replace mock login with real cloudAuth
import { cloudAuth } from '../cloud/auth';

login: async (email: string, password: string) => {
  try {
    // Real login
    const tokens = await cloudAuth.login({ email, password });
    const profile = await cloudAuth.me();

    // Fetch user's permissions
    const permissions = await cloudAPI.getPermissions();

    set({
      isAuthenticated: true,
      currentUser: {
        id: profile.id,
        name: profile.name,
        email: profile.email,
        role: profile.role,
        accountType: profile.role === 'admin' ? 'enterprise' : 'individual',
        joinedAt: new Date().toISOString(),
      },
      userPermissions: permissions,  // Store permissions
    });
  } catch (error: any) {
    throw new Error(error.message || 'Login failed');
  }
},

// Add permission check helpers
canCreate: (resourceType: string) => {
  const { currentUser, userPermissions } = get();

  // Admin can do anything
  if (currentUser?.role === 'admin') return true;

  // Check permissions
  return userPermissions.some(p =>
    p.subject_type === 'user' &&
    p.subject_id === currentUser?.id &&
    p.resource_type === resourceType &&
    p.can_create
  );
},

canUpdate: (resourceType: string, resourceId?: string) => {
  const { currentUser, userPermissions } = get();
  if (currentUser?.role === 'admin') return true;

  return userPermissions.some(p =>
    p.subject_type === 'user' &&
    p.subject_id === currentUser?.id &&
    p.resource_type === resourceType &&
    (p.resource_id === resourceId || p.resource_id === null) &&
    p.can_update
  );
},

canDelete: (resourceType: string, resourceId?: string) => {
  const { currentUser, userPermissions } = get();
  if (currentUser?.role === 'admin') return true;

  return userPermissions.some(p =>
    p.subject_type === 'user' &&
    p.subject_id === currentUser?.id &&
    p.resource_type === resourceType &&
    (p.resource_id === resourceId || p.resource_id === null) &&
    p.can_delete
  );
},
```

#### Update AdminView to use permission checks:

```typescript
import { useAuthStore } from '../../lib/stores/auth';

export const AdminView: React.FC<AdminViewProps> = ({ adminTab }) => {
  const { canCreate, canUpdate, canDelete } = useAuthStore();

  return (
    <>
      {canCreate('agent') && (
        <button onClick={handleCreateAgent}>
          Create Agent
        </button>
      )}

      {canUpdate('agent', agent.id) && (
        <button onClick={() => handleEditAgent(agent)}>
          Edit
        </button>
      )}

      {canDelete('agent', agent.id) && (
        <button onClick={() => handleDeleteAgent(agent.id)}>
          Delete
        </button>
      )}

      {!canCreate('agent') && (
        <div className="text-slate-500">
          You don't have permission to create agents. Contact your admin.
        </div>
      )}
    </>
  );
};
```

---

## Implementation Checklist

### Backend (Cloud):
- ✅ Permission model created
- ⏳ Permission serializer
- ⏳ Permission ViewSet
- ⏳ PermissionFilteredViewSet mixin
- ⏳ LicenseEnforcedViewSet mixin
- ⏳ Apply mixins to all ViewSets
- ⏳ Create migrations
- ⏳ Test permission enforcement

### Frontend (Local):
- ⏳ Create deviceId.ts utility
- ⏳ Update chatWebSocket.ts with device_id
- ⏳ Update syncWebSocket.ts with device_id and delete events
- ⏳ Create cloudAPI.ts service
- ⏳ Update AdminView to use real API
- ⏳ Update auth store to use cloudAuth
- ⏳ Add permission check helpers
- ⏳ Update UI to show/hide based on permissions

### Testing:
- ⏳ Test admin can create/update/delete all resources
- ⏳ Test regular user cannot create/update/delete without permission
- ⏳ Test WebSocket device routing
- ⏳ Test license limits are enforced
- ⏳ Test real-time sync across multiple devices

---

## Priority Order

1. **CRITICAL - Backend Permission Enforcement:**
   - Create serializer and ViewSet
   - Create mixins
   - Apply to all ViewSets
   - Run migrations

2. **HIGH - Frontend WebSocket:**
   - Add device_id to WebSocket URLs
   - Add delete event handlers

3. **HIGH - Frontend Admin Functionality:**
   - Create cloudAPI service
   - Update AdminView to use real API
   - Update auth store

4. **MEDIUM - UI Permission Checks:**
   - Add permission helpers to auth store
   - Show/hide UI based on permissions

---

## Next Steps

Run this implementation guide step by step:

```bash
# 1. Create files in order
# 2. Test each component
# 3. Run migrations
# 4. Test full flow: admin creates resource → WebSocket broadcasts → all users see update
```

The Permission model is already created and committed. Continue with Task 1 (serializer) to complete the implementation.
