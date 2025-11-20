# Execution Context Implementation Guide

## Overview

Execution Context tracks the full chain of agent calls from when a user @mentions an agent until the chain completes. This enables:
- **WebSocket Routing**: Route messages back to the correct device
- **Analytics**: Track which user initiated which agent chains
- **Cost Attribution**: Attribute LLM costs to the initiating user
- **Debugging**: Full call stack for troubleshooting

---

## Phase 1: Device Identification ✅ IMPLEMENTED

### Local Backend Changes

**1. Device Manager** (`local_backend/src/core/device_manager.py`)
- Generates unique device ID on first run
- Persists to `~/.agentverse/device.json`
- Device ID remains consistent across restarts

**2. Cloud Client** (`local_backend/src/api/cloud_client.py`)
- Added `device_id` parameter to `__init__`
- Passes `X-Device-ID` header in all requests
- Updated `initialize_cloud_client()` to accept device_id

### Usage

```python
from src.core.device_manager import initialize_device_manager, get_device_manager
from src.api.cloud_client import initialize_cloud_client, CloudConfig

# On startup
device_mgr = initialize_device_manager("/home/user/.agentverse")
device_id = device_mgr.get_device_id()

# Initialize cloud client with device ID
config = CloudConfig(base_url="https://api.agentverse.com")
client = initialize_cloud_client(config, device_id=device_id)

# All requests now include X-Device-ID header
```

---

## Phase 2: Execution Context ✅ IMPLEMENTED

### Execution Context Class (`local_backend/src/core/execution_context.py`)

Tracks:
- `execution_id`: Unique ID for this execution chain
- `initiator_user_id`: User who @mentioned the first agent
- `initiator_device_id`: Device running the execution
- `group_id`: Group where execution is happening
- `tenant_id`: Tenant context
- `call_stack`: Agent call chain (e.g., ["agent_A", "agent_B"])
- `depth`: Current depth in call chain

### Usage in Agent Chains

```python
from src.core.execution_context import ExecutionContext

# User @john mentions @agent_A in group-123
ctx = ExecutionContext.create(
    initiator_user_id="user-uuid",
    initiator_device_id="device-uuid",
    group_id="group-123",
    tenant_id="tenant-uuid"
)

# Agent A execution starts
ctx.push_agent("agent_A")

# Agent A calls Agent B
ctx.push_agent("agent_B")

# Call chain: user -> agent_A -> agent_B
print(ctx.get_call_chain_str())
# Output: "user:user-uui -> agent_A -> agent_B"

# Agent B completes
ctx.pop_agent()  # Returns "agent_B"

# Agent A completes
ctx.pop_agent()  # Returns "agent_A"
```

### Cloud Client Integration

```python
from src.api.cloud_client import get_cloud_client

client = get_cloud_client()

# Set execution context before making requests
client.set_execution_context(ctx)

# All requests now include execution context headers:
# - X-Execution-ID
# - X-Initiator-User-ID
# - X-Initiator-Device-ID
# - X-Call-Depth

# Send message to cloud
await client.send_message(group_id, message_data)

# Clear execution context when chain completes
client.set_execution_context(None)
```

---

## Phase 3: Cloud Backend Tracking ⚠️ REQUIRES IMPLEMENTATION

### Cloud Backend Changes Needed

**1. Middleware: Extract Execution Context from Headers**

Create `cloud_backend/apps/core/middleware/execution_context.py`:

```python
class ExecutionContextMiddleware:
    """Extract execution context from request headers"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract execution context from headers
        execution_id = request.headers.get('X-Execution-ID')
        initiator_user_id = request.headers.get('X-Initiator-User-ID')
        initiator_device_id = request.headers.get('X-Initiator-Device-ID')
        device_id = request.headers.get('X-Device-ID')
        call_depth = request.headers.get('X-Call-Depth', '0')

        # Attach to request
        request.execution_context = {
            'execution_id': execution_id,
            'initiator_user_id': initiator_user_id,
            'initiator_device_id': initiator_device_id,
            'device_id': device_id,
            'call_depth': int(call_depth)
        } if execution_id else None

        response = self.get_response(request)
        return response
```

Add to `settings.py`:
```python
MIDDLEWARE = [
    # ... other middleware
    'apps.core.middleware.execution_context.ExecutionContextMiddleware',
]
```

**2. Message ViewSet: Store Execution Context**

Update `cloud_backend/apps/messages/views.py`:

```python
class MessageViewSet(viewsets.ModelViewSet):
    def create(self, request, group_id):
        # Extract execution context from request
        execution_context = getattr(request, 'execution_context', None)

        # Get device ID for WebSocket routing
        device_id = request.headers.get('X-Device-ID')

        # Create message with execution metadata
        message = Message.objects.create(
            group=group_id,
            tenant=request.tenant,
            sender_type=request.data['sender_type'],
            sender_id=request.data['sender_id'],
            content=request.data['content'],
            metadata={
                # Existing metadata
                **request.data.get('metadata', {}),

                # Execution context
                'execution_id': execution_context['execution_id'] if execution_context else None,
                'initiator_user_id': execution_context['initiator_user_id'] if execution_context else None,
                'initiator_device_id': execution_context['initiator_device_id'] if execution_context else None,
                'call_depth': execution_context['call_depth'] if execution_context else 0,

                # Device for WebSocket routing
                'device_id': device_id,

                'timestamp': datetime.utcnow().isoformat()
            }
        )

        # Broadcast to all tenant users via WebSocket
        await self.broadcast_message(message, device_id)

        return Response(MessageSerializer(message).data)

    async def broadcast_message(self, message, target_device_id=None):
        """
        Broadcast message via WebSocket.

        Args:
            message: Message instance
            target_device_id: Specific device to route to (for initiator updates)
        """
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()

        # Broadcast to all users in tenant
        await channel_layer.group_send(
            f"tenant_{message.tenant_id}",
            {
                "type": "message.new",
                "message": MessageSerializer(message).data,
                "target_device": target_device_id  # Route to specific device if specified
            }
        )
```

**3. WebSocket Consumer: Route by Device ID**

Update `cloud_backend/apps/core/consumers.py`:

```python
class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract device ID from query params or headers
        self.device_id = self.scope['query_string'].decode().split('device_id=')[1]
        self.tenant_id = self.scope['user'].tenant_id

        # Join tenant group
        await self.channel_layer.group_add(
            f"tenant_{self.tenant_id}",
            self.channel_name
        )

        # Also join device-specific group
        await self.channel_layer.group_add(
            f"device_{self.device_id}",
            self.channel_name
        )

        await self.accept()

    async def message_new(self, event):
        """Handle new message broadcast"""
        message = event['message']
        target_device = event.get('target_device')

        # If message is targeted to specific device, only send if this is that device
        if target_device and target_device != self.device_id:
            return

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': message
        }))
```

**4. Analytics: Query Execution Chains**

Create `cloud_backend/apps/analytics/views.py`:

```python
class ExecutionAnalyticsViewSet(viewsets.ViewSet):
    """Analytics on execution chains"""

    def execution_chains(self, request):
        """Get execution chains for current tenant"""
        tenant = request.tenant

        # Query messages with execution_id
        chains = Message.objects.filter(
            tenant=tenant,
            metadata__execution_id__isnull=False
        ).values(
            'metadata__execution_id',
            'metadata__initiator_user_id',
            'metadata__call_depth'
        ).annotate(
            message_count=Count('id'),
            avg_depth=Avg('metadata__call_depth'),
            max_depth=Max('metadata__call_depth')
        )

        return Response(list(chains))

    def user_execution_stats(self, request):
        """Get per-user execution statistics"""
        tenant = request.tenant

        stats = Message.objects.filter(
            tenant=tenant,
            metadata__initiator_user_id__isnull=False
        ).values(
            'metadata__initiator_user_id'
        ).annotate(
            total_chains=Count('metadata__execution_id', distinct=True),
            total_messages=Count('id'),
            avg_chain_length=Avg('metadata__call_depth')
        )

        return Response(list(stats))
```

---

## Integration Example: Full Flow

### 1. Local Backend: User @mentions Agent

```python
from src.core.execution_context import ExecutionContext
from src.api.cloud_client import get_cloud_client
from src.core.device_manager import get_device_manager

async def process_user_message(group_id, message, user_id, tenant_id):
    """User @mentions an agent"""

    # Extract mentioned agent
    agent_id = extract_mention(message)  # e.g., "@agent_A" -> "agent_A"

    # Create execution context
    device_id = get_device_manager().get_device_id()
    ctx = ExecutionContext.create(
        initiator_user_id=user_id,
        initiator_device_id=device_id,
        group_id=group_id,
        tenant_id=tenant_id
    )

    # Set execution context in cloud client
    client = get_cloud_client()
    client.set_execution_context(ctx)

    # Execute agent (passes context through)
    orchestrator = get_orchestrator()
    await orchestrator.process_user_message(
        group_id=group_id,
        agent_id=agent_id,
        message=message,
        execution_context=ctx  # Pass to agent
    )

    # Clear execution context
    client.set_execution_context(None)
```

### 2. Local Backend: Agent Calls Another Agent

```python
async def agent_call(
    self,
    group_id: str,
    caller_key: str,
    target_key: str,
    prompt: str,
    execution_context: Optional[ExecutionContext] = None,
    depth: int = 2
) -> str:
    """Agent calls another agent"""

    # Push caller to call stack
    if execution_context:
        execution_context.push_agent(caller_key)

    # Update cloud client context
    client = get_cloud_client()
    client.set_execution_context(execution_context)

    # Execute target agent
    callee = await self.get_agent(target_key)
    reply = await callee.respond(
        prompt,
        group_id=group_id,
        orchestrator=self,
        execution_context=execution_context,  # Pass through
        depth=depth - 1
    )

    # Pop caller from call stack
    if execution_context:
        execution_context.pop_agent()

    return reply
```

### 3. Cloud Backend: Receive and Store

```python
# cloud_backend/apps/messages/views.py

def create(self, request, group_id):
    execution_context = request.execution_context  # From middleware
    device_id = request.headers.get('X-Device-ID')

    message = Message.objects.create(
        group=group_id,
        tenant=request.tenant,
        sender_type=request.data['sender_type'],
        sender_id=request.data['sender_id'],
        content=request.data['content'],
        metadata={
            'execution_id': execution_context['execution_id'] if execution_context else None,
            'initiator_user_id': execution_context['initiator_user_id'] if execution_context else None,
            'device_id': device_id,
            'call_depth': execution_context['call_depth'] if execution_context else 0
        }
    )

    # Broadcast via WebSocket to specific device
    await broadcast_to_device(device_id, message)
```

---

## Benefits

### 1. WebSocket Routing
- Cloud knows which device to send messages to
- Real-time updates arrive at correct local backend instance

### 2. Analytics
- Track which users are power users (initiate most chains)
- Identify longest agent chains
- Cost attribution for LLM usage

### 3. Debugging
- Full call stack for troubleshooting
- Trace execution flow across agents
- Identify performance bottlenecks

### 4. Audit Trail
- Complete record of who initiated what
- Compliance and security tracking

---

## Testing

### Test Device ID Persistence

```bash
# Run local backend twice, device ID should be same
python main.py
# Check logs: "Device manager initialized: abc12345-..."

# Kill and restart
python main.py
# Should show same ID: "Loaded device ID: abc12345-..."
```

### Test Execution Context

```python
from src.core.execution_context import ExecutionContext

ctx = ExecutionContext.create(
    initiator_user_id="user-123",
    initiator_device_id="device-456",
    group_id="group-789",
    tenant_id="tenant-abc"
)

ctx.push_agent("agent_A")
ctx.push_agent("agent_B")
ctx.push_agent("agent_C")

assert ctx.depth == 3
assert ctx.call_stack == ["agent_A", "agent_B", "agent_C"]
assert ctx.get_call_chain_str() == "user:user-123 -> agent_A -> agent_B -> agent_C"

ctx.pop_agent()
assert ctx.depth == 2
assert ctx.get_current_agent() == "agent_B"
```

### Test Headers

```python
from src.api.cloud_client import CloudAPIClient, CloudConfig
from src.core.execution_context import ExecutionContext

config = CloudConfig(base_url="https://api.test.com")
client = CloudAPIClient(config, device_id="device-123")

ctx = ExecutionContext.create(
    initiator_user_id="user-456",
    initiator_device_id="device-123",
    group_id="group-789",
    tenant_id="tenant-abc"
)
ctx.push_agent("agent_A")

client.set_execution_context(ctx)
headers = client._get_headers(include_auth=False)

assert headers["X-Device-ID"] == "device-123"
assert headers["X-Execution-ID"] == ctx.execution_id
assert headers["X-Initiator-User-ID"] == "user-456"
assert headers["X-Call-Depth"] == "1"
```

---

## Summary

| Phase | Status | Files Changed |
|-------|--------|---------------|
| Phase 1: Device ID | ✅ Complete | `device_manager.py`, `cloud_client.py` |
| Phase 2: Execution Context | ✅ Complete | `execution_context.py`, `cloud_client.py` |
| Phase 3: Cloud Tracking | ⚠️ Pending | Cloud backend middleware, views, consumers |

**Next Steps**:
1. ✅ Device ID generation and persistence (DONE)
2. ✅ Execution context tracking (DONE)
3. ⚠️ Implement cloud backend middleware and WebSocket routing (PENDING)
