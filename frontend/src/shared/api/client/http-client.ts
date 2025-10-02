/**
 * HTTP Client
 * Centralized HTTP client with interceptors, error handling, and logging
 */

import { env, isDevelopment } from '../../config/env';
import { ERROR_MESSAGES } from '../../constants/app';
// import { API_ENDPOINTS } from '../../constants/app';
// import type { ApiResponse } from '../../types/common';

export interface RequestConfig extends RequestInit {
  timeout?: number;
  retry?: {
    attempts: number;
    delay: number;
  };
}

export interface LogEntry {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  context?: Record<string, any>;
}

class HttpClient {
  private baseURL: string;
  private logs: LogEntry[] = [];
  private readonly maxLogs = 1000;
  private abortControllers = new Map<string, AbortController>();

  constructor() {
    this.baseURL = env.API_BASE_URL;
  }

  // Logging methods
  private log(level: LogEntry['level'], message: string, context?: Record<string, any>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
    };

    this.logs.unshift(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    if (isDevelopment) {
      const logMethod = level.toLowerCase() as 'debug' | 'info' | 'warn' | 'error';
      console[logMethod](`[API] ${message}`, context || '');
    }
  }

  // Request timeout helper
  private createTimeoutSignal(timeout: number, requestId: string): AbortSignal {
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);

    const timeoutId = setTimeout(() => {
      controller.abort();
      this.abortControllers.delete(requestId);
    }, timeout);

    // Clean up timeout if request completes normally
    const originalSignal = controller.signal;
    const cleanup = () => {
      clearTimeout(timeoutId);
      this.abortControllers.delete(requestId);
    };

    originalSignal.addEventListener('abort', cleanup, { once: true });
    return originalSignal;
  }

  // Retry logic
  private async withRetry<T>(
    operation: () => Promise<T>,
    retryConfig?: { attempts: number; delay: number }
  ): Promise<T> {
    const { attempts = 1, delay = 1000 } = retryConfig || {};

    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        if (attempt === attempts) {
          throw error;
        }

        // Don't retry on client errors (4xx)
        if (error instanceof Error && 'status' in error) {
          const status = (error as any).status;
          if (status >= 400 && status < 500) {
            throw error;
          }
        }

        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }

    throw new Error('Retry attempts exhausted');
  }

  // Core request method
  private async request<T = any>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<T> {
    const {
      timeout = env.API_TIMEOUT,
      retry,
      ...requestInit
    } = config;

    const url = `${this.baseURL}${endpoint}`;
    const method = requestInit.method || 'GET';
    const requestId = `${method}_${endpoint}_${Date.now()}`;
    const startTime = Date.now();

    this.log('DEBUG', `${method} ${endpoint}`, {
      url,
      headers: requestInit.headers,
      bodySize: requestInit.body ? new Blob([requestInit.body as string]).size : 0,
      requestId,
    });

    const operation = async () => {
      const signal = this.createTimeoutSignal(timeout, requestId);

      try {
        const response = await fetch(url, {
          signal,
          headers: {
            'Content-Type': 'application/json',
            ...requestInit.headers,
          },
          ...requestInit,
        });

        const duration = Date.now() - startTime;

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          const error = new Error(`API request failed: ${response.statusText}`) as any;

          error.status = response.status;
          error.statusText = response.statusText;
          error.data = errorData;

          this.log('ERROR', `API Error: ${method} ${endpoint}`, {
            status: response.status,
            statusText: response.statusText,
            duration,
            errorData,
            endpoint,
            method,
            requestId,
          });

          // Attach validation errors if present
          if (errorData?.detail?.validation_errors) {
            error.validation_errors = errorData.detail.validation_errors;
          } else if (errorData?.detail && typeof errorData.detail === 'object') {
            error.validation_errors = errorData.detail;
          }

          throw error;
        }

        // Log successful requests
        this.log('INFO', `${method} ${endpoint} - ${response.status}`, {
          status: response.status,
          duration,
          endpoint,
          method,
          requestId,
        });

        // Performance warning for slow requests
        if (duration > 2000) {
          this.log('WARN', `Slow API request: ${method} ${endpoint}`, {
            duration,
            threshold: 2000,
            endpoint,
            method,
            requestId,
          });
        }

        const data = await response.json();
        return data;
      } catch (error) {
        const duration = Date.now() - startTime;

        if (error instanceof Error && error.name === 'AbortError') {
          this.log('WARN', `Request timeout: ${method} ${endpoint}`, {
            duration,
            timeout,
            endpoint,
            method,
            requestId,
          });
          throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
        }

        this.log('ERROR', `Request failed: ${method} ${endpoint}`, {
          error: error instanceof Error ? error.message : String(error),
          duration,
          endpoint,
          method,
          requestId,
          type: 'network_error',
        });

        throw error;
      } finally {
        this.abortControllers.delete(requestId);
      }
    };

    if (retry) {
      return this.withRetry(operation, retry);
    }

    return operation();
  }

  // HTTP methods
  async get<T = any>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  async post<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T = any>(endpoint: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  // File upload
  async upload<T = any>(
    endpoint: string,
    formData: FormData,
    config?: Omit<RequestConfig, 'body'> & {
      onProgress?: (progress: number) => void;
    }
  ): Promise<T> {
    const { onProgress } = config || {};
    const url = `${this.baseURL}${endpoint}`;

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });
      }

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            resolve(xhr.responseText as any);
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', url);
      xhr.send(formData);
    });
  }

  // Utility methods
  getLogs(level?: LogEntry['level']): LogEntry[] {
    if (level) {
      return this.logs.filter(log => log.level === level);
    }
    return [...this.logs];
  }

  clearLogs(): void {
    this.logs = [];
  }

  cancelRequest(requestId: string): void {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
    }
  }

  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }
}

// Create singleton instance
export const httpClient = new HttpClient();