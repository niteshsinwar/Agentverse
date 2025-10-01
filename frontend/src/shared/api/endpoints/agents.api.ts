/**
 * Agents API
 * API endpoints for agent management
 */

import { httpClient } from '../client/http-client';
import type {
  Agent,
  CreateAgentRequest,
  UpdateAgentRequest,
  ValidateAgentRequest,
} from '../types/entities';

export interface AgentValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  agent_preview?: Agent;
}

export interface AgentFolderValidation {
  is_valid: boolean;
  errors: string[];
  found_files: string[];
  agent_config?: any;
}

export const agentsApi = {
  // Agent CRUD operations
  async getAgents(): Promise<Agent[]> {
    return httpClient.get<Agent[]>('/api/v1/agents');
  },

  async getAgent(agentKey: string): Promise<Agent> {
    return httpClient.get<Agent>(`/api/v1/agents/${agentKey}`);
  },

  async createAgent(data: CreateAgentRequest): Promise<Agent> {
    return httpClient.post<Agent>('/api/v1/agents/create/', data);
  },

  async updateAgent(agentKey: string, data: UpdateAgentRequest): Promise<Agent> {
    return httpClient.put<Agent>(`/api/v1/agents/${agentKey}/`, data);
  },

  async deleteAgent(agentKey: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/agents/${agentKey}/`);
  },

  // Agent validation
  async validateAgent(data: ValidateAgentRequest): Promise<AgentValidationResult> {
    return httpClient.post<AgentValidationResult>('/api/v1/agents/test-register/', data);
  },

  async validateAgentConfig(data: CreateAgentRequest): Promise<AgentValidationResult> {
    return httpClient.post<AgentValidationResult>('/api/v1/config/validate/agent/', data);
  },

  async validateAgentFolder(folderPath: string): Promise<AgentFolderValidation> {
    return httpClient.post<AgentFolderValidation>('/api/v1/config/validate/agent/folder/', {
      folder_path: folderPath,
    });
  },
};