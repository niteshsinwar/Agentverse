/**
 * Tools API
 * API endpoints for tools management
 */

import { httpClient } from '../client/http-client';
import type {
  Tool,
  ToolTemplate,
  CreateToolRequest,
  UpdateToolRequest,
  ValidateToolRequest,
} from '../types/entities';

export interface ToolValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  functions_found: string[];
  syntax_check: {
    valid: boolean;
    error?: string;
  };
}

export const toolsApi = {
  // Tool CRUD operations
  async getTools(): Promise<{tools: Record<string, any>, count: number}> {
    return httpClient.get<{tools: Record<string, any>, count: number}>('/api/v1/config/tools/');
  },

  async getTool(toolId: string): Promise<Tool> {
    return httpClient.get<Tool>(`/api/v1/config/tools/${toolId}`);
  },

  async createTool(toolId: string, data: CreateToolRequest): Promise<Tool> {
    return httpClient.post<Tool>(`/api/v1/config/tools/?tool_id=${toolId}`, data);
  },

  async updateTool(toolId: string, data: UpdateToolRequest): Promise<Tool> {
    return httpClient.put<Tool>(`/api/v1/config/tools/${toolId}`, data);
  },

  async deleteTool(toolId: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/config/tools/${toolId}`);
  },

  // Tool validation
  async validateTool(data: CreateToolRequest): Promise<ToolValidationResult> {
    return httpClient.post<ToolValidationResult>('/api/v1/config/validate/tool/', data);
  },

  async validateToolCode(data: ValidateToolRequest): Promise<ToolValidationResult> {
    return httpClient.post<ToolValidationResult>('/api/v1/config/validate/tool/code/', data);
  },

  // Tool templates
  async getToolTemplates(): Promise<{templates: ToolTemplate[], base_template: string}> {
    return httpClient.get<{templates: ToolTemplate[], base_template: string}>('/api/v1/config/validate/templates/tools/');
  },
};