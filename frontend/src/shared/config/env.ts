/**
 * Environment Configuration
 * Type-safe environment variables with validation
 */

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