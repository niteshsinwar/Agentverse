# Frontend Cloud Integration Guide

Complete guide for integrating the local frontend with cloud backend APIs and real-time WebSocket features.

## Architecture Overview

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Local Frontend  │─────▶│  Local Backend   │─────▶│  Cloud Backend   │
│  (React + Vite)  │      │  (FastAPI:8000)  │      │  (Django:9000)   │
│                  │      │                  │      │                  │
│  - UI/UX         │      │  - Auth Proxy    │      │  - Multi-tenant  │
│  - State Mgmt    │      │  - Cache Layer   │      │  - CRUD APIs     │
│  - WebSocket     │      │  - Local Exec    │      │  - WebSocket     │
└──────────────────┘      └──────────────────┘      └──────────────────┘
         │                                                    │
         └────────────────────────────────────────────────────┘
                     Direct WebSocket Connection
                    (for real-time sync and chat)
```

## Integration Strategy

### Phase 1: Hybrid Mode (Current)
- Frontend → Local Backend → Cloud Backend
- Local backend acts as proxy and cache
- Agent execution happens locally
- Configuration synced from cloud

### Phase 2: Direct Cloud Integration (Future)
- Frontend → Cloud Backend (direct)
- All CRUD operations via cloud
- WebSocket for real-time updates
- Agent execution via cloud workers

## 1. API Integration

### 1.1 Current Configuration

```typescript
// local_frontend/src/lib/config.ts
export const env = {
  API_BASE_URL: 'http://localhost:8000',  // Local Backend
  ...
};
```

### 1.2 Cloud-Enabled Configuration

Update the config to support both local and cloud modes:

```typescript
// local_frontend/src/lib/config.ts

interface CloudConfig {
  ENABLED: boolean;
  BASE_URL: string;
  WS_URL: string;
}

const validateCloudConfig = (): CloudConfig => {
  const enabled = import.meta.env.VITE_CLOUD_ENABLED === 'true';

  return {
    ENABLED: enabled,
    BASE_URL: import.meta.env.VITE_CLOUD_BASE_URL || 'http://localhost:9000',
    WS_URL: import.meta.env.VITE_CLOUD_WS_URL || 'ws://localhost:9000',
  };
};

export const cloudConfig = validateCloudConfig();

// Determine which backend to use
export const apiBaseUrl = cloudConfig.ENABLED
  ? cloudConfig.BASE_URL
  : env.API_BASE_URL;
```

### 1.3 Environment Variables

Create `.env` file in `local_frontend/`:

```bash
# Local Backend Mode (default)
VITE_API_BASE_URL=http://localhost:8000
VITE_CLOUD_ENABLED=false

# Cloud Backend Mode (optional)
VITE_CLOUD_ENABLED=true
VITE_CLOUD_BASE_URL=http://localhost:9000
VITE_CLOUD_WS_URL=ws://localhost:9000

# Production Cloud Mode
# VITE_CLOUD_ENABLED=true
# VITE_CLOUD_BASE_URL=https://cloud.agentverse.com
# VITE_CLOUD_WS_URL=wss://cloud.agentverse.com
```

### 1.4 API Endpoints

Cloud backend provides these REST API endpoints:

```typescript
// Cloud API Endpoints
export const CLOUD_API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/v1/auth/login/',
    LOGOUT: '/api/v1/auth/logout/',
    REGISTER: '/api/v1/auth/register/',
    REFRESH: '/api/v1/auth/refresh/',
    ME: '/api/v1/auth/me/',
  },

  // Agents
  AGENTS: {
    LIST: '/api/v1/agents/',
    CREATE: '/api/v1/agents/',
    DETAIL: (id: string) => `/api/v1/agents/${id}/`,
    UPDATE: (id: string) => `/api/v1/agents/${id}/`,
    DELETE: (id: string) => `/api/v1/agents/${id}/`,
    EXECUTE: (id: string) => `/api/v1/agents/${id}/execute/`,
  },

  // Tools
  TOOLS: {
    LIST: '/api/v1/tools/',
    CREATE: '/api/v1/tools/',
    DETAIL: (id: string) => `/api/v1/tools/${id}/`,
    UPDATE: (id: string) => `/api/v1/tools/${id}/`,
    DELETE: (id: string) => `/api/v1/tools/${id}/`,
  },

  // MCP Servers
  MCP: {
    LIST: '/api/v1/mcp-servers/',
    CREATE: '/api/v1/mcp-servers/',
    DETAIL: (id: string) => `/api/v1/mcp-servers/${id}/`,
    UPDATE: (id: string) => `/api/v1/mcp-servers/${id}/`,
    DELETE: (id: string) => `/api/v1/mcp-servers/${id}/`,
  },

  // Groups
  GROUPS: {
    LIST: '/api/v1/groups/',
    CREATE: '/api/v1/groups/',
    DETAIL: (id: string) => `/api/v1/groups/${id}/`,
    UPDATE: (id: string) => `/api/v1/groups/${id}/`,
    DELETE: (id: string) => `/api/v1/groups/${id}/`,
  },

  // Messages
  MESSAGES: {
    LIST: (groupId: string) => `/api/v1/groups/${groupId}/messages/`,
    CREATE: (groupId: string) => `/api/v1/groups/${groupId}/messages/`,
    DETAIL: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
    UPDATE: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
    DELETE: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
  },

  // Documents
  DOCUMENTS: {
    LIST: (groupId: string) => `/api/v1/groups/${groupId}/documents/`,
    UPLOAD: (groupId: string) => `/api/v1/groups/${groupId}/documents/upload/`,
    DELETE: (groupId: string, docId: string) => `/api/v1/groups/${groupId}/documents/${docId}/`,
  },

  // Analytics
  ANALYTICS: {
    DASHBOARD: '/api/v1/analytics/dashboard/',
    MESSAGES: '/api/v1/analytics/messages/',
    AGENTS: '/api/v1/analytics/agents/',
  },
};
```

## 2. Authentication Integration

### 2.1 JWT Token Management

```typescript
// local_frontend/src/lib/auth/cloudAuth.ts

interface AuthTokens {
  access: string;
  refresh: string;
}

class CloudAuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  // Login and store tokens
  async login(email: string, password: string): Promise<void> {
    const response = await fetch(`${cloudConfig.BASE_URL}/api/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const tokens: AuthTokens = await response.json();
    this.setTokens(tokens);
  }

  // Store tokens
  private setTokens(tokens: AuthTokens): void {
    this.accessToken = tokens.access;
    this.refreshToken = tokens.refresh;

    // Store in localStorage for persistence
    localStorage.setItem('cloud_access_token', tokens.access);
    localStorage.setItem('cloud_refresh_token', tokens.refresh);
  }

  // Get access token
  getAccessToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('cloud_access_token');
    }
    return this.accessToken;
  }

  // Refresh token
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      this.refreshToken = localStorage.getItem('cloud_refresh_token');
    }

    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${cloudConfig.BASE_URL}/api/v1/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: this.refreshToken }),
    });

    if (!response.ok) {
      this.logout();
      throw new Error('Token refresh failed');
    }

    const { access } = await response.json();
    this.accessToken = access;
    localStorage.setItem('cloud_access_token', access);

    return access;
  }

  // Logout
  logout(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('cloud_access_token');
    localStorage.removeItem('cloud_refresh_token');
  }

  // Check if authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

export const cloudAuth = new CloudAuthService();
```

### 2.2 HTTP Client with Auth Interceptor

Update the HTTP client to include JWT authentication:

```typescript
// local_frontend/src/lib/api/cloudClient.ts

import { cloudConfig } from '../config';
import { cloudAuth } from '../auth/cloudAuth';

class CloudHttpClient {
  private async request<T>(
    endpoint: string,
    config: RequestInit = {}
  ): Promise<T> {
    const url = `${cloudConfig.BASE_URL}${endpoint}`;
    const token = cloudAuth.getAccessToken();

    // Add authorization header
    const headers = {
      'Content-Type': 'application/json',
      ...config.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...config,
        headers,
      });

      // Handle 401 (token expired)
      if (response.status === 401) {
        try {
          // Try to refresh token
          await cloudAuth.refreshAccessToken();

          // Retry request with new token
          const newToken = cloudAuth.getAccessToken();
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`;
            return this.request<T>(endpoint, { ...config, headers });
          }
        } catch (refreshError) {
          // Refresh failed, logout user
          cloudAuth.logout();
          throw new Error('Session expired. Please login again.');
        }
      }

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail || `Request failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Cloud API Error: ${endpoint}`, error);
      throw error;
    }
  }

  // HTTP Methods
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const cloudHttpClient = new CloudHttpClient();
```

## 3. WebSocket Integration

### 3.1 WebSocket Client for Real-time Chat

```typescript
// local_frontend/src/lib/websocket/chatWebSocket.ts

import { cloudConfig } from '../config';
import { cloudAuth } from '../auth/cloudAuth';

export interface ChatMessage {
  id: string;
  content: string;
  sender_id: string;
  group_id: string;
  created_at: string;
}

export type ChatEventType =
  | 'message_created'
  | 'message_updated'
  | 'message_deleted'
  | 'typing_indicator'
  | 'user_presence';

export interface ChatEvent {
  type: ChatEventType;
  message?: ChatMessage;
  message_id?: string;
  user_id?: string;
  user_name?: string;
  is_typing?: boolean;
  action?: 'joined' | 'left';
}

class ChatWebSocket {
  private ws: WebSocket | null = null;
  private groupId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private messageHandlers: ((event: ChatEvent) => void)[] = [];

  // Connect to chat WebSocket
  connect(groupId: string): void {
    this.groupId = groupId;
    this.reconnectAttempts = 0;
    this.createConnection();
  }

  private createConnection(): void {
    const token = cloudAuth.getAccessToken();
    if (!token) {
      console.error('Cannot connect to chat: No access token');
      return;
    }

    const wsUrl = `${cloudConfig.WS_URL}/ws/messages/${this.groupId}/?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`Connected to chat for group ${this.groupId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: ChatEvent = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('Chat WebSocket closed');
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.createConnection(), this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }

  private handleMessage(event: ChatEvent): void {
    // Notify all registered handlers
    this.messageHandlers.forEach(handler => handler(event));
  }

  // Register message handler
  onMessage(handler: (event: ChatEvent) => void): () => void {
    this.messageHandlers.push(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
    };
  }

  // Send typing indicator
  sendTypingIndicator(isTyping: boolean): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing_indicator',
        is_typing: isTyping,
      }));
    }
  }

  // Disconnect
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageHandlers = [];
  }
}

export const chatWebSocket = new ChatWebSocket();
```

### 3.2 WebSocket Client for Cloud Sync

```typescript
// local_frontend/src/lib/websocket/syncWebSocket.ts

import { cloudConfig } from '../config';
import { cloudAuth } from '../auth/cloudAuth';

export type SyncEventType =
  | 'agent_updated'
  | 'tool_updated'
  | 'mcp_updated'
  | 'group_updated';

export interface SyncEvent {
  type: SyncEventType;
  agent?: any;
  tool?: any;
  mcp_server?: any;
  group?: any;
}

class SyncWebSocket {
  private ws: WebSocket | null = null;
  private syncHandlers: ((event: SyncEvent) => void)[] = [];

  // Connect to sync WebSocket
  connect(): void {
    const token = cloudAuth.getAccessToken();
    if (!token) {
      console.error('Cannot connect to sync: No access token');
      return;
    }

    const wsUrl = `${cloudConfig.WS_URL}/ws/sync/?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('Connected to cloud sync channel');
      };

      this.ws.onmessage = (event) => {
        try {
          const data: SyncEvent = JSON.parse(event.data);
          this.handleSync(data);
        } catch (error) {
          console.error('Error parsing sync message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Sync WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('Sync WebSocket closed');
        // Auto-reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000);
      };
    } catch (error) {
      console.error('Error creating sync WebSocket:', error);
    }
  }

  private handleSync(event: SyncEvent): void {
    console.log('Received sync event:', event.type);

    // Notify all registered handlers
    this.syncHandlers.forEach(handler => handler(event));
  }

  // Register sync handler
  onSync(handler: (event: SyncEvent) => void): () => void {
    this.syncHandlers.push(handler);

    // Return unsubscribe function
    return () => {
      this.syncHandlers = this.syncHandlers.filter(h => h !== handler);
    };
  }

  // Disconnect
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.syncHandlers = [];
  }
}

export const syncWebSocket = new SyncWebSocket();
```

## 4. React Integration Examples

### 4.1 Using Cloud API in Components

```typescript
// Example: AgentManagementPanel.tsx

import { useEffect, useState } from 'react';
import { cloudHttpClient } from '../lib/api/cloudClient';
import { CLOUD_API_ENDPOINTS } from '../lib/config';

interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  tools: string[];
}

export function AgentManagementPanel() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch agents from cloud
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const data = await cloudHttpClient.get<Agent[]>(
        CLOUD_API_ENDPOINTS.AGENTS.LIST
      );
      setAgents(data);
    } catch (error) {
      console.error('Error loading agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const createAgent = async (agentData: Partial<Agent>) => {
    try {
      const newAgent = await cloudHttpClient.post<Agent>(
        CLOUD_API_ENDPOINTS.AGENTS.CREATE,
        agentData
      );
      setAgents([...agents, newAgent]);
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const updateAgent = async (id: string, agentData: Partial<Agent>) => {
    try {
      const updated = await cloudHttpClient.put<Agent>(
        CLOUD_API_ENDPOINTS.AGENTS.UPDATE(id),
        agentData
      );
      setAgents(agents.map(a => a.id === id ? updated : a));
    } catch (error) {
      console.error('Error updating agent:', error);
    }
  };

  const deleteAgent = async (id: string) => {
    try {
      await cloudHttpClient.delete(
        CLOUD_API_ENDPOINTS.AGENTS.DELETE(id)
      );
      setAgents(agents.filter(a => a.id !== id));
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  return (
    <div>
      {loading ? <p>Loading...</p> : (
        <ul>
          {agents.map(agent => (
            <li key={agent.id}>
              {agent.name}
              <button onClick={() => deleteAgent(agent.id)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### 4.2 Using WebSocket in Components

```typescript
// Example: ConversationView.tsx

import { useEffect, useState } from 'react';
import { chatWebSocket, ChatEvent } from '../lib/websocket/chatWebSocket';

export function ConversationView({ groupId }: { groupId: string }) {
  const [messages, setMessages] = useState<ChatEvent[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  useEffect(() => {
    // Connect to chat WebSocket
    chatWebSocket.connect(groupId);

    // Subscribe to messages
    const unsubscribe = chatWebSocket.onMessage((event: ChatEvent) => {
      switch (event.type) {
        case 'message_created':
          setMessages(prev => [...prev, event]);
          break;

        case 'message_updated':
          setMessages(prev =>
            prev.map(msg =>
              msg.message?.id === event.message?.id ? event : msg
            )
          );
          break;

        case 'message_deleted':
          setMessages(prev =>
            prev.filter(msg => msg.message?.id !== event.message_id)
          );
          break;

        case 'typing_indicator':
          if (event.is_typing && event.user_name) {
            setTypingUsers(prev => [...prev, event.user_name!]);
          } else if (event.user_name) {
            setTypingUsers(prev => prev.filter(u => u !== event.user_name));
          }
          break;

        case 'user_presence':
          console.log(`User ${event.user_name} ${event.action}`);
          break;
      }
    });

    // Cleanup on unmount
    return () => {
      unsubscribe();
      chatWebSocket.disconnect();
    };
  }, [groupId]);

  const handleTyping = () => {
    chatWebSocket.sendTypingIndicator(true);
    setTimeout(() => chatWebSocket.sendTypingIndicator(false), 3000);
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i}>{msg.message?.content}</div>
        ))}
      </div>

      {typingUsers.length > 0 && (
        <div className="typing-indicator">
          {typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...
        </div>
      )}

      <input
        type="text"
        onChange={handleTyping}
        placeholder="Type a message..."
      />
    </div>
  );
}
```

### 4.3 Using Cloud Sync

```typescript
// Example: App.tsx - Global sync listener

import { useEffect } from 'react';
import { syncWebSocket, SyncEvent } from '../lib/websocket/syncWebSocket';

export function App() {
  useEffect(() => {
    // Connect to sync WebSocket
    syncWebSocket.connect();

    // Subscribe to sync events
    const unsubscribe = syncWebSocket.onSync((event: SyncEvent) => {
      console.log('Sync event received:', event.type);

      switch (event.type) {
        case 'agent_updated':
          // Update local agent cache
          console.log('Agent updated:', event.agent);
          // Trigger re-fetch or update local state
          break;

        case 'tool_updated':
          console.log('Tool updated:', event.tool);
          break;

        case 'mcp_updated':
          console.log('MCP server updated:', event.mcp_server);
          break;

        case 'group_updated':
          console.log('Group updated:', event.group);
          break;
      }
    });

    // Cleanup
    return () => {
      unsubscribe();
      syncWebSocket.disconnect();
    };
  }, []);

  return <div>{/* Your app */}</div>;
}
```

## 5. Testing

### 5.1 Test Cloud API Connection

```bash
cd local_frontend

# Create .env file
cat > .env << EOF
VITE_CLOUD_ENABLED=true
VITE_CLOUD_BASE_URL=http://localhost:9000
VITE_CLOUD_WS_URL=ws://localhost:9000
EOF

# Install dependencies
npm install

# Start frontend
npm run dev
```

### 5.2 Test WebSocket Connection

Open browser console and run:

```javascript
// Test chat WebSocket
const ws = new WebSocket('ws://localhost:9000/ws/messages/<group-id>/?token=<your-jwt>');
ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));

// Send typing indicator
ws.send(JSON.stringify({ type: 'typing_indicator', is_typing: true }));
```

## 6. Deployment Checklist

- [ ] Update `.env` with production cloud URLs
- [ ] Enable HTTPS/WSS for production
- [ ] Configure CORS in cloud backend
- [ ] Test authentication flow
- [ ] Test WebSocket connections
- [ ] Monitor WebSocket reconnection
- [ ] Implement offline message queue
- [ ] Add error boundaries for API failures
- [ ] Add loading states for all API calls
- [ ] Implement retry logic for failed requests

## 7. Troubleshooting

### Issue: WebSocket connection fails

**Solution:**
- Verify JWT token is valid
- Check WebSocket URL format (ws:// or wss://)
- Ensure cloud backend is running
- Check CORS configuration

### Issue: 401 Unauthorized errors

**Solution:**
- Check if access token is included in headers
- Verify token hasn't expired
- Implement token refresh logic

### Issue: Messages not appearing in real-time

**Solution:**
- Verify WebSocket is connected (check browser console)
- Check if Django signals are registered
- Ensure Redis is running (for production)
- Verify channel layer configuration

## Next Steps

1. Complete integration of all CRUD operations
2. Add optimistic UI updates
3. Implement local caching strategy
4. Add offline support
5. Test with production data
6. Implement WebSocket heartbeat
7. Add connection status indicator
8. Build reconnection UI feedback
