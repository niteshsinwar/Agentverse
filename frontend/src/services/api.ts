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
      const errorData = await response.json().catch(() => null);
      const error = new Error(`API request failed: ${response.statusText}`);

      // Attach validation errors if present
      if (errorData?.detail?.validation_errors) {
        (error as any).validation_errors = errorData.detail.validation_errors;
      } else if (errorData?.detail && typeof errorData.detail === 'object') {
        (error as any).validation_errors = errorData.detail;
      }

      throw error;
    }

    return response.json();
  }

  // Groups
  async getGroups() {
    return this.request('/api/v1/groups');
  }

  async createGroup(name: string) {
    return this.request('/api/v1/groups', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async deleteGroup(groupId: string) {
    return this.request(`/api/v1/groups/${groupId}`, {
      method: 'DELETE',
    });
  }

  // Agents
  async getAvailableAgents() {
    return this.request('/api/v1/agents');
  }

  async getGroupAgents(groupId: string) {
    return this.request(`/api/v1/groups/${groupId}/agents`);
  }

  async addAgentToGroup(groupId: string, agentKey: string) {
    return this.request(`/api/v1/groups/${groupId}/agents`, {
      method: 'POST',
      body: JSON.stringify({ agent_key: agentKey }),
    });
  }

  async removeAgentFromGroup(groupId: string, agentKey: string) {
    return this.request(`/api/v1/groups/${groupId}/agents/${agentKey}`, {
      method: 'DELETE',
    });
  }

  // Messages
  async getGroupMessages(groupId: string) {
    const response = await this.request(`/api/v1/groups/${groupId}/messages`);
    return response || [];
  }

  async sendMessage(groupId: string, agentId: string, message: string) {
    return this.request(`/api/v1/groups/${groupId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        agent_id: agentId,
        message,
      }),
    });
  }

  // Documents
  async getGroupDocuments(groupId: string) {
    return this.request(`/api/v1/groups/${groupId}/documents/`);
  }

  async uploadDocument(groupId: string, agentId: string, file: File, message: string = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('agent_id', agentId);
    formData.append('message', message); // Include message context like Gradio

    const response = await fetch(`${API_BASE_URL}/api/v1/groups/${groupId}/documents/upload/`, {
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
    return this.request('/api/v1/agents/create/', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async validateAgent(agentData: any) {
    return this.request('/api/v1/agents/test-register/', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async updateAgent(agentKey: string, agentData: any) {
    return this.request(`/api/v1/agents/${agentKey}/`, {
      method: 'PUT',
      body: JSON.stringify(agentData),
    });
  }

  async deleteAgent(agentKey: string) {
    return this.request(`/api/v1/agents/${agentKey}/`, {
      method: 'DELETE',
    });
  }

  async getSystemInfo() {
    return this.request('/api/v1/analytics/system/modules/');
  }

  // Configuration Management
  // Tools Management
  async getTools() {
    return this.request('/api/v1/config/tools/');
  }

  async addTool(toolId: string, toolData: any) {
    return this.request(`/api/v1/config/tools/?tool_id=${toolId}`, {
      method: 'POST',
      body: JSON.stringify(toolData),
    });
  }

  async updateTool(toolId: string, toolData: any) {
    return this.request(`/api/v1/config/tools/${toolId}`, {
      method: 'PUT',
      body: JSON.stringify(toolData),
    });
  }

  async deleteTool(toolId: string) {
    return this.request(`/api/v1/config/tools/${toolId}`, {
      method: 'DELETE',
    });
  }

  // MCP Management
  async getMcpServers() {
    return this.request('/api/v1/config/mcp/');
  }

  async addMcpServer(mcpId: string, mcpData: any) {
    return this.request(`/api/v1/config/mcp/?mcp_id=${mcpId}`, {
      method: 'POST',
      body: JSON.stringify(mcpData),
    });
  }

  async updateMcpServer(mcpId: string, mcpData: any) {
    return this.request(`/api/v1/config/mcp/${mcpId}`, {
      method: 'PUT',
      body: JSON.stringify(mcpData),
    });
  }

  async deleteMcpServer(mcpId: string) {
    return this.request(`/api/v1/config/mcp/${mcpId}`, {
      method: 'DELETE',
    });
  }

  // Settings Management
  async getSettings() {
    return this.request('/api/v1/config/settings/');
  }

  async updateSettings(settings: any) {
    return this.request('/api/v1/config/settings/', {
      method: 'POST',
      body: JSON.stringify({ settings }),
    });
  }

  async resetSettings() {
    return this.request('/api/v1/config/settings/', {
      method: 'DELETE',
    });
  }

  async validateSettings() {
    return this.request('/api/v1/config/settings/validate/');
  }

  async getConfigStatus() {
    return this.request('/api/v1/config/status/');
  }

  async createConfigBackup() {
    return this.request('/api/v1/config/backup/', {
      method: 'POST',
    });
  }

  // ===== VALIDATION ENDPOINTS =====
  // These endpoints validate configurations before creation/modification

  // Agent Validation
  async validateAgentConfig(agentData: any) {
    return this.request('/api/v1/config/validate/agent/', {
      method: 'POST',
      body: JSON.stringify(agentData),
    });
  }

  async validateAgentFolder(folderPath: string) {
    return this.request('/api/v1/config/validate/agent/folder/', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath }),
    });
  }

  // Tool Validation
  async validateToolConfig(toolData: any) {
    return this.request('/api/v1/config/validate/tool/', {
      method: 'POST',
      body: JSON.stringify(toolData),
    });
  }

  async validateToolCode(code: string, functionNames: string[] = []) {
    return this.request('/api/v1/config/validate/tool/code/', {
      method: 'POST',
      body: JSON.stringify({
        code,
        function_names: functionNames
      }),
    });
  }

  // MCP Validation
  async validateMcpConfig(mcpData: any) {
    return this.request('/api/v1/config/validate/mcp/', {
      method: 'POST',
      body: JSON.stringify(mcpData),
    });
  }

  async validateMcpConnectivity(name: string, config: any, timeout: number = 10.0) {
    return this.request('/api/v1/config/validate/mcp/connectivity/', {
      method: 'POST',
      body: JSON.stringify({
        name,
        config,
        timeout
      }),
    });
  }

  // Templates
  async getToolTemplates() {
    return this.request('/api/v1/config/validate/templates/tools/');
  }

  async getMcpTemplates() {
    return this.request('/api/v1/config/validate/templates/mcp/');
  }

  // Events (Server-Sent Events)
  createEventStream(groupId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/api/v1/groups/${groupId}/events/`);
  }
}

export const apiService = new ApiService();