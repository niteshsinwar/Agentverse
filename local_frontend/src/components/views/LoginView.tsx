/**
 * LoginView - Cloud authentication component
 *
 * Handles user login via cloud backend and initializes local cache.
 */

import React, { useState } from 'react';
import './LoginView.css';

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
  tenant_id: string;
  user_role: string;
}

interface LoginViewProps {
  onLoginSuccess: () => void;
}

const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Call local backend cloud proxy
      const response = await fetch('http://localhost:8000/api/v1/cloud/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();

      // Store authentication data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      localStorage.setItem('tenant_id', data.tenant_id);
      localStorage.setItem('user_role', data.user_role);

      console.log('✅ Login successful:', {
        user: data.user.email,
        role: data.user_role,
        tenant: data.tenant_id,
      });

      // Check cache status
      try {
        const cacheResponse = await fetch('http://localhost:8000/api/v1/cloud/cache/status');
        const cacheStatus = await cacheResponse.json();
        console.log('📊 Cache status:', cacheStatus);
      } catch (cacheError) {
        console.warn('⚠️ Could not fetch cache status:', cacheError);
      }

      // Call success callback
      onLoginSuccess();
    } catch (err) {
      console.error('❌ Login error:', err);
      setError(err instanceof Error ? err.message : 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>🤖 AgentVerse</h1>
          <p>Sign in to your account</p>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="admin@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading || !email || !password}
          >
            {loading ? (
              <>
                <span className="spinner">⏳</span>
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="login-footer">
          <p className="demo-credentials">
            <strong>Demo credentials:</strong><br />
            Email: admin@example.com<br />
            Password: password123
          </p>
          <p className="version-info">
            AgentVerse v1.0.0 | Cloud-enabled
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginView;
