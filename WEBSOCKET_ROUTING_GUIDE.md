# WebSocket Routing Implementation Guide

## Overview

This guide documents the complete WebSocket routing implementation for AgentVerse, enabling real-time updates across all users in a tenant-group with proper device identification and execution context tracking.

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. User Action (Local Backend)                                          │
│    - User @mentions agent OR CRUD operation (create/update/delete)      │
│    - Local backend executes agent OR performs CRUD operation            │
│    - Device ID included in request header (X-Device-ID)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. Cloud Backend API (Django)                                           │
│    - ExecutionContextMiddleware extracts headers                        │
│      * X-Device-ID                                                       │
│      * X-Execution-ID (if agent chain)                                  │
│      * X-Initiator-User-ID                                              │
│      * X-Call-Depth                                                      │
│    - MessageViewSet/Signals store data with execution context           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. WebSocket Broadcasting (Channels)                                    │
│    - Messages broadcast to: messages_{group_id}                         │
│    - CRUD updates broadcast to: sync_{tenant_id}                        │
│    - ALL users in group/tenant receive update                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. Frontend Update (All Devices)                                        │
│    - All local frontends in group receive update via WebSocket          │
│    - UI updates in real-time                                            │
│    - Synchronized state across all users                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Components Implemented

### Phase 1: Device Identification ✅

**Local Backend:**
- `/home/user/Agentverse/local_backend/src/core/device_manager.py`
  - Generates unique device ID on first run
  - Persists to `~/.agentverse/device.json`
  - Device ID remains consistent across restarts

- `/home/user/Agentverse/local_backend/src/api/cloud_client.py`
  - Added `device_id` parameter to `__init__`
  - Passes `X-Device-ID` header in all requests
  - Updated `initialize_cloud_client()` to accept device_id

### Phase 2: Execution Context Tracking ✅

**Local Backend:**
- `/home/user/Agentverse/local_backend/src/core/execution_context.py`
  - ExecutionContext dataclass tracks:
    - `execution_id`: Unique chain ID
    - `initiator_user_id`: User who started chain
    - `initiator_device_id`: Device where execution started
    - `group_id`, `tenant_id`: Context
    - `call_stack`: Agent call chain
    - `depth`: Current depth

- `/home/user/Agentverse/local_backend/src/api/cloud_client.py`
  - Added `set_execution_context()` method
  - Updated `_get_headers()` to include:
    - `X-Execution-ID`
    - `X-Initiator-User-ID`
    - `X-Initiator-Device-ID`
    - `X-Call-Depth`

### Phase 3: Cloud Backend WebSocket Routing ✅

**Cloud Backend:**

1. **Middleware** - `/home/user/Agentverse/cloud_backend/apps/core/middleware/execution_context.py`
   - Extracts execution context from request headers
   - Attaches to `request.execution_context`
   - Available to all views

2. **Settings** - `/home/user/Agentverse/cloud_backend/config/settings.py`
   - Added `ExecutionContextMiddleware` to `MIDDLEWARE`
   - Updated `CORS_ALLOW_HEADERS` to include:
     - `x-device-id`
     - `x-execution-id`
     - `x-initiator-user-id`
     - `x-initiator-device-id`
     - `x-call-depth`
     - `x-tenant-id`

3. **Message ViewSet** - `/home/user/Agentverse/cloud_backend/apps/messages/views.py`
   - `perform_create()`: Stores execution context in message metadata
   - `_broadcast_message_created()`: Broadcasts to group WebSocket
   - `_broadcast_message_updated()`: Broadcasts updates
   - `_broadcast_message_deleted()`: Broadcasts deletions

4. **WebSocket Consumers** - `/home/user/Agentverse/cloud_backend/apps/messages/consumers.py`

   **MessageConsumer:**
   - Connects to group-specific channel: `messages_{group_id}`
   - Extracts `device_id` from query params
   - Joins both group channel AND device-specific channel
   - Broadcasts to ALL users in group
   - Handlers: `message_created`, `message_updated`, `message_deleted`

   **CloudSyncConsumer:**
   - Connects to tenant-wide channel: `sync_{tenant_id}`
   - Extracts `device_id` from query params
   - Joins both tenant channel AND device-specific channel
   - Broadcasts CRUD updates to ALL users in tenant
   - Handlers: `agent_updated/deleted`, `tool_updated/deleted`, `mcp_updated/deleted`, `group_updated/deleted`

5. **Signal Handlers** - `/home/user/Agentverse/cloud_backend/apps/core/signals.py`
   - Monitors: Agent, Tool, MCPServer, Group models
   - On save: Broadcasts `{model}_updated` to tenant sync channel
   - On delete: Broadcasts `{model}_deleted` to tenant sync channel
   - Registered via `apps.core.apps.CoreConfig`

---

## WebSocket Connection Flow

### 1. Local Backend Connects to WebSocket

**Message Channel (Group-specific):**
```javascript
// Frontend establishes WebSocket connection
const device_id = getDeviceId(); // From device_manager
const ws = new WebSocket(
  `wss://cloud.agentverse.com/ws/messages/${group_id}/?device_id=${device_id}`,
  {
    headers: {
      'Authorization': `Bearer ${jwt_token}`
    }
  }
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'message_created':
      // Update UI with new message
      break;
    case 'message_updated':
      // Update existing message in UI
      break;
    case 'message_deleted':
      // Remove message from UI
      break;
    case 'presence':
      // User joined/left
      break;
    case 'typing':
      // Typing indicator
      break;
  }
};
```

**Sync Channel (Tenant-wide):**
```javascript
// Connect to tenant-wide sync channel for CRUD updates
const syncWs = new WebSocket(
  `wss://cloud.agentverse.com/ws/sync/?device_id=${device_id}`,
  {
    headers: {
      'Authorization': `Bearer ${jwt_token}`
    }
  }
);

syncWs.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'agent_updated':
      // Refresh agent cache
      updateLocalAgentCache(data.agent);
      break;
    case 'agent_deleted':
      // Remove from cache
      removeFromLocalAgentCache(data.agent_id);
      break;
    case 'tool_updated':
      // Refresh tool cache
      updateLocalToolCache(data.tool);
      break;
    case 'tool_deleted':
      // Remove from cache
      removeFromLocalToolCache(data.tool_id);
      break;
    case 'mcp_updated':
      // Refresh MCP cache
      updateLocalMCPCache(data.mcp_server);
      break;
    case 'mcp_deleted':
      // Remove from cache
      removeFromLocalMCPCache(data.mcp_id);
      break;
    case 'group_updated':
      // Refresh group metadata
      updateLocalGroupCache(data.group);
      break;
    case 'group_deleted':
      // Remove group
      removeFromLocalGroupCache(data.group_id);
      break;
  }
};
```

### 2. Cloud Backend Connection Handler

**Backend (MessageConsumer.connect):**
```python
async def connect(self):
    # Extract device_id from query params
    query_string = self.scope.get('query_string', b'').decode()
    params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
    self.device_id = params.get('device_id')

    # Join group channel (all users in group)
    await self.channel_layer.group_add(
        f'messages_{self.group_id}',
        self.channel_name
    )

    # Join device-specific channel (for future device-specific routing)
    if self.device_id:
        await self.channel_layer.group_add(
            f'device_{self.device_id}',
            self.channel_name
        )

    await self.accept()
```

---

## Broadcasting Events

### Message Broadcasting

**When message is created:**
```python
# In MessageViewSet.perform_create()

# 1. Extract execution context
execution_context = getattr(self.request, 'execution_context', None)

# 2. Store in message metadata
metadata = {
    'device_id': execution_context.get('device_id'),
    'execution_id': execution_context.get('execution_id'),
    'initiator_user_id': execution_context.get('initiator_user_id'),
    'call_depth': execution_context.get('call_depth', 0)
}

# 3. Save message
message = serializer.save(tenant=tenant, metadata=metadata)

# 4. Broadcast to WebSocket
channel_layer = get_channel_layer()
async_to_sync(channel_layer.group_send)(
    f'messages_{message.group}',  # Group channel
    {
        'type': 'message_created',
        'message': MessageSerializer(message).data
    }
)
```

### CRUD Broadcasting

**When agent is created/updated:**
```python
# In apps/core/signals.py

@receiver(post_save, sender='agents.Agent')
def agent_saved(sender, instance, created, **kwargs):
    # Serialize agent
    agent_data = AgentSerializer(instance).data

    # Broadcast to tenant sync channel
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'sync_{instance.tenant_id}',  # Tenant channel
        {
            'type': 'agent_updated',
            'agent': agent_data
        }
    )
```

---

## Tenant Isolation

All WebSocket connections are tenant-isolated:

1. **Authentication**: JWT token validates user
2. **Tenant Check**: User must belong to tenant
3. **Group Access**: User must have access to group (for MessageConsumer)
4. **Channel Isolation**:
   - Messages: `messages_{group_id}` (only group members)
   - Sync: `sync_{tenant_id}` (only tenant members)

---

## Device Routing

### Current Implementation (Broadcast to All)

Per user's architecture requirement:
> "All users in group will get exactly similar UI update from their WebSocket"

**Behavior:**
- Messages broadcast to ALL users in group
- CRUD updates broadcast to ALL users in tenant
- No device-specific filtering for group messages

### Device Channels (Available for Future Use)

Each WebSocket connection also joins a device-specific channel:
- `device_{device_id}`

This enables:
- Device-specific notifications (future feature)
- Targeted updates to specific devices
- Device presence tracking

**Example future use:**
```python
# Send message only to initiator's device
async_to_sync(channel_layer.group_send)(
    f'device_{initiator_device_id}',
    {
        'type': 'execution_complete',
        'result': result_data
    }
)
```

---

## Execution Context Metadata

Every message stores execution context in metadata:

```json
{
  "id": "msg-uuid",
  "group": "group-uuid",
  "sender_type": "agent",
  "sender_id": "agent-uuid",
  "content": "Agent response...",
  "metadata": {
    "device_id": "device-abc123...",
    "execution_id": "exec-def456...",
    "initiator_user_id": "user-ghi789...",
    "initiator_device_id": "device-abc123...",
    "call_depth": 2,

    "custom_field": "value"
  }
}
```

**Use Cases:**
- Analytics: Track which users initiate most executions
- Cost Attribution: Attribute LLM costs to initiating user
- Debugging: Full call stack for troubleshooting
- Audit Trail: Who initiated what

---

## Testing

### 1. Test Device ID Persistence

```bash
# Run local backend twice, device ID should be same
cd /home/user/Agentverse/local_backend
python -m src.main

# Check logs for device ID
# Kill and restart
python -m src.main

# Should show same device ID
```

### 2. Test WebSocket Connection

```bash
# Start cloud backend
cd /home/user/Agentverse/cloud_backend
python manage.py runserver

# Start Channels worker
python manage.py runworker

# Connect WebSocket client and verify:
# - Connection accepted
# - device_id in confirmation message
# - Can send/receive messages
```

### 3. Test Message Broadcasting

```bash
# 1. Connect two WebSocket clients to same group
# 2. Send message via API from one client
# 3. Verify BOTH clients receive message in real-time
```

### 4. Test CRUD Broadcasting

```bash
# 1. Connect WebSocket to sync channel
# 2. Create/update agent via API
# 3. Verify WebSocket receives agent_updated event
# 4. Delete agent via API
# 5. Verify WebSocket receives agent_deleted event
```

### 5. Test Execution Context

```bash
# 1. Send message with X-Device-ID and execution headers
# 2. Verify message metadata contains execution context
# 3. Check database: metadata field has device_id, execution_id, etc.
```

---

## Summary

| Feature | Status | Files |
|---------|--------|-------|
| Device ID generation | ✅ Complete | `local_backend/src/core/device_manager.py` |
| Execution context tracking | ✅ Complete | `local_backend/src/core/execution_context.py` |
| Cloud client headers | ✅ Complete | `local_backend/src/api/cloud_client.py` |
| ExecutionContextMiddleware | ✅ Complete | `cloud_backend/apps/core/middleware/execution_context.py` |
| CORS headers | ✅ Complete | `cloud_backend/config/settings.py` |
| Message ViewSet broadcasting | ✅ Complete | `cloud_backend/apps/messages/views.py` |
| WebSocket consumers | ✅ Complete | `cloud_backend/apps/messages/consumers.py` |
| Signal handlers | ✅ Complete | `cloud_backend/apps/core/signals.py` |
| Tenant isolation | ✅ Complete | All components |
| Device routing infrastructure | ✅ Complete | WebSocket consumers |

---

## Benefits Achieved

### 1. Real-Time Synchronization
- All users in group see UI updates simultaneously
- No polling required
- Instant feedback for user actions

### 2. Tenant Isolation
- Complete data separation
- WebSocket channels scoped to tenant/group
- No cross-tenant data leakage

### 3. Execution Tracking
- Full audit trail of agent chains
- Cost attribution to initiating user
- Analytics on execution patterns
- Debugging capabilities

### 4. Device Identification
- WebSocket routing infrastructure ready
- Device-specific channels available
- Future: Targeted notifications possible

### 5. CRUD Synchronization
- Agent/Tool/MCP/Group changes broadcast in real-time
- Local caches stay synchronized
- No manual refresh needed

---

## Next Steps (Optional Enhancements)

1. **Analytics Dashboard**
   - Query execution chains from message metadata
   - Per-user execution statistics
   - Cost attribution reports

2. **Device-Specific Routing**
   - Send execution results only to initiator device
   - Device presence indicators
   - Multi-device conflict resolution

3. **Rate Limiting**
   - Per-tenant WebSocket connection limits
   - Message rate limiting
   - Prevent WebSocket abuse

4. **Monitoring**
   - WebSocket connection metrics
   - Message delivery latency
   - Channel saturation alerts

---

## Architecture Compliance

✅ **User's Requirement:**
> "Any local change that can mutate user UI will first always go to cloud and all the user will get exactly similar UI update present in that group from their web socket"

**Implementation:**
- ✅ Local backend sends all mutations to cloud API
- ✅ Cloud API stores in database
- ✅ Cloud API broadcasts to ALL users in group/tenant via WebSocket
- ✅ All users receive exact same update
- ✅ UI updates synchronized across all devices

**WebSocket Routing:**
- ✅ Messages → Broadcast to `messages_{group_id}` (all group members)
- ✅ CRUD → Broadcast to `sync_{tenant_id}` (all tenant members)
- ✅ Tenant isolation enforced
- ✅ Device ID tracked for analytics and future features
