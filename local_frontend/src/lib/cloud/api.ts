/**
 * Cloud API Client
 *
 * Provides methods to fetch tenant-specific data from cloud backend.
 * All requests are proxied through local_backend.
 */

import { cloudConfig, CLOUD_ENDPOINTS } from './config';
import { cloudAuth } from './auth';

/**
 * Generic API request wrapper with authentication
 */
async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = cloudAuth.getAccessToken();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// GROUPS API
// ============================================================================

export interface Group {
  id: string;
  name: string;
  description: string;
  color?: string;
  member_count?: number;
  created_at?: string;
  updated_at?: string;
}

export async function fetchGroups(): Promise<Group[]> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.groups.list}`;

  const response = await apiRequest<{ groups: Group[] }>(url);
  return response.groups || [];
}

export async function createGroup(data: Partial<Group>): Promise<Group> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.groups.create}`;

  return apiRequest<Group>(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// USERS API
// ============================================================================

export interface TenantUser {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
  status: 'active' | 'inactive';
  groups: string[];
  last_active?: string;
  joined_at?: string;
}

export async function fetchUsers(): Promise<TenantUser[]> {
  const config = cloudConfig();
  // Note: This endpoint doesn't exist yet in cloud_proxy.py
  // For now, return empty array until backend is updated
  try {
    const url = `${config.baseUrl}/api/v1/cloud/users`;
    const response = await apiRequest<{ users: TenantUser[] }>(url);
    return response.users || [];
  } catch (error) {
    console.warn('Users endpoint not implemented yet:', error);
    return [];
  }
}

// ============================================================================
// AGENTS API
// ============================================================================

export interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'agent';
  created_by?: string;
  created_at?: string;
}

export async function fetchAgents(): Promise<Agent[]> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.agents.list}`;

  const response = await apiRequest<{ agents: Agent[] }>(url);
  return response.agents || [];
}

// ============================================================================
// TOOLS API
// ============================================================================

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: 'tool';
  created_by?: string;
  created_at?: string;
}

export async function fetchTools(): Promise<Tool[]> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.tools.list}`;

  const response = await apiRequest<{ tools: Tool[] }>(url);
  return response.tools || [];
}

// ============================================================================
// MCP SERVERS API
// ============================================================================

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  type: 'mcp';
  is_protected?: boolean;
  created_by?: string;
  created_at?: string;
}

export async function fetchMCPServers(): Promise<MCPServer[]> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.mcp.list}`;

  const response = await apiRequest<{ mcp_servers: MCPServer[] }>(url);
  return response.mcp_servers || [];
}

// ============================================================================
// CACHE STATUS API
// ============================================================================

export interface CacheStatus {
  last_sync: string | null;
  counts: {
    agents: number;
    tools: number;
    mcp_servers: number;
    groups: number;
    users: number;
  };
}

export async function fetchCacheStatus(): Promise<CacheStatus> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.cache.status}`;

  return apiRequest<CacheStatus>(url);
}

export async function refreshCache(): Promise<void> {
  const config = cloudConfig();
  const url = `${config.baseUrl}${CLOUD_ENDPOINTS.cache.refresh}`;

  await apiRequest<{ message: string }>(url, { method: 'POST' });
}
