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
 */
export function getCloudConfig(): CloudConfig {
  const enabled = import.meta.env.VITE_CLOUD_ENABLED === 'true';
  const baseUrl = import.meta.env.VITE_CLOUD_BASE_URL || 'http://localhost:9000';

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
 * Cloud API endpoints
 */
export const CLOUD_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/api/v1/auth/login/',
    logout: '/api/v1/auth/logout/',
    refresh: '/api/v1/auth/refresh/',
    me: '/api/v1/auth/me/',
  },

  // Agents
  agents: {
    list: '/api/v1/agents/',
    create: '/api/v1/agents/',
    detail: (id: string) => `/api/v1/agents/${id}/`,
    update: (id: string) => `/api/v1/agents/${id}/`,
    delete: (id: string) => `/api/v1/agents/${id}/`,
    execute: (id: string) => `/api/v1/agents/${id}/execute/`,
  },

  // Tools
  tools: {
    list: '/api/v1/tools/',
    create: '/api/v1/tools/',
    detail: (id: string) => `/api/v1/tools/${id}/`,
    update: (id: string) => `/api/v1/tools/${id}/`,
    delete: (id: string) => `/api/v1/tools/${id}/`,
  },

  // MCP Servers
  mcp: {
    list: '/api/v1/mcp-servers/',
    create: '/api/v1/mcp-servers/',
    detail: (id: string) => `/api/v1/mcp-servers/${id}/`,
    update: (id: string) => `/api/v1/mcp-servers/${id}/`,
    delete: (id: string) => `/api/v1/mcp-servers/${id}/`,
  },

  // Groups
  groups: {
    list: '/api/v1/groups/',
    create: '/api/v1/groups/',
    detail: (id: string) => `/api/v1/groups/${id}/`,
    update: (id: string) => `/api/v1/groups/${id}/`,
    delete: (id: string) => `/api/v1/groups/${id}/`,
  },

  // Messages
  messages: {
    list: (groupId: string) => `/api/v1/groups/${groupId}/messages/`,
    create: (groupId: string) => `/api/v1/groups/${groupId}/messages/`,
    detail: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
    update: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
    delete: (groupId: string, msgId: string) => `/api/v1/groups/${groupId}/messages/${msgId}/`,
  },

  // Documents
  documents: {
    list: (groupId: string) => `/api/v1/groups/${groupId}/documents/`,
    upload: (groupId: string) => `/api/v1/groups/${groupId}/documents/upload/`,
    delete: (groupId: string, docId: string) => `/api/v1/groups/${groupId}/documents/${docId}/`,
  },

  // Analytics
  analytics: {
    dashboard: '/api/v1/analytics/dashboard/',
    messages: '/api/v1/analytics/messages/',
    agents: '/api/v1/analytics/agents/',
  },

  // WebSocket
  websocket: {
    messages: (groupId: string) => `/ws/messages/${groupId}/`,
    sync: '/ws/sync/',
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
