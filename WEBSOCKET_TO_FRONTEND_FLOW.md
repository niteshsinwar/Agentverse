# WebSocket to Frontend Display Flow

## 🔄 Complete Data Flow: Cloud → Local Backend → Frontend

### Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Cloud Backend                                │
│                      (Django + Channels)                            │
│                                                                     │
│  PostgreSQL → Django Signal → WebSocket Broadcast                  │
│                                  │                                  │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                                   │ WebSocket (wss://)
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│     Device A (User A)       │   │     Device B (User B)       │
│                             │   │                             │
│  ┌───────────────────────┐ │   │  ┌───────────────────────┐ │
│  │   Local Backend       │ │   │  │   Local Backend       │ │
│  │   (FastAPI)           │ │   │  │   (FastAPI)           │ │
│  │                       │ │   │  │                       │ │
│  │ 1. WebSocket Client   │ │   │  │ 1. WebSocket Client   │ │
│  │    Receives update    │ │   │  │    Receives update    │ │
│  │                       │ │   │  │                       │ │
│  │ 2. Updates local cache│ │   │  │ 2. Updates local cache│ │
│  │                       │ │   │  │                       │ │
│  │ 3. REST API serves    │ │   │  │ 3. REST API serves    │ │
│  │    updated data       │ │   │  │    updated data       │ │
│  └───────┬───────────────┘ │   │  └───────┬───────────────┘ │
│          │ HTTP/REST         │   │          │ HTTP/REST       │
│          ▼                   │   │          ▼                 │
│  ┌───────────────────────┐ │   │  ┌───────────────────────┐ │
│  │   Local Frontend      │ │   │  │   Local Frontend      │ │
│  │   (React)             │ │   │  │   (React)             │ │
│  │                       │ │   │  │                       │ │
│  │ 4. Fetches updated    │ │   │  │ 4. Fetches updated    │ │
│  │    data via API       │ │   │  │    data via API       │ │
│  │                       │ │   │  │                       │ │
│  │ 5. Updates UI         │ │   │  │ 5. Updates UI         │ │
│  │    (React state)      │ │   │  │    (React state)      │ │
│  └───────────────────────┘ │   │  └───────────────────────┘ │
│                             │   │                             │
│  ✅ User sees update        │   │  ✅ User sees update        │
└─────────────────────────────┘   └─────────────────────────────┘
```

## 📝 Detailed Flow: Step by Step

### Scenario: User A Creates a New Agent

#### Step 1: User Creates Agent (Frontend)

```typescript
// local_frontend/src/components/AgentForm.tsx

const handleCreateAgent = async (agentData) => {
  // POST to local backend
  const response = await fetch('http://localhost:8000/api/v1/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agentData)
  });

  const newAgent = await response.json();
  console.log('Agent created:', newAgent);
};
```

#### Step 2: Local Backend Creates Agent + Syncs to Cloud

```python
# local_backend/src/api/agents.py

@router.post("/api/v1/agents")
async def create_agent(agent: AgentCreate):
    # 1. Create in local SQLite cache
    agent_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO agents (id, name, ...) VALUES (?, ?, ...)",
        (agent_id, agent.name, ...)
    )

    # 2. Sync to cloud backend (if cloud enabled)
    if settings.cloud_enabled:
        await cloud_client.create_agent(agent.dict())

    return {"id": agent_id, "name": agent.name, ...}
```

#### Step 3: Cloud Backend Saves + Broadcasts

```python
# cloud_backend/apps/agents/views.py

class AgentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # 1. Save to PostgreSQL
        agent = Agent.objects.create(**request.data)

        # 2. Django signal automatically fires
        # (see cloud_backend/apps/agents/signals.py)

        return Response(AgentSerializer(agent).data, status=201)
```

```python
# cloud_backend/apps/agents/signals.py

@receiver(post_save, sender=Agent)
def broadcast_agent_update(sender, instance, created, **kwargs):
    """Automatically broadcast agent changes via WebSocket"""

    # Get tenant's WebSocket channel group
    channel_layer = get_channel_layer()
    tenant_id = connection.tenant.id

    # Broadcast to ALL devices subscribed to this tenant
    async_to_sync(channel_layer.group_send)(
        f"tenant_{tenant_id}_sync",
        {
            'type': 'sync_update',
            'event_type': 'agent_created' if created else 'agent_updated',
            'data': AgentSerializer(instance).data
        }
    )
```

#### Step 4: WebSocket Client Receives Update (Local Backend)

```python
# local_backend/src/api/cloud_websocket.py

class CloudWebSocketClient:
    async def _listen(self):
        """Listen for messages from cloud backend"""
        async for message in self.ws:
            data = json.loads(message)

            # Parse sync event
            event = SyncEvent(
                type=data.get('event_type'),  # 'agent_created'
                data=data.get('data')          # Agent object
            )

            # Notify all registered handlers
            await self._notify_handlers(event)
```

#### Step 5: Sync Handler Updates Local Cache

```python
# local_backend/src/api/cloud_sync_handler.py

class CloudSyncHandler:
    async def handle_sync_event(self, event: SyncEvent):
        """Handle incoming sync event from cloud"""

        if event.type == 'agent_created':
            await self._handle_agent_create(event)
        elif event.type == 'agent_updated':
            await self._handle_agent_update(event)
        # ... other event types

    async def _handle_agent_create(self, event: SyncEvent):
        """Handle agent creation event"""
        agent_data = event.data

        # Update local SQLite cache
        await self.cache._cache_agent(agent_data)

        logger.info(f"✅ New agent cached: {agent_data['name']}")
```

#### Step 6: Frontend Fetches Updated Data

**Option A: Polling (Current Simple Approach)**

```typescript
// local_frontend/src/hooks/useAgents.ts

export function useAgents() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    // Poll for updates every 2 seconds
    const interval = setInterval(async () => {
      const response = await fetch('http://localhost:8000/api/v1/agents');
      const data = await response.json();
      setAgents(data);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return agents;
}
```

**Option B: WebSocket from Local Backend to Frontend (Real-Time)**

```typescript
// local_frontend/src/lib/localWebSocket.ts

class LocalWebSocketClient {
  private ws: WebSocket;

  connect() {
    // Connect to local backend WebSocket
    this.ws = new WebSocket('ws://localhost:8000/ws');

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'agent_created') {
        // Notify React components to update
        this.notifyAgentUpdate(data.agent);
      }
    };
  }

  private notifyAgentUpdate(agent: Agent) {
    // Trigger React state update
    window.dispatchEvent(new CustomEvent('agent-update', {
      detail: agent
    }));
  }
}
```

```typescript
// local_frontend/src/hooks/useAgents.ts (WebSocket version)

export function useAgents() {
  const [agents, setAgents] = useState([]);

  useEffect(() => {
    // Initial fetch
    fetchAgents().then(setAgents);

    // Listen for real-time updates
    const handleUpdate = (event: CustomEvent) => {
      const newAgent = event.detail;
      setAgents(prev => [...prev, newAgent]);
    };

    window.addEventListener('agent-update', handleUpdate);

    return () => {
      window.removeEventListener('agent-update', handleUpdate);
    };
  }, []);

  return agents;
}
```

#### Step 7: React Component Updates UI

```typescript
// local_frontend/src/components/AgentList.tsx

export function AgentList() {
  const agents = useAgents();  // Auto-updates via WebSocket

  return (
    <div className="agent-list">
      {agents.map(agent => (
        <AgentCard
          key={agent.id}
          agent={agent}
        />
      ))}
    </div>
  );
}

// UI automatically re-renders when agents state updates!
```

## 🔥 Two Approaches for Local Backend → Frontend

### Approach 1: HTTP Polling (Simple, Current)

**Pros:**
- ✅ Simple to implement
- ✅ Works with any frontend framework
- ✅ No persistent connections needed

**Cons:**
- ❌ Not truly real-time (2-5 second delay)
- ❌ More server load (frequent polling)
- ❌ Inefficient (fetches even if no changes)

**Implementation:**
```typescript
// Frontend polls local backend every 2s
setInterval(() => {
  fetch('/api/v1/agents').then(data => updateState(data));
}, 2000);
```

### Approach 2: WebSocket (Real-Time, Recommended)

**Pros:**
- ✅ True real-time (< 100ms updates)
- ✅ Efficient (only sends when data changes)
- ✅ Lower server load
- ✅ Better UX

**Cons:**
- ❌ Slightly more complex
- ❌ Requires WebSocket server in local backend

**Implementation:**

```python
# local_backend/server.py - Add WebSocket endpoint

from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Register this connection
    active_connections.append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

async def broadcast_to_frontend(event_type: str, data: dict):
    """Broadcast update to all connected frontends"""
    message = json.dumps({'type': event_type, 'data': data})

    for connection in active_connections:
        await connection.send_text(message)
```

```python
# local_backend/src/api/cloud_sync_handler.py - Notify frontend

class CloudSyncHandler:
    async def _handle_agent_create(self, event: SyncEvent):
        agent_data = event.data

        # 1. Update local cache
        await self.cache._cache_agent(agent_data)

        # 2. Broadcast to frontend via WebSocket
        await broadcast_to_frontend('agent_created', agent_data)

        logger.info(f"✅ Agent synced to frontend: {agent_data['name']}")
```

## 📊 Message Flow Example (Multi-User Chat)

### Scenario: User A sends message, all users see it

```
User A (Device A):
  1. Types message in frontend
  2. POST /api/v1/groups/{group_id}/messages → Local Backend A
  3. Local Backend A → Cloud Backend (save message)
  4. Cloud Backend → PostgreSQL (save)
  5. Cloud Backend → Django Signal fires
  6. Cloud Backend → WebSocket broadcast to ALL devices

Device A (User A):
  7. WebSocket Client receives message
  8. Sync Handler updates local cache
  9. [Option A] Frontend polls → sees new message
     [Option B] WebSocket → frontend updates instantly
  10. UI shows message

Device B (User B):
  7. WebSocket Client receives same message
  8. Sync Handler updates local cache
  9. [Option A] Frontend polls → sees new message
     [Option B] WebSocket → frontend updates instantly
  10. UI shows message

Device C (User C):
  7. WebSocket Client receives same message
  8. Sync Handler updates local cache
  9. [Option A] Frontend polls → sees new message
     [Option B] WebSocket → frontend updates instantly
  10. UI shows message

Result: ALL users see the message in real-time!
```

## 🎯 Recommended Architecture

### For Production: Use WebSocket All The Way

```
Cloud Backend
    │ (WebSocket)
    ▼
Local Backend
    │ (WebSocket)
    ▼
Local Frontend
    │ (React State)
    ▼
UI Updates (< 100ms total latency!)
```

### Current Implementation: Hybrid

```
Cloud Backend
    │ (WebSocket)
    ▼
Local Backend (cache updated)
    │ (HTTP polling every 2s)
    ▼
Local Frontend
    │ (React State)
    ▼
UI Updates (2-3s latency)
```

## 🚀 Implementation Steps for Full WebSocket

### Step 1: Add WebSocket to Local Backend

```python
# local_backend/server.py

from fastapi import WebSocket
from typing import List

# Active WebSocket connections
active_frontend_connections: List[WebSocket] = []

@app.websocket("/ws/frontend")
async def frontend_websocket(websocket: WebSocket):
    """WebSocket endpoint for frontend connections"""
    await websocket.accept()
    active_frontend_connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        active_frontend_connections.remove(websocket)

async def broadcast_to_frontends(event_type: str, data: dict):
    """Broadcast to all connected frontends"""
    message = json.dumps({'type': event_type, 'data': data})

    dead_connections = []
    for ws in active_frontend_connections:
        try:
            await ws.send_text(message)
        except:
            dead_connections.append(ws)

    # Remove dead connections
    for ws in dead_connections:
        active_frontend_connections.remove(ws)
```

### Step 2: Update Sync Handler to Broadcast

```python
# local_backend/src/api/cloud_sync_handler.py

class CloudSyncHandler:
    async def _handle_agent_update(self, event: SyncEvent):
        agent_data = event.data

        # Update local cache
        await self.cache._cache_agent(agent_data)

        # Broadcast to frontend
        from server import broadcast_to_frontends
        await broadcast_to_frontends('agent_updated', agent_data)
```

### Step 3: Frontend WebSocket Client

```typescript
// local_frontend/src/lib/localWebSocket.ts

class LocalWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private handlers: Map<string, Function[]> = new Map();

  connect() {
    this.ws = new WebSocket('ws://localhost:8000/ws/frontend');

    this.ws.onopen = () => {
      console.log('✅ Connected to local backend WebSocket');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.notifyHandlers(data.type, data.data);
    };

    this.ws.onclose = () => {
      console.log('⚠️  Disconnected from local backend');
      this.reconnect();
    };
  }

  on(eventType: string, handler: Function) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  private notifyHandlers(eventType: string, data: any) {
    const handlers = this.handlers.get(eventType) || [];
    handlers.forEach(handler => handler(data));
  }

  private reconnect() {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    setTimeout(() => this.connect(), delay);
  }
}

export const localWebSocket = new LocalWebSocketClient();
```

### Step 4: React Hook for Real-Time Updates

```typescript
// local_frontend/src/hooks/useRealtimeAgents.ts

import { useState, useEffect } from 'react';
import { localWebSocket } from '@/lib/localWebSocket';

export function useRealtimeAgents() {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    // Initial fetch
    fetchAgents().then(setAgents);

    // Listen for real-time updates
    localWebSocket.on('agent_created', (agent: Agent) => {
      setAgents(prev => [...prev, agent]);
    });

    localWebSocket.on('agent_updated', (agent: Agent) => {
      setAgents(prev => prev.map(a =>
        a.id === agent.id ? agent : a
      ));
    });

    localWebSocket.on('agent_deleted', (agentId: string) => {
      setAgents(prev => prev.filter(a => a.id !== agentId));
    });

    // Connect WebSocket
    localWebSocket.connect();

    return () => {
      // Cleanup handled by WebSocket client
    };
  }, []);

  return agents;
}
```

## 🎉 Result: True Real-Time UI

```typescript
// local_frontend/src/components/AgentList.tsx

export function AgentList() {
  // Automatically updates when agents change!
  const agents = useRealtimeAgents();

  return (
    <div className="agent-list">
      <h2>Agents ({agents.length})</h2>
      {agents.map(agent => (
        <AgentCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}

// When User B creates an agent on Device B:
// 1. Cloud broadcasts update (< 50ms)
// 2. Device A's local backend receives it (< 50ms)
// 3. Device A's frontend WebSocket gets update (< 10ms)
// 4. React re-renders (< 10ms)
// Total: ~120ms - User A sees the new agent almost instantly! ⚡
```

## 📝 Summary

### Current Flow (HTTP Polling):
```
Cloud → WebSocket → Local Backend (cache) → HTTP Poll (2s) → Frontend
```

### Recommended Flow (Full WebSocket):
```
Cloud → WebSocket → Local Backend (cache) → WebSocket (instant) → Frontend
```

### Key Takeaways:

1. **Cloud to Local Backend**: WebSocket for real-time config sync ✅
2. **Local Backend to Frontend**: Currently HTTP polling, recommend WebSocket
3. **All Users See Updates**: Yes! Cloud broadcasts to ALL devices
4. **Performance**:
   - Current: 2-3 second delay
   - With WebSocket: < 200ms delay
5. **Implementation**: WebSocket in local backend + React hook = real-time UI

The architecture supports true real-time collaboration across all devices! 🎉
