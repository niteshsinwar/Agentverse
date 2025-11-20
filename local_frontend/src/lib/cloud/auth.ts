/**
 * Cloud Authentication Service
 *
 * Manages JWT tokens and authentication with cloud backend.
 */

import { cloudConfig, CLOUD_ENDPOINTS } from './config';

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  tenant_id: string;
  email: string;
  password: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  tenant_id?: string;
  tenant_name?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
  tenant_id: string;
  user_role: string;
}

class CloudAuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    // Load tokens from localStorage on initialization
    this.loadTokens();
  }

  /**
   * Login with tenant_id, email and password
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const config = cloudConfig();
    const url = `${config.baseUrl}${CLOUD_ENDPOINTS.auth.login}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Login failed' }));
      throw new Error(error.error || error.detail || 'Login failed');
    }

    const loginResponse: LoginResponse = await response.json();

    // Store tokens
    this.accessToken = loginResponse.access_token;
    this.refreshToken = loginResponse.refresh_token;
    localStorage.setItem('cloud_access_token', loginResponse.access_token);
    localStorage.setItem('cloud_refresh_token', loginResponse.refresh_token);

    return loginResponse;
  }

  /**
   * Logout and clear tokens
   */
  async logout(): Promise<void> {
    const config = cloudConfig();
    const url = `${config.baseUrl}${CLOUD_ENDPOINTS.auth.logout}`;

    try {
      await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    }

    this.clearTokens();
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const config = cloudConfig();
    const url = `${config.baseUrl}${CLOUD_ENDPOINTS.auth.refresh}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Token refresh failed');
    }

    const { access_token, refresh_token } = await response.json();
    this.accessToken = access_token;
    this.refreshToken = refresh_token;
    localStorage.setItem('cloud_access_token', access_token);
    localStorage.setItem('cloud_refresh_token', refresh_token);

    return access_token;
  }

  /**
   * Get current user profile
   */
  async me(): Promise<UserProfile> {
    const config = cloudConfig();
    const url = `${config.baseUrl}${CLOUD_ENDPOINTS.auth.me}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user profile');
    }

    return response.json();
  }

  /**
   * Store tokens in memory and localStorage
   */
  private setTokens(tokens: AuthTokens): void {
    this.accessToken = tokens.access;
    this.refreshToken = tokens.refresh;

    localStorage.setItem('cloud_access_token', tokens.access);
    localStorage.setItem('cloud_refresh_token', tokens.refresh);
  }

  /**
   * Load tokens from localStorage
   */
  private loadTokens(): void {
    this.accessToken = localStorage.getItem('cloud_access_token');
    this.refreshToken = localStorage.getItem('cloud_refresh_token');
  }

  /**
   * Clear tokens from memory and localStorage
   */
  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;

    localStorage.removeItem('cloud_access_token');
    localStorage.removeItem('cloud_refresh_token');
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }
}

// Singleton instance
export const cloudAuth = new CloudAuthService();
