// API service for communicating with Python FastAPI backend
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Groups
  async getGroups() {
    return this.request('/api/groups');
  }

  async createGroup(name: string) {
    return this.request('/api/groups', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async deleteGroup(groupId: string) {
    return this.request(`/api/groups/${groupId}`, {
      method: 'DELETE',
    });
  }

  // Agents
  async getAvailableAgents() {
    return this.request('/api/agents');
  }

  async getGroupAgents(groupId: string) {
    return this.request(`/api/groups/${groupId}/agents`);
  }

  async addAgentToGroup(groupId: string, agentKey: string) {
    return this.request(`/api/groups/${groupId}/agents`, {
      method: 'POST',
      body: JSON.stringify({ agent_key: agentKey }),
    });
  }

  async removeAgentFromGroup(groupId: string, agentKey: string) {
    return this.request(`/api/groups/${groupId}/agents/${agentKey}`, {
      method: 'DELETE',
    });
  }

  // Messages
  async getGroupMessages(groupId: string) {
    const response = await this.request(`/api/groups/${groupId}/messages`);
    return response || [];
  }

  async sendMessage(groupId: string, agentId: string, message: string) {
    return this.request(`/api/groups/${groupId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        agent_id: agentId,
        message,
      }),
    });
  }

  // Documents
  async getGroupDocuments(groupId: string) {
    return this.request(`/api/groups/${groupId}/documents`);
  }

  async uploadDocument(groupId: string, agentId: string, file: File, message: string = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('agent_id', agentId);
    formData.append('message', message); // Include message context like Gradio

    const response = await fetch(`${API_BASE_URL}/api/groups/${groupId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Document upload failed: ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  // Agent Management
  async createAgent(agentData: any) {
    return this.request('/api/agents/create', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async validateAgent(agentData: any) {
    return this.request('/api/agents/test-register', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async updateAgent(agentKey: string, agentData: any) {
    return this.request(`/api/agents/${agentKey}`, {
      method: 'PUT',
      body: JSON.stringify(agentData),
    });
  }

  async deleteAgent(agentKey: string) {
    return this.request(`/api/agents/${agentKey}`, {
      method: 'DELETE',
    });
  }

  async getSystemInfo() {
    return this.request('/api/system/modules');
  }

  // Events (Server-Sent Events)
  createEventStream(groupId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/api/groups/${groupId}/events`);
  }
}

export const apiService = new ApiService();