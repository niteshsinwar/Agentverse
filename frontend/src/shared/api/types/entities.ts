/**
 * API Entity Types
 * TypeScript interfaces matching the backend data models
 */

import type { ID, Timestamp, ISODateString } from '../../types/common';

// Base entity interface
export interface BaseEntity {
  created_at: Timestamp;
  updated_at: Timestamp;
}

// Group entity
export interface Group extends BaseEntity {
  id: ID;
  name: string;
}

export interface CreateGroupRequest {
  name: string;
}

export interface UpdateGroupRequest {
  name?: string;
}

// Agent entity
export interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
  llm?: {
    provider: string;
    model: string;
  };
}

export interface CreateAgentRequest {
  name: string;
  description: string;
  emoji?: string;
  agent_folder?: string;
  tools_code?: string;
  selected_tools?: string[];
  mcp_config?: Record<string, any>;
  selected_mcps?: string[];
  llm_config?: {
    provider: string;
    model: string;
    api_key?: string;
    base_url?: string;
    temperature?: number;
    max_tokens?: number;
  };
}

export interface UpdateAgentRequest extends Partial<CreateAgentRequest> {
  key?: string;
}

export interface ValidateAgentRequest extends CreateAgentRequest {}

// Message entity
export interface Message extends BaseEntity {
  id: number;
  group_id: ID;
  sender: string;
  role: 'user' | 'agent' | 'system' | 'tool_call' | 'tool_result' | 'mcp_call' | 'error';
  content: string;
  metadata?: Record<string, any>;
}

export interface SendMessageRequest {
  agent_id: string;
  message: string;
}

// Document entity
export interface Document extends BaseEntity {
  document_id: ID;
  filename: string;
  size: number;
  target_agent: string;
  sender: string;
  size_str: string;
  date_str: string;
  file_extension: string;
  content_summary?: string;
}

export interface UploadDocumentRequest {
  file: File;
  agent_id: string;
  message?: string;
}

// Tool entity
export interface Tool {
  id: string;
  name: string;
  description: string;
  code: string;
  functions: string[];
  enabled: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface CreateToolRequest {
  name: string;
  description: string;
  code: string;
  functions?: string[];
  enabled?: boolean;
}

export interface UpdateToolRequest extends Partial<CreateToolRequest> {}

export interface ValidateToolRequest {
  code: string;
  function_names?: string[];
}

// MCP Server entity
export interface McpServer {
  id: string;
  name: string;
  type: 'stdio' | 'sse' | 'websocket';
  config: Record<string, any>;
  enabled: boolean;
  tools?: string[];
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface CreateMcpServerRequest {
  name: string;
  type: 'stdio' | 'sse' | 'websocket';
  config: Record<string, any>;
  enabled?: boolean;
}

export interface UpdateMcpServerRequest extends Partial<CreateMcpServerRequest> {}

export interface ValidateMcpRequest {
  name: string;
  config: Record<string, any>;
  timeout?: number;
}

// Settings entity (matches backend flat structure)
export interface Settings {
  app_name?: string;
  version?: string;
  environment?: 'development' | 'staging' | 'production' | 'testing';
  debug?: boolean;
  host?: string;
  port?: number;
  allowed_origins?: string[];
  openai_api_key?: string;
  anthropic_api_key?: string;
  gemini_api_key?: string;
  github_token?: string;
  database_url?: string;
  max_upload_size_mb?: number;
  supported_file_formats?: string[];
  max_agent_iterations?: number;
  default_temperature?: number;
  default_max_tokens?: number;
  llm_provider?: string;
  llm_model?: string;
  llm_temperature?: number;
  llm_max_tokens?: number;
  llm_fallback_provider?: string;
  secret_key?: string;
  session_timeout_hours?: number;
  log_level?: string;
  enable_file_logging?: boolean;
  log_file_max_size_mb?: number;
  [key: string]: any; // Allow any additional settings
}

export interface UpdateSettingsRequest {
  settings: Settings;
}

// System Info
export interface SystemModule {
  name: string;
  version: string;
  status: 'available' | 'unavailable' | 'error';
  description?: string;
  dependencies?: string[];
}

export interface SystemInfo {
  modules: SystemModule[];
  python_version: string;
  platform: string;
  installed_packages: Record<string, string>;
}

// Configuration Status
export interface ConfigStatus {
  agents: {
    count: number;
    valid: number;
    invalid: number;
  };
  tools: {
    count: number;
    enabled: number;
    disabled: number;
  };
  mcp_servers: {
    count: number;
    connected: number;
    disconnected: number;
  };
  settings: {
    configured: boolean;
    valid: boolean;
  };
}

// Templates
export interface ToolTemplate {
  id: string;
  name: string;
  description: string;
  code: string;
  functions: string[];
  category: string;
}

export interface McpTemplate {
  id: string;
  name: string;
  description: string;
  type: 'stdio' | 'sse' | 'websocket';
  config_schema: Record<string, any>;
  example_config: Record<string, any>;
  category: string;
}