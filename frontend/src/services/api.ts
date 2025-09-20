// Enhanced API service with comprehensive logging and error tracking
const API_BASE_URL = 'http://localhost:8000';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  context?: Record<string, any>;
}

class ApiService {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;

  private log(level: LogEntry['level'], message: string, context?: Record<string, any>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context
    };

    this.logs.unshift(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    // Also log to console in development
    if (process.env.NODE_ENV === 'development') {
      console[level.toLowerCase() as 'info' | 'warn' | 'error' | 'debug']?.(
        `[API] ${message}`,
        context ? context : ''
      );
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const startTime = Date.now();
    const url = `${API_BASE_URL}${endpoint}`;
    const method = options.method || 'GET';

    this.log('DEBUG', `${method} ${endpoint}`, {
      url,
      headers: options.headers,
      bodySize: options.body ? new Blob([options.body as string]).size : 0
    });

    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const duration = Date.now() - startTime;

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const error = new Error(`API request failed: ${response.statusText}`);

        // Enhanced error logging
        this.log('ERROR', `API Error: ${method} ${endpoint}`, {
          status: response.status,
          statusText: response.statusText,
          duration,
          errorData,
          endpoint,
          method,
          requestBody: options.body
        });

        // Attach validation errors if present
        if (errorData?.detail?.validation_errors) {
          (error as any).validation_errors = errorData.detail.validation_errors;
        } else if (errorData?.detail && typeof errorData.detail === 'object') {
          (error as any).validation_errors = errorData.detail;
        }

        throw error;
      }

      // Log successful requests
      this.log('INFO', `${method} ${endpoint} - ${response.status}`, {
        status: response.status,
        duration,
        endpoint,
        method
      });

      // Performance warning for slow requests
      if (duration > 2000) {
        this.log('WARNING', `Slow API request: ${method} ${endpoint}`, {
          duration,
          threshold: 2000,
          endpoint,
          method
        });
      }

      return response.json();

    } catch (error) {
      const duration = Date.now() - startTime;

      // Log network or other errors
      this.log('ERROR', `Request failed: ${method} ${endpoint}`, {
        error: error instanceof Error ? error.message : String(error),
        duration,
        endpoint,
        method,
        type: 'network_error'
      });

      throw error;
    }
  }

  // Get API logs for debugging
  getLogs(level?: LogEntry['level']): LogEntry[] {
    if (level) {
      return this.logs.filter(log => log.level === level);
    }
    return [...this.logs];
  }

  // Clear logs
  clearLogs(): void {
    this.logs = [];
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

  // Logs API
  async getLogSessions() {
    return this.request('/api/v1/logs/sessions');
  }

  async getSessionLogs(sessionId: string, options: {
    format?: 'json' | 'human';
    limit?: number;
    level?: string;
    event_type?: string;
    agent_id?: string;
    from_timestamp?: string;
    to_timestamp?: string;
  } = {}) {
    const params = new URLSearchParams();
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    });

    const endpoint = `/api/v1/logs/sessions/${sessionId}`;
    return this.request(`${endpoint}?${params.toString()}`);
  }

  async getSessionSummary(sessionId: string) {
    return this.request(`/api/v1/logs/sessions/${sessionId}/summary`);
  }

  async getSessionPerformance(sessionId: string) {
    return this.request(`/api/v1/logs/sessions/${sessionId}/performance`);
  }

  async deleteSessionLogs(sessionId: string) {
    return this.request(`/api/v1/logs/sessions/${sessionId}`, { method: 'DELETE' });
  }

  async exportSessionLogs(sessionId: string, format: 'json' | 'zip' = 'json') {
    const endpoint = `/api/v1/logs/export/${sessionId}?format=${format}`;

    if (format === 'zip') {
      // Handle file download
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      return response.blob();
    } else {
      return this.request(endpoint);
    }
  }

  async getApplicationLogs(limit: number = 100, level?: string) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (level) params.append('level', level);

    return this.request(`/api/v1/logs/application?${params.toString()}`);
  }

  async getStartupLogs() {
    return this.request('/api/v1/logs/startup');
  }

  // Frontend error logging
  async logFrontendError(errorData: {
    error_id: string;
    timestamp: string;
    message: string;
    stack?: string;
    component_stack?: string;
    user_agent: string;
    url: string;
    context?: Record<string, any>;
  }) {
    return this.request('/api/v1/logs/frontend-error', {
      method: 'POST',
      body: JSON.stringify(errorData)
    });
  }

  // Events (Server-Sent Events)
  createEventStream(groupId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/api/v1/groups/${groupId}/events/`);
  }
}

export const apiService = new ApiService();