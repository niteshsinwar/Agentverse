/**
 * Unified Type Definitions
 * All TypeScript interfaces and types for AgentVerse Frontend
 * Date: October 11, 2025
 */

// ============================================================================
// UTILITY TYPES
// ============================================================================

export type ID = string;
export type Timestamp = number;
export type ISODateString = string;

// ============================================================================
// DOMAIN ENTITIES (Core Business Objects)
// ============================================================================

export interface BaseEntity {
  created_at: Timestamp;
  updated_at: Timestamp;
}

export interface Group extends BaseEntity {
  id: ID;
  name: string;
}

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

export interface Message extends BaseEntity {
  id: number;
  group_id: ID;
  sender: string;
  role: 'user' | 'agent' | 'system' | 'tool_call' | 'tool_result' | 'mcp_call' | 'mcp_result' | 'error' | 'agent_thought';
  content: string;
  metadata?: Record<string, any>;
}

export interface Document extends BaseEntity {
  document_id: ID;
  filename: string;
  size: number;
  target_agent: string;
  sender: string;
  size_str: string;
  date_str: string;
  file_extension: string;
}

export interface Tool {
  id: ID;
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  parameters: Record<string, any>;
}

export interface McpServer {
  id: ID;
  name: string;
  description: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  enabled: boolean;
}

export interface Settings {
  [key: string]: any;
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

// Group API
export interface CreateGroupRequest {
  name: string;
}

export interface UpdateGroupRequest {
  name?: string;
}

// Agent API
export interface CreateAgentRequest {
  name: string;
  description: string;
  emoji: string;
  llm?: {
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

// Message API
export interface SendMessageRequest {
  agent_id: string;
  message: string;
}

// Document API
export interface UploadDocumentRequest {
  file: File;
  target_agent: string;
  sender: string;
  agent_id?: string;
  message?: string;
}

// Tool API
export interface CreateToolRequest {
  name: string;
  description: string;
  category: string;
  code: string;
  functions: string[];
}

export interface UpdateToolRequest extends Partial<CreateToolRequest> {}

export interface ValidateToolRequest {
  name: string;
  code: string;
  functions: string[];
}

// MCP API
export interface CreateMcpServerRequest {
  name: string;
  description: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

export interface UpdateMcpServerRequest extends Partial<CreateMcpServerRequest> {}

export interface ValidateMcpRequest {
  command: string;
  args: string[];
  env?: Record<string, string>;
}

// ============================================================================
// EVENT & MESSAGING TYPES
// ============================================================================

export interface EventMessage {
  type: string;
  data: Record<string, any>;
  timestamp: number;
}

export interface WebSocketMessage<T = any> {
  type: string;
  payload: T;
  timestamp: Timestamp;
  id?: ID;
}

export interface AppEvent<T = any> {
  type: string;
  payload: T;
  timestamp: Timestamp;
  source?: string;
}

// ============================================================================
// LOGGING & ANALYTICS TYPES
// ============================================================================

export interface LogEvent {
  id: string;
  session_id: string;
  timestamp: number;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  category: string;
  message: string;
  metadata?: Record<string, any>;
  agent_key?: string;
  user_id?: string;
  details?: any;
  event_type?: string;
  duration_ms?: number;
  error?: string;
  agent_id?: string;
}

export interface LogSession {
  session_id: string;
  created_at: number;
  last_activity: number;
  user_id?: string;
  group_id?: string;
  status: 'active' | 'archived';
}

export interface SessionSummary {
  session_id: string;
  message_count?: number;
  agent_count?: number;
  start_time: string | number;
  end_time: string | number;
  duration_seconds?: number;
  average_response_time?: number;
  total_events: number;
  error_count: number;
  agent_activity: Record<string, number>;
  event_counts: Record<string, number>;
  status: string;
}

export interface PerformanceMetrics {
  total_messages: number;
  average_response_time: number;
  success_rate: number;
  error_count: number;
  most_active_agent: string;
  peak_activity_time: string;
}

// Log Query Options
export interface LogQueryOptions {
  format?: 'json' | 'human';
  session_id?: string;
  level?: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  category?: string;
  event_type?: string;
  agent_id?: string;
  from_timestamp?: string;
  to_timestamp?: string;
  start_time?: number;
  end_time?: number;
  limit?: number;
  offset?: number;
}

// Frontend Error Log
export interface FrontendErrorLog {
  message: string;
  stack?: string;
  url: string;
  user_agent: string;
  timestamp: number;
  session_id?: string;
  user_id?: string;
  metadata?: Record<string, any>;
}

// Application Log
export interface ApplicationLog {
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical';
  message: string;
  category: string;
  metadata?: Record<string, any>;
  timestamp: number;
}

// Startup Log
export interface StartupLog {
  event: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Template Types
export interface ToolTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  code: string;
  parameters: Record<string, any>;
}

export interface McpTemplate {
  id: string;
  name: string;
  description: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
}

// Settings Types
export interface UpdateSettingsRequest {
  [key: string]: any;
}

export interface SystemInfo {
  version: string;
  platform: string;
  node_version: string;
  memory: {
    total: number;
    used: number;
    free: number;
  };
  cpu: {
    model: string;
    cores: number;
  };
}

export interface ConfigStatus {
  loaded: boolean;
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

// ============================================================================
// API UTILITY TYPES
// ============================================================================

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// ============================================================================
// STATE MANAGEMENT TYPES
// ============================================================================

export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
  lastUpdated?: Timestamp;
}

// ============================================================================
// FORM & VALIDATION TYPES
// ============================================================================

export interface FormFieldError {
  field: string;
  message: string;
  code?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: FormFieldError[];
}

export interface FileUpload {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  uploadedUrl?: string;
  id?: ID;
}

// ============================================================================
// UI & COMPONENT TYPES
// ============================================================================

export type Theme = 'light' | 'dark' | 'auto' | 'system';

export interface UserPreferences {
  theme: Theme;
  language: string;
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
  };
  sidebar: {
    expanded: boolean;
    width: number;
  };
  editor: {
    fontSize: number;
    lineHeight: number;
    tabSize: number;
  };
}

export interface SearchParams {
  query: string;
  filters?: Record<string, any>;
  sort?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Timestamp;
  stack?: string;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: string;
}

export interface TableColumn<T = any> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  render?: (value: any, row: T) => React.ReactNode;
}

export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  error?: string;
  onRowClick?: (row: T) => void;
  onSort?: (column: keyof T | string, order: 'asc' | 'desc') => void;
  pagination?: {
    page: number;
    limit: number;
    total: number;
    onPageChange: (page: number) => void;
  };
}

export interface AnimationConfig {
  duration: number;
  delay?: number;
  easing?: string;
}

export interface ContextValue<T> {
  state: T;
  setState: (state: T | ((prev: T) => T)) => void;
}

// ============================================================================
// AUTH & USER TYPES
// ============================================================================

export interface User {
  id: ID;
  name: string;
  email: string;
  accountType: 'individual' | 'enterprise';
  isAdmin: boolean;
  avatar?: string;
  preferences?: UserPreferences;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

// ============================================================================
// EXPORT ALL TYPES
// ============================================================================

export type {
  // Re-export all types for convenience
};
