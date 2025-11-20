/**
 * Cloud Backend Configuration
 *
 * Manages connection to cloud backend for multi-tenant operations.
 */

export interface CloudConfig {
  enabled: boolean;
  baseUrl: string;
  wsUrl: string;
  apiVersion: string;
}

/**
 * Get cloud configuration from environment variables
 *
 * IMPORTANT: Frontend MUST call local_backend proxy, NOT cloud_backend directly!
 * Architecture: Frontend → Local Backend (port 8000) → Cloud Backend (port 9000)
 */
export function getCloudConfig(): CloudConfig {
  const enabled = import.meta.env.VITE_CLOUD_ENABLED === 'true';

  // CRITICAL: Use local_backend URL, NOT cloud_backend!
  // All cloud requests are proxied through local_backend
  const baseUrl = import.meta.env.VITE_LOCAL_BACKEND_URL || 'http://localhost:8000';

  // Convert HTTP URL to WebSocket URL
  const wsUrl = baseUrl
    .replace('http://', 'ws://')
    .replace('https://', 'wss://');

  return {
    enabled,
    baseUrl,
    wsUrl,
    apiVersion: 'v1',
  };
}

/**
 * Cloud API endpoints (via local_backend proxy)
 *
 * All endpoints use /api/v1/cloud/ prefix to route through local_backend proxy
 */
export const CLOUD_ENDPOINTS = {
  // Authentication (proxied through local_backend)
  auth: {
    login: '/api/v1/cloud/auth/login',
    logout: '/api/v1/cloud/auth/logout',
    refresh: '/api/v1/cloud/auth/refresh',
    me: '/api/v1/cloud/auth/me',
  },

  // Agents (proxied through local_backend)
  agents: {
    list: '/api/v1/cloud/agents',
    create: '/api/v1/cloud/agents',
    detail: (id: string) => `/api/v1/cloud/agents/${id}`,
    update: (id: string) => `/api/v1/cloud/agents/${id}`,
    delete: (id: string) => `/api/v1/cloud/agents/${id}`,
    execute: (id: string) => `/api/v1/cloud/agents/${id}/execute`,
  },

  // Tools (proxied through local_backend)
  tools: {
    list: '/api/v1/cloud/tools',
    create: '/api/v1/cloud/tools',
    detail: (id: string) => `/api/v1/cloud/tools/${id}`,
    update: (id: string) => `/api/v1/cloud/tools/${id}`,
    delete: (id: string) => `/api/v1/cloud/tools/${id}`,
  },

  // MCP Servers (proxied through local_backend)
  mcp: {
    list: '/api/v1/cloud/mcp-servers',
    create: '/api/v1/cloud/mcp-servers',
    detail: (id: string) => `/api/v1/cloud/mcp-servers/${id}`,
    update: (id: string) => `/api/v1/cloud/mcp-servers/${id}`,
    delete: (id: string) => `/api/v1/cloud/mcp-servers/${id}`,
  },

  // Groups (proxied through local_backend)
  groups: {
    list: '/api/v1/cloud/groups',
    create: '/api/v1/cloud/groups',
    detail: (id: string) => `/api/v1/cloud/groups/${id}`,
    update: (id: string) => `/api/v1/cloud/groups/${id}`,
    delete: (id: string) => `/api/v1/cloud/groups/${id}`,
  },

  // Messages (proxied through local_backend)
  messages: {
    list: (groupId: string) => `/api/v1/cloud/groups/${groupId}/messages`,
    create: (groupId: string) => `/api/v1/cloud/groups/${groupId}/messages`,
    detail: (groupId: string, msgId: string) => `/api/v1/cloud/groups/${groupId}/messages/${msgId}`,
    update: (groupId: string, msgId: string) => `/api/v1/cloud/groups/${groupId}/messages/${msgId}`,
    delete: (groupId: string, msgId: string) => `/api/v1/cloud/groups/${groupId}/messages/${msgId}`,
  },

  // Documents (proxied through local_backend)
  documents: {
    list: (groupId: string) => `/api/v1/cloud/groups/${groupId}/documents`,
    upload: (groupId: string) => `/api/v1/cloud/groups/${groupId}/documents/upload`,
    delete: (groupId: string, docId: string) => `/api/v1/cloud/groups/${groupId}/documents/${docId}`,
  },

  // Analytics (proxied through local_backend)
  analytics: {
    dashboard: '/api/v1/cloud/analytics/dashboard',
    messages: '/api/v1/cloud/analytics/messages',
    agents: '/api/v1/cloud/analytics/agents',
  },

  // Cache Management (local_backend specific)
  cache: {
    status: '/api/v1/cloud/cache/status',
    refresh: '/api/v1/cloud/cache/refresh',
  },

  // WebSocket (proxied through local_backend)
  websocket: {
    messages: (groupId: string) => `/ws/cloud/messages/${groupId}`,
    sync: '/ws/cloud/sync',
  },
};

// Singleton config
let cachedConfig: CloudConfig | null = null;

/**
 * Get cached cloud configuration
 */
export function cloudConfig(): CloudConfig {
  if (!cachedConfig) {
    cachedConfig = getCloudConfig();
  }
  return cachedConfig;
}
