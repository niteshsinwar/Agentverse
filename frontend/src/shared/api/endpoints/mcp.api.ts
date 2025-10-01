/**
 * MCP API
 * API endpoints for MCP (Model Context Protocol) management
 */

import { httpClient } from '../client/http-client';
import type {
  McpServer,
  McpTemplate,
  CreateMcpServerRequest,
  UpdateMcpServerRequest,
  ValidateMcpRequest,
} from '../types/entities';

export interface McpValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  connection_test?: {
    success: boolean;
    message: string;
    tools_found?: string[];
  };
}

export const mcpApi = {
  // MCP Server CRUD operations
  async getMcpServers(): Promise<{mcpServers: Record<string, any>, count: number}> {
    return httpClient.get<{mcpServers: Record<string, any>, count: number}>('/api/v1/config/mcp/');
  },

  async getMcpServer(mcpId: string): Promise<McpServer> {
    return httpClient.get<McpServer>(`/api/v1/config/mcp/${mcpId}`);
  },

  async createMcpServer(mcpId: string, data: CreateMcpServerRequest): Promise<McpServer> {
    return httpClient.post<McpServer>(`/api/v1/config/mcp/?mcp_id=${mcpId}`, data);
  },

  async updateMcpServer(mcpId: string, data: UpdateMcpServerRequest): Promise<McpServer> {
    return httpClient.put<McpServer>(`/api/v1/config/mcp/${mcpId}`, data);
  },

  async deleteMcpServer(mcpId: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/config/mcp/${mcpId}`);
  },

  // MCP validation
  async validateMcpServer(data: CreateMcpServerRequest): Promise<McpValidationResult> {
    return httpClient.post<McpValidationResult>('/api/v1/config/validate/mcp/', data);
  },

  async validateMcpConnectivity(data: ValidateMcpRequest): Promise<McpValidationResult> {
    return httpClient.post<McpValidationResult>('/api/v1/config/validate/mcp/connectivity/', data);
  },

  // MCP templates
  async getMcpTemplates(): Promise<McpTemplate[]> {
    const response = await httpClient.get<{templates: McpTemplate[]}>('/api/v1/config/validate/templates/mcp/');
    return response.templates;
  },
};