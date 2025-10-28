/**
 * Unified Configuration
 * Environment variables, constants, and application configuration
 * Date: October 11, 2025
 */

// ============================================================================
// ENVIRONMENT CONFIGURATION
// ============================================================================

interface EnvConfig {
  API_BASE_URL: string;
  APP_VERSION: string;
  ENVIRONMENT: 'development' | 'staging' | 'production';
  LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error';
  ENABLE_MOCK_API: boolean;
  SSE_RECONNECT_INTERVAL: number;
  API_TIMEOUT: number;
}

const validateEnv = (): EnvConfig => {
  const config: EnvConfig = {
    API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
    ENVIRONMENT: (import.meta.env.VITE_ENVIRONMENT as EnvConfig['ENVIRONMENT']) || 'development',
    LOG_LEVEL: (import.meta.env.VITE_LOG_LEVEL as EnvConfig['LOG_LEVEL']) || 'info',
    ENABLE_MOCK_API: import.meta.env.VITE_ENABLE_MOCK_API === 'true',
    SSE_RECONNECT_INTERVAL: parseInt(import.meta.env.VITE_SSE_RECONNECT_INTERVAL || '5000'),
    API_TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  };

  // Validate required fields
  if (!config.API_BASE_URL) {
    throw new Error('VITE_API_BASE_URL is required');
  }

  // Validate environment
  if (!['development', 'staging', 'production'].includes(config.ENVIRONMENT)) {
    throw new Error('VITE_ENVIRONMENT must be development, staging, or production');
  }

  return config;
};

export const env = validateEnv();

export const isDevelopment = env.ENVIRONMENT === 'development';
export const isProduction = env.ENVIRONMENT === 'production';
export const isStaging = env.ENVIRONMENT === 'staging';

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API_ENDPOINTS = {
  GROUPS: '/api/v1/groups',
  AGENTS: '/api/v1/agents',
  MESSAGES: '/api/v1/groups',
  DOCUMENTS: '/api/v1/groups',
  CONFIG: '/api/v1/config',
  LOGS: '/api/v1/logs',
  ANALYTICS: '/api/v1/analytics',
} as const;

// ============================================================================
// UI CONSTANTS
// ============================================================================

export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 280,
  HEADER_HEIGHT: 64,
  TOAST_DURATION: 4000,
  ANIMATION_DURATION: 300,
  DEBOUNCE_DELAY: 300,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  PAGINATION_SIZE: 20,
} as const;

// ============================================================================
// THEME CONSTANTS
// ============================================================================

export const THEME_CONSTANTS = {
  STORAGE_KEY: 'agentverse-theme',
  DEFAULT_THEME: 'system' as const,
  THEMES: ['light', 'dark', 'system'] as const,
} as const;

// ============================================================================
// AGENT CONSTANTS
// ============================================================================

export const AGENT_CONSTANTS = {
  MAX_NAME_LENGTH: 50,
  MAX_DESCRIPTION_LENGTH: 200,
  DEFAULT_EMOJI: '🤖',
  SUPPORTED_LLM_PROVIDERS: ['openai', 'anthropic', 'ollama'] as const,
} as const;

// ============================================================================
// MESSAGE CONSTANTS
// ============================================================================

export const MESSAGE_CONSTANTS = {
  MAX_LENGTH: 8000,
  TYPING_INDICATOR_TIMEOUT: 3000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// ============================================================================
// FILE UPLOAD CONSTANTS
// ============================================================================

export const DEFAULT_SUPPORTED_FILE_FORMATS = Object.freeze([
  'txt', 'csv', 'json', 'pdf', 'docx', 'pptx', 'xlsx', 'xls', 'md', 'png',
  'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'rtf', 'odt', 'xml', 'html',
  'htm', 'py', 'js', 'ts', 'ods'
]);

export const FILE_CONSTANTS = {
  SUPPORTED_TYPES: [
    'text/plain',
    'text/markdown',
    'application/pdf',
    'application/json',
    'text/csv',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ] as const,
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  CHUNK_SIZE: 1024 * 1024, // 1MB chunks
} as const;

// ============================================================================
// VALIDATION CONSTANTS
// ============================================================================

export const VALIDATION_CONSTANTS = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_INPUT_LENGTH: 1000,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL_REGEX: /^https?:\/\/.+/,
  SLUG_REGEX: /^[a-z0-9-]+$/,
} as const;

// ============================================================================
// ERROR MESSAGES
// ============================================================================

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your internet connection.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
  FILE_TOO_LARGE: 'File size exceeds the maximum limit.',
  UNSUPPORTED_FILE_TYPE: 'File type is not supported.',
} as const;

// ============================================================================
// SUCCESS MESSAGES
// ============================================================================

export const SUCCESS_MESSAGES = {
  SAVE_SUCCESS: 'Changes saved successfully.',
  CREATE_SUCCESS: 'Created successfully.',
  UPDATE_SUCCESS: 'Updated successfully.',
  DELETE_SUCCESS: 'Deleted successfully.',
  UPLOAD_SUCCESS: 'File uploaded successfully.',
  COPY_SUCCESS: 'Copied to clipboard.',
} as const;

// ============================================================================
// STORAGE KEYS
// ============================================================================

export const STORAGE_KEYS = {
  THEME: 'agentverse-theme',
  SIDEBAR_STATE: 'agentverse-sidebar',
  USER_PREFERENCES: 'agentverse-preferences',
  SESSION_DATA: 'agentverse-session',
  RECENT_GROUPS: 'agentverse-recent-groups',
  DRAFT_MESSAGES: 'agentverse-drafts',
} as const;

// ============================================================================
// STATUS TYPES
// ============================================================================

export const STATUS_TYPES = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
} as const;

// ============================================================================
// LOG LEVELS
// ============================================================================

export const LOG_LEVELS = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
} as const;

// ============================================================================
// COMBINED CONFIG EXPORT
// ============================================================================

export const config = {
  env,
  isDevelopment,
  isProduction,
  isStaging,
  api: API_ENDPOINTS,
  ui: UI_CONSTANTS,
  theme: THEME_CONSTANTS,
  agent: AGENT_CONSTANTS,
  message: MESSAGE_CONSTANTS,
  file: FILE_CONSTANTS,
  validation: VALIDATION_CONSTANTS,
  errors: ERROR_MESSAGES,
  success: SUCCESS_MESSAGES,
  storage: STORAGE_KEYS,
  status: STATUS_TYPES,
  log: LOG_LEVELS,
} as const;

export default config;
