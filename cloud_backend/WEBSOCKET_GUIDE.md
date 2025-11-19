# WebSocket Real-Time Communication Guide

Complete guide to WebSocket implementation for real-time features in AgentVerse Cloud Backend.

## Overview

The cloud backend implements two WebSocket consumers for different real-time features:

1. **MessageConsumer** - Real-time chat messages within groups
2. **CloudSyncConsumer** - Cloud→Local synchronization for config updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Backend                            │
│                                                              │
│  ┌──────────────┐      ┌─────────────────────────────────┐ │
│  │  Django ORM  │──────│  Django Signals                 │ │
│  │  (Models)    │      │  - broadcast_message_saved      │ │
│  └──────────────┘      │  - broadcast_agent_update       │ │
│         │              │  - broadcast_tool_update        │ │
│         │              │  - broadcast_mcp_update         │ │
│         ▼              └─────────────┬───────────────────┘ │
│  ┌──────────────────────────────────▼───────────────────┐  │
│  │              Channel Layer (Redis)                    │  │
│  │  - messages_{group_id}  (chat messages)              │  │
│  │  - sync_{tenant_id}     (config sync)                │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  WebSocket Consumers  │
              │  - MessageConsumer    │
              │  - CloudSyncConsumer  │
              └───────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │  WebSocket Clients  │
                │  (Local Backends)   │
                └─────────────────────┘
```

## WebSocket Endpoints

### 1. Message Consumer (Real-time Chat)

**Endpoint:** `ws://localhost:9000/ws/messages/<group_id>/?token=<jwt>`

**Purpose:** Real-time chat messages for a specific group

**Features:**
- Message broadcasting (create, update, delete)
- Typing indicators
- User presence (joined/left)
- Group access control

**Connection Example:**
```python
import websockets
import json

uri = f"ws://localhost:9000/ws/messages/{group_id}/?token={jwt_token}"

async with websockets.connect(uri) as ws:
    # Send typing indicator
    await ws.send(json.dumps({
        'type': 'typing_indicator',
        'is_typing': True
    }))

    # Receive messages
    while True:
        message = await ws.recv()
        data = json.loads(message)
        print(f"Received: {data['type']}")
```

**Events Received:**
```json
// Message created
{
    "type": "message_created",
    "message": {
        "id": "uuid",
        "content": "Hello world",
        "sender_id": "uuid",
        "group_id": "uuid",
        "created_at": "2025-01-01T00:00:00Z"
    }
}

// Message updated
{
    "type": "message_updated",
    "message": { /* updated message data */ }
}

// Message deleted
{
    "type": "message_deleted",
    "message_id": "uuid"
}

// Typing indicator
{
    "type": "typing_indicator",
    "user_id": "uuid",
    "user_name": "John Doe",
    "is_typing": true
}

// User presence
{
    "type": "user_presence",
    "action": "joined",  // or "left"
    "user_id": "uuid",
    "user_name": "John Doe"
}
```

### 2. Cloud Sync Consumer (Config Synchronization)

**Endpoint:** `ws://localhost:9000/ws/sync/?token=<jwt>`

**Purpose:** Push agent/tool/MCP/group config updates from cloud to local backends

**Features:**
- Automatic broadcasting when admin updates configs in cloud
- Tenant-specific channels (only receive updates for your tenant)
- Real-time synchronization without polling

**Connection Example:**
```python
uri = f"ws://localhost:9000/ws/sync/?token={jwt_token}"

async with websockets.connect(uri) as ws:
    # Listen for config updates
    while True:
        update = await ws.recv()
        data = json.loads(update)

        if data['type'] == 'agent_updated':
            # Update local cache with new agent config
            update_local_agent_cache(data['agent'])
        elif data['type'] == 'tool_updated':
            update_local_tool_cache(data['tool'])
```

**Events Received:**
```json
// Agent config updated
{
    "type": "agent_updated",
    "agent": {
        "id": "uuid",
        "name": "Customer Support Bot",
        "system_prompt": "...",
        "tools": ["uuid1", "uuid2"],
        "updated_at": "2025-01-01T00:00:00Z"
    }
}

// Tool updated
{
    "type": "tool_updated",
    "tool": {
        "id": "uuid",
        "name": "search_database",
        "code": "def search_database(query): ...",
        "updated_at": "2025-01-01T00:00:00Z"
    }
}

// MCP server updated
{
    "type": "mcp_updated",
    "mcp_server": {
        "id": "uuid",
        "name": "File System Server",
        "command": "npx @modelcontextprotocol/server-filesystem",
        "updated_at": "2025-01-01T00:00:00Z"
    }
}

// Group updated
{
    "type": "group_updated",
    "group": {
        "id": "uuid",
        "name": "Sales Team",
        "members": ["user1", "user2"],
        "updated_at": "2025-01-01T00:00:00Z"
    }
}
```

## Authentication

All WebSocket connections require JWT authentication.

### Token Generation (Server-side)

```python
import jwt
from django.conf import settings

def generate_jwt_token(user):
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
```

### Token Usage (Client-side)

**Option 1: Query Parameter (Recommended)**
```
ws://localhost:9000/ws/sync/?token=<jwt_token>
```

**Option 2: Authorization Header**
```javascript
const ws = new WebSocket('ws://localhost:9000/ws/sync/', {
    headers: {
        'Authorization': `Bearer ${jwt_token}`
    }
});
```

### Security

- Invalid tokens are rejected with code `4001`
- Unauthorized access is rejected with code `4003`
- Token expiry is checked on each connection
- Allowed hosts validation prevents CSRF attacks

## Django Signals (Automatic Broadcasting)

The WebSocket system uses Django signals to automatically broadcast events when database changes occur.

### Message Signals

```python
# apps/messages/signals.py

@receiver(post_save, sender=Message)
def broadcast_message_saved(sender, instance, created, **kwargs):
    """Automatically broadcast when message is created/updated"""
    # Broadcasts to: messages_{instance.group_id}

@receiver(post_delete, sender=Message)
def broadcast_message_deleted(sender, instance, **kwargs):
    """Automatically broadcast when message is deleted"""
```

### Config Sync Signals

```python
@receiver(post_save, sender='agents.Agent')
def broadcast_agent_update(sender, instance, created, **kwargs):
    """Automatically broadcast when agent config changes"""
    # Broadcasts to: sync_{tenant_id}

@receiver(post_save, sender='tools.Tool')
def broadcast_tool_update(sender, instance, created, **kwargs):
    """Automatically broadcast when tool code changes"""

@receiver(post_save, sender='mcp.MCPServer')
def broadcast_mcp_update(sender, instance, created, **kwargs):
    """Automatically broadcast when MCP server config changes"""

@receiver(post_save, sender='groups.Group')
def broadcast_group_update(sender, instance, created, **kwargs):
    """Automatically broadcast when group membership changes"""
```

## Channel Layers

The WebSocket system uses Redis for production and in-memory for development.

### Production (Redis)

```python
# config/settings.py

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
        },
    },
}
```

### Development (In-Memory)

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    },
}
```

## Testing

### Run WebSocket Tests

```bash
cd cloud_backend

# Install test dependencies
pip install websocket-client websockets

# Make test script executable
chmod +x test_websocket.py

# Run tests
python test_websocket.py
```

### Manual Testing with JavaScript

```javascript
// Test MessageConsumer
const chatWs = new WebSocket(
    `ws://localhost:9000/ws/messages/${groupId}/?token=${jwtToken}`
);

chatWs.onopen = () => {
    console.log('Connected to chat');

    // Send typing indicator
    chatWs.send(JSON.stringify({
        type: 'typing_indicator',
        is_typing: true
    }));
};

chatWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Test CloudSyncConsumer
const syncWs = new WebSocket(
    `ws://localhost:9000/ws/sync/?token=${jwtToken}`
);

syncWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Config update:', data);

    // Update local cache based on event type
    switch(data.type) {
        case 'agent_updated':
            updateAgentCache(data.agent);
            break;
        case 'tool_updated':
            updateToolCache(data.tool);
            break;
    }
};
```

## Deployment

### Redis Requirement

For production, Redis is required for channel layer.

**Render.com setup (already configured in render.yaml):**
```yaml
databases:
  - name: agentverse-redis
    plan: starter
```

**Manual Redis setup:**
```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
redis-server

# Configure in settings
REDIS_URL=redis://localhost:6379
```

### Running with ASGI Server

For production, use Daphne or Uvicorn ASGI server:

```bash
# Install Daphne
pip install daphne

# Run ASGI application
daphne -b 0.0.0.0 -p 9000 config.asgi:application
```

Or with Uvicorn:
```bash
pip install uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 9000
```

## Troubleshooting

### WebSocket Connection Refused

**Problem:** `Connection refused` when connecting to WebSocket

**Solutions:**
- Ensure Django server is running: `python manage.py runserver 9000`
- Check that ASGI application is configured correctly in `config/asgi.py`
- Verify channel layers are configured in settings

### Authentication Fails (4001)

**Problem:** Connection closed with code 4001

**Solutions:**
- Verify JWT token is valid and not expired
- Check SECRET_KEY matches between token generation and validation
- Ensure user exists in database

### Unauthorized Access (4003)

**Problem:** Connection closed with code 4003

**Solutions:**
- Verify user has access to the group (for MessageConsumer)
- Check group exists in database
- Ensure user is a member of the group

### Messages Not Broadcasting

**Problem:** Messages saved but not broadcasted to WebSocket clients

**Solutions:**
- Verify signals are registered in `apps.py` ready() method
- Check channel layer is configured correctly
- Ensure Redis is running (for production)
- Check logs for signal errors

## Performance Considerations

### Connection Limits

- Each WebSocket connection uses system resources
- Recommended: Max 10,000 concurrent connections per server
- Use load balancing for higher scale

### Channel Layer Optimization

**Redis Configuration:**
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)],
            'capacity': 1500,  # Messages per channel
            'expiry': 10,      # Message expiry in seconds
        },
    },
}
```

### Monitoring

Monitor WebSocket connections:
```bash
# Check active connections
netstat -an | grep :9000 | grep ESTABLISHED | wc -l

# Check Redis memory usage
redis-cli INFO memory
```

## Next Steps

1. **Frontend Integration:** Connect frontend to WebSocket endpoints
2. **Reconnection Logic:** Implement automatic reconnection on disconnect
3. **Message Queuing:** Handle offline messages with queue
4. **Load Testing:** Test with multiple concurrent connections
5. **Monitoring:** Add WebSocket metrics to analytics dashboard

## Resources

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket Protocol Specification](https://datatracker.ietf.org/doc/html/rfc6455)
- [Redis Channel Layer](https://github.com/django/channels_redis)
