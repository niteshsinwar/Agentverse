/**
 * Authentication Utilities
 *
 * Handles JWT token management and authentication state.
 */

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  tenantId: string | null;
  userRole: string | null;
}

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

/**
 * Get access token
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Get refresh token
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem('refresh_token');
};

/**
 * Get current user
 */
export const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Get tenant ID
 */
export const getTenantId = (): string | null => {
  return localStorage.getItem('tenant_id');
};

/**
 * Get user role
 */
export const getUserRole = (): string | null => {
  return localStorage.getItem('user_role');
};

/**
 * Get authentication state
 */
export const getAuthState = (): AuthState => {
  return {
    isAuthenticated: isAuthenticated(),
    user: getCurrentUser(),
    tenantId: getTenantId(),
    userRole: getUserRole(),
  };
};

/**
 * Check if user is admin
 */
export const isAdmin = (): boolean => {
  const role = getUserRole();
  return role === 'admin';
};

/**
 * Logout user
 */
export const logout = async (): Promise<void> => {
  const refreshToken = getRefreshToken();

  // Call logout endpoint
  if (refreshToken) {
    try {
      await fetch('http://localhost:8000/api/v1/cloud/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  // Clear local storage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('tenant_id');
  localStorage.removeItem('user_role');
};

/**
 * Refresh access token
 */
export const refreshAccessToken = async (): Promise<boolean> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch('http://localhost:8000/api/v1/cloud/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) return false;

    const data = await response.json();

    // Update tokens
    localStorage.setItem('access_token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }

    return true;
  } catch (error) {
    console.error('Token refresh error:', error);
    return false;
  }
};

/**
 * Make authenticated API request
 */
export const authenticatedFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAccessToken();

  const headers = {
    ...options.headers,
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If 401, try to refresh token and retry
  if (response.status === 401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry request with new token
      const newToken = getAccessToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        return fetch(url, { ...options, headers });
      }
    }

    // Refresh failed, logout
    await logout();
    window.location.href = '/login';
  }

  return response;
};
