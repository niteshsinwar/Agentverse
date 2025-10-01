/**
 * Application Constants
 * Centralized constants used throughout the application
 */

// API Configuration
export const API_ENDPOINTS = {
  GROUPS: '/api/v1/groups',
  AGENTS: '/api/v1/agents',
  MESSAGES: '/api/v1/groups',
  DOCUMENTS: '/api/v1/groups',
  CONFIG: '/api/v1/config',
  LOGS: '/api/v1/logs',
  ANALYTICS: '/api/v1/analytics',
} as const;

// UI Constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 280,
  HEADER_HEIGHT: 64,
  TOAST_DURATION: 4000,
  ANIMATION_DURATION: 300,
  DEBOUNCE_DELAY: 300,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  PAGINATION_SIZE: 20,
} as const;

// Theme Constants
export const THEME_CONSTANTS = {
  STORAGE_KEY: 'agentverse-theme',
  DEFAULT_THEME: 'system' as const,
  THEMES: ['light', 'dark', 'system'] as const,
} as const;

// Agent Constants
export const AGENT_CONSTANTS = {
  MAX_NAME_LENGTH: 50,
  MAX_DESCRIPTION_LENGTH: 200,
  DEFAULT_EMOJI: '🤖',
  SUPPORTED_LLM_PROVIDERS: ['openai', 'anthropic', 'ollama'] as const,
} as const;

// Message Constants
export const MESSAGE_CONSTANTS = {
  MAX_LENGTH: 8000,
  TYPING_INDICATOR_TIMEOUT: 3000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// File Upload Constants
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

// Validation Constants
export const VALIDATION_CONSTANTS = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_INPUT_LENGTH: 1000,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL_REGEX: /^https?:\/\/.+/,
  SLUG_REGEX: /^[a-z0-9-]+$/,
} as const;

// Error Messages
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

// Success Messages
export const SUCCESS_MESSAGES = {
  SAVE_SUCCESS: 'Changes saved successfully.',
  CREATE_SUCCESS: 'Created successfully.',
  UPDATE_SUCCESS: 'Updated successfully.',
  DELETE_SUCCESS: 'Deleted successfully.',
  UPLOAD_SUCCESS: 'File uploaded successfully.',
  COPY_SUCCESS: 'Copied to clipboard.',
} as const;

// Storage Keys
export const STORAGE_KEYS = {
  THEME: 'agentverse-theme',
  SIDEBAR_STATE: 'agentverse-sidebar',
  USER_PREFERENCES: 'agentverse-preferences',
  SESSION_DATA: 'agentverse-session',
  RECENT_GROUPS: 'agentverse-recent-groups',
  DRAFT_MESSAGES: 'agentverse-drafts',
} as const;

// Status Types
export const STATUS_TYPES = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
} as const;

// Log Levels
export const LOG_LEVELS = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
} as const;