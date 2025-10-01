/**
 * API Layer Index
 * Centralized exports for the API layer
 */

// HTTP Client
export { httpClient } from './client/http-client';
export type { RequestConfig, LogEntry } from './client/http-client';

// API Endpoints
export { groupsApi } from './endpoints/groups.api';
export { agentsApi } from './endpoints/agents.api';
export { toolsApi } from './endpoints/tools.api';
export { mcpApi } from './endpoints/mcp.api';
export { settingsApi } from './endpoints/settings.api';
export { logsApi } from './endpoints/logs.api';

// API Types
export type * from './types/entities';
export type * from './types/logs';

// Legacy API Service for backward compatibility during migration
import { httpClient } from './client/http-client';
import { groupsApi } from './endpoints/groups.api';
import { agentsApi } from './endpoints/agents.api';
import { toolsApi } from './endpoints/tools.api';
import { mcpApi } from './endpoints/mcp.api';
import { settingsApi } from './endpoints/settings.api';
import { logsApi } from './endpoints/logs.api';

/**
 * Legacy API Service
 * Provides backward compatibility with the existing apiService
 * TODO: Remove this after all components are migrated to use the new API structure
 */
export const apiService = {
  // HTTP client methods
  getLogs: httpClient.getLogs.bind(httpClient),
  clearLogs: httpClient.clearLogs.bind(httpClient),

  // Groups
  getGroups: groupsApi.getGroups,
  createGroup: groupsApi.createGroup,
  deleteGroup: groupsApi.deleteGroup,
  getGroupAgents: groupsApi.getGroupAgents,
  addAgentToGroup: groupsApi.addAgentToGroup,
  removeAgentFromGroup: groupsApi.removeAgentFromGroup,
  getGroupMessages: groupsApi.getGroupMessages,
  sendMessage: groupsApi.sendMessage,
  getGroupDocuments: groupsApi.getGroupDocuments,
  uploadDocument: groupsApi.uploadDocument,
  createEventStream: groupsApi.createEventStream,

  // Agents
  getAvailableAgents: agentsApi.getAgents,
  createAgent: agentsApi.createAgent,
  validateAgent: agentsApi.validateAgent,
  updateAgent: agentsApi.updateAgent,
  deleteAgent: agentsApi.deleteAgent,
  validateAgentConfig: agentsApi.validateAgentConfig,
  validateAgentFolder: agentsApi.validateAgentFolder,

  // Tools
  getTools: toolsApi.getTools,
  addTool: toolsApi.createTool,
  updateTool: toolsApi.updateTool,
  deleteTool: toolsApi.deleteTool,
  validateToolConfig: toolsApi.validateTool,
  validateToolCode: toolsApi.validateToolCode,
  getToolTemplates: toolsApi.getToolTemplates,

  // MCP
  getMcpServers: mcpApi.getMcpServers,
  addMcpServer: mcpApi.createMcpServer,
  updateMcpServer: mcpApi.updateMcpServer,
  deleteMcpServer: mcpApi.deleteMcpServer,
  validateMcpConfig: mcpApi.validateMcpServer,
  validateMcpConnectivity: mcpApi.validateMcpConnectivity,
  getMcpTemplates: mcpApi.getMcpTemplates,

  // Settings
  getSettings: settingsApi.getSettings,
  updateSettings: settingsApi.updateSettings,
  resetSettings: settingsApi.resetSettings,
  validateSettings: settingsApi.validateSettings,
  getSystemInfo: settingsApi.getSystemInfo,
  getConfigStatus: settingsApi.getConfigStatus,
  createConfigBackup: settingsApi.createConfigBackup,

  // Logs
  getLogSessions: logsApi.getLogSessions,
  getSessionLogs: logsApi.getSessionLogs,
  getSessionSummary: logsApi.getSessionSummary,
  getSessionPerformance: logsApi.getSessionPerformance,
  deleteSessionLogs: logsApi.deleteSessionLogs,
  exportSessionLogs: logsApi.exportSessionLogs,
  getApplicationLogs: logsApi.getApplicationLogs,
  getStartupLogs: logsApi.getStartupLogs,
  logFrontendError: logsApi.logFrontendError,
};