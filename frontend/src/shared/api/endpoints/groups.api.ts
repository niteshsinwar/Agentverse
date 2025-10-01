/**
 * Groups API
 * API endpoints for group management
 */

import { httpClient } from '../client/http-client';
import type {
  Group,
  Agent,
  Message,
  Document,
  CreateGroupRequest,
  UpdateGroupRequest,
  SendMessageRequest,
  UploadDocumentRequest,
} from '../types/entities';

export const groupsApi = {
  // Group CRUD operations
  async getGroups(): Promise<Group[]> {
    return httpClient.get<Group[]>('/api/v1/groups');
  },

  async createGroup(data: CreateGroupRequest): Promise<Group> {
    return httpClient.post<Group>('/api/v1/groups', data);
  },

  async updateGroup(groupId: string, data: UpdateGroupRequest): Promise<Group> {
    return httpClient.put<Group>(`/api/v1/groups/${groupId}`, data);
  },

  async deleteGroup(groupId: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/groups/${groupId}`);
  },

  // Group agents
  async getGroupAgents(groupId: string): Promise<Agent[]> {
    return httpClient.get<Agent[]>(`/api/v1/groups/${groupId}/agents`);
  },

  async addAgentToGroup(groupId: string, agentKey: string): Promise<void> {
    return httpClient.post<void>(`/api/v1/groups/${groupId}/agents`, {
      agent_key: agentKey,
    });
  },

  async removeAgentFromGroup(groupId: string, agentKey: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/groups/${groupId}/agents/${agentKey}`);
  },

  // Group messages
  async getGroupMessages(groupId: string): Promise<Message[]> {
    const response = await httpClient.get<Message[]>(`/api/v1/groups/${groupId}/messages`);
    return response || [];
  },

  async sendMessage(groupId: string, data: SendMessageRequest): Promise<Message> {
    return httpClient.post<Message>(`/api/v1/groups/${groupId}/messages`, data);
  },

  // Group documents
  async getGroupDocuments(groupId: string): Promise<Document[]> {
    return httpClient.get<Document[]>(`/api/v1/groups/${groupId}/documents/`);
  },

  async uploadDocument(
    groupId: string,
    data: UploadDocumentRequest,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('agent_id', data.agent_id);
    if (data.message) {
      formData.append('message', data.message);
    }

    return httpClient.upload<Document>(
      `/api/v1/groups/${groupId}/documents/upload/`,
      formData,
      { onProgress }
    );
  },

  // Group control
  async stopGroupChain(groupId: string): Promise<void> {
    return httpClient.post<void>(`/api/v1/groups/${groupId}/stop`, {});
  },

  // Server-Sent Events
  createEventStream(groupId: string): EventSource {
    return new EventSource(`${httpClient['baseURL']}/api/v1/groups/${groupId}/events/`);
  },
};