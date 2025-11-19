/**
 * Cloud HTTP Client
 *
 * Handles HTTP requests to cloud backend with JWT authentication.
 */

import { cloudConfig } from './config';
import { cloudAuth } from './auth';

export interface RequestOptions extends RequestInit {
  timeout?: number;
  skipAuth?: boolean;
}

class CloudHttpClient {
  /**
   * Make HTTP request with automatic token refresh
   */
  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const config = cloudConfig();
    const url = `${config.baseUrl}${endpoint}`;
    const { timeout = 30000, skipAuth = false, ...fetchOptions } = options;

    // Prepare headers
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    };

    // Add authorization header
    if (!skipAuth) {
      const token = cloudAuth.getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle 401 Unauthorized (token expired)
      if (response.status === 401 && !skipAuth) {
        try {
          // Try to refresh token
          await cloudAuth.refreshAccessToken();

          // Retry request with new token
          const newToken = cloudAuth.getAccessToken();
          if (newToken) {
            headers['Authorization'] = `Bearer ${newToken}`;

            const retryResponse = await fetch(url, {
              ...fetchOptions,
              headers,
            });

            if (!retryResponse.ok) {
              throw new Error(`Request failed: ${retryResponse.statusText}`);
            }

            return retryResponse.json();
          }
        } catch (refreshError) {
          // Refresh failed, logout user
          cloudAuth.logout();
          throw new Error('Session expired. Please login again.');
        }
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || `Request failed: ${response.statusText}`);
      }

      // Handle empty response (204 No Content, etc.)
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return null as T;
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * Upload file with FormData
   */
  async upload<T>(
    endpoint: string,
    formData: FormData,
    options?: Omit<RequestOptions, 'body'>
  ): Promise<T> {
    const config = cloudConfig();
    const url = `${config.baseUrl}${endpoint}`;
    const token = cloudAuth.getAccessToken();

    const headers: HeadersInit = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }
}

// Singleton instance
export const cloudHttpClient = new CloudHttpClient();
