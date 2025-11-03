/**
 * Unified Configuration
 * Environment variables, constants, and application configuration
 * Date: October 11, 2025
 */

import type { Theme } from './types';

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
  THEMES: [
    'system',
    'auto',
    'light',
    'dark',
    'titan',
    'sentinel',
    'carbon',
    'arctic',
    'quantum',
    'sci-fi-indigo',
    'carpet-orange',
    'royal-dark-green',
    'bloody-reddish',
    'party-yellow',
  ] as const,
} as const;

export interface ThemeCatalogEntry {
  id: Theme;
  label: string;
  description: string;
  scheme: 'light' | 'dark' | 'adaptive';
  previewGradient: string;
  previewColors: [string, string, string];
  accent: string;
  shortLabel: string;
  badge?: {
    text: string;
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  };
}

export const THEME_CATALOG: ThemeCatalogEntry[] = [
  {
    id: 'system',
    label: 'Match System',
    description: 'Aligns instantly with your operating system preference.',
    scheme: 'adaptive',
    previewGradient: 'linear-gradient(135deg, #e2e8f0 0%, #cbd5f5 35%, #1d4ed8 70%, #0f172a 100%)',
    previewColors: ['#94a3b8', '#1d4ed8', '#0f172a'],
    accent: '#1d4ed8',
    shortLabel: 'OS',
    badge: { text: 'Adaptive', variant: 'info' },
  },
  {
    id: 'auto',
    label: 'Auto (Circadian)',
    description: 'Transitions between light and dark to mirror your day.',
    scheme: 'adaptive',
    previewGradient: 'linear-gradient(135deg, #f8fafc 0%, #93c5fd 40%, #3b82f6 70%, #1e3a8a 100%)',
    previewColors: ['#f8fafc', '#3b82f6', '#111827'],
    accent: '#2563eb',
    shortLabel: 'AU',
    badge: { text: 'Dynamic', variant: 'secondary' },
  },
  {
    id: 'light',
    label: 'Light Classic',
    description: 'Crisp whites and soft neutrals for ultimate clarity.',
    scheme: 'light',
    previewGradient: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%)',
    previewColors: ['#f8fafc', '#e2e8f0', '#cbd5f5'],
    accent: '#0f172a',
    shortLabel: 'L',
    badge: { text: 'Classic', variant: 'secondary' },
  },
  {
    id: 'dark',
    label: 'Dark Classic',
    description: 'Midnight blues with elevated contrast for focus.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #0f172a 0%, #111827 60%, #1f2937 100%)',
    previewColors: ['#111827', '#1e293b', '#0f172a'],
    accent: '#1e293b',
    shortLabel: 'D',
    badge: { text: 'Classic', variant: 'secondary' },
  },
  {
    id: 'titan',
    label: 'Titan Core',
    description: 'Flagship cobalt blues with luminous highlights.',
    scheme: 'light',
    previewGradient: 'linear-gradient(135deg, #0f172a 0%, #1d4ed8 45%, #0ea5e9 85%, #0f172a 100%)',
    previewColors: ['#1d4ed8', '#0ea5e9', '#0891b2'],
    accent: '#1d4ed8',
    shortLabel: 'T',
    badge: { text: 'Flagship', variant: 'primary' },
  },
  {
    id: 'sentinel',
    label: 'Sentinel Midnight',
    description: 'Stealth blues engineered for command centers.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(140deg, #0b1220 0%, #1e3a8a 45%, #2563eb 80%, #38bdf8 100%)',
    previewColors: ['#1e3a8a', '#2563eb', '#38bdf8'],
    accent: '#2563eb',
    shortLabel: 'S',
    badge: { text: 'Night Ops', variant: 'info' },
  },
  {
    id: 'carbon',
    label: 'Carbon Neon',
    description: 'Graphite depths with electric cyan accents.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #020617 0%, #0b1120 35%, #0ea5e9 85%, #22d3ee 100%)',
    previewColors: ['#0ea5e9', '#22d3ee', '#38bdf8'],
    accent: '#0ea5e9',
    shortLabel: 'C',
    badge: { text: 'Neon Grid', variant: 'success' },
  },
  {
    id: 'arctic',
    label: 'Arctic Aurora',
    description: 'Glacial cyan gradients with polar serenity.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #0b1220 0%, #0f172a 35%, #38bdf8 80%, #22d3ee 100%)',
    previewColors: ['#38bdf8', '#22d3ee', '#94a3b8'],
    accent: '#22d3ee',
    shortLabel: 'AR',
    badge: { text: 'Polar', variant: 'info' },
  },
  {
    id: 'quantum',
    label: 'Quantum Flux',
    description: 'Neo-futuristic gradients for experimentation.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #030712 0%, #1e293b 40%, #0284c7 80%, #38bdf8 100%)',
    previewColors: ['#0284c7', '#38bdf8', '#22d3ee'],
    accent: '#0284c7',
    shortLabel: 'Q',
    badge: { text: 'Lab', variant: 'warning' },
  },
  {
    id: 'sci-fi-indigo',
    label: 'Sci-Fi Indigo',
    description: 'Galactic indigos with phosphor glows for control rooms.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #070b1a 0%, #111c44 45%, #3b5bcc 80%, #7dd3fc 100%)',
    previewColors: ['#111c44', '#3b5bcc', '#7dd3fc'],
    accent: '#3b5bcc',
    shortLabel: 'SI',
    badge: { text: 'Galaxy', variant: 'info' },
  },
  {
    id: 'carpet-orange',
    label: 'Carpet Orange',
    description: 'Warm sunset ambers with grounded sandstone bases.',
    scheme: 'light',
    previewGradient: 'linear-gradient(135deg, #fdf6ec 0%, #f59e0b 45%, #f97316 80%, #b45309 100%)',
    previewColors: ['#f59e0b', '#f97316', '#b45309'],
    accent: '#f97316',
    shortLabel: 'CO',
    badge: { text: 'Sunset', variant: 'warning' },
  },
  {
    id: 'royal-dark-green',
    label: 'Royal Dark Green',
    description: 'Emerald courts with aurora highlights for executive ops.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #03110c 0%, #064e3b 45%, #10b981 80%, #6ee7b7 100%)',
    previewColors: ['#064e3b', '#10b981', '#6ee7b7'],
    accent: '#10b981',
    shortLabel: 'RD',
    badge: { text: 'Sovereign', variant: 'success' },
  },
  {
    id: 'bloody-reddish',
    label: 'Crimson Reactor',
    description: 'Tactical crimsons with reactor-core magentas.',
    scheme: 'dark',
    previewGradient: 'linear-gradient(135deg, #140308 0%, #7f1d1d 40%, #dc2626 80%, #f87171 100%)',
    previewColors: ['#7f1d1d', '#dc2626', '#f87171'],
    accent: '#dc2626',
    shortLabel: 'CR',
    badge: { text: 'Command', variant: 'error' },
  },
  {
    id: 'party-yellow',
    label: 'Party Yellow',
    description: 'Festive golds with confetti pops for celebratory ops.',
    scheme: 'light',
    previewGradient: 'linear-gradient(135deg, #fffbe6 0%, #facc15 40%, #f59e0b 75%, #fef08a 100%)',
    previewColors: ['#facc15', '#f59e0b', '#fef08a'],
    accent: '#facc15',
    shortLabel: 'PY',
    badge: { text: 'Festival', variant: 'warning' },
  },
];

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
