/**
 * API Services Barrel Export
 * Centralized exports for all API endpoints
 */

export * from './client';
export * from './agents';
export * from './groups';
export * from './logs';
export * from './mcp';
export * from './settings';
export * from './tools';

// Import individual API modules
import { httpClient } from './client';
import { agentsApi } from './agents';
import { groupsApi } from './groups';
import { logsApi } from './logs';
import { mcpApi } from './mcp';
import { settingsApi } from './settings';
import { toolsApi } from './tools';

// Create aggregate apiService for backward compatibility
export const apiService = {
  // HTTP Client methods
  ...httpClient,
  
  // Agents API
  getAvailableAgents: agentsApi.getAgents,
  getAgent: agentsApi.getAgent,
  createAgent: agentsApi.createAgent,
  updateAgent: agentsApi.updateAgent,
  deleteAgent: agentsApi.deleteAgent,
  validateAgent: agentsApi.validateAgent,
  
  // Groups API
  getGroups: groupsApi.getGroups,
  createGroup: groupsApi.createGroup,
  updateGroup: groupsApi.updateGroup,
  deleteGroup: groupsApi.deleteGroup,
  getGroupAgents: groupsApi.getGroupAgents,
  addAgentToGroup: groupsApi.addAgentToGroup,
  removeAgentFromGroup: groupsApi.removeAgentFromGroup,
  sendMessage: groupsApi.sendMessage,
  getGroupDocuments: groupsApi.getGroupDocuments,
  uploadDocument: groupsApi.uploadDocument,
  
  // Logs API
  getLogSessions: logsApi.getLogSessions,
  getSessionLogs: logsApi.getSessionLogs,
  getSessionSummary: logsApi.getSessionSummary,
  logFrontendError: logsApi.logFrontendError,
  getStartupLogs: logsApi.getStartupLogs,
  
  // MCP API
  getMcpServers: mcpApi.getMcpServers,
  getMcpServer: mcpApi.getMcpServer,
  createMcpServer: mcpApi.createMcpServer,
  updateMcpServer: mcpApi.updateMcpServer,
  deleteMcpServer: mcpApi.deleteMcpServer,
  validateMcpServer: mcpApi.validateMcpServer,
  getMcpTemplates: mcpApi.getMcpTemplates,
  
  // Settings API
  getSettings: settingsApi.getSettings,
  updateSettings: settingsApi.updateSettings,
  getSystemInfo: settingsApi.getSystemInfo,
  getConfigStatus: settingsApi.getConfigStatus,
  
  // Tools API
  getTools: toolsApi.getTools,
  getTool: toolsApi.getTool,
  createTool: toolsApi.createTool,
  updateTool: toolsApi.updateTool,
  deleteTool: toolsApi.deleteTool,
  validateTool: toolsApi.validateTool,
  getToolTemplates: toolsApi.getToolTemplates,
};
