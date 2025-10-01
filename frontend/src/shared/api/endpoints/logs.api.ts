/**
 * Logs API
 * API endpoints for logging and analytics
 */

import { httpClient } from '../client/http-client';
import type {
  LogSession,
  LogEvent,
  SessionSummary,
  PerformanceMetrics,
  LogQueryOptions,
  FrontendErrorLog,
  ApplicationLog,
  StartupLog,
} from '../types/logs';

export const logsApi = {
  // Log sessions
  async getLogSessions(): Promise<LogSession[]> {
    return httpClient.get<LogSession[]>('/api/v1/logs/sessions');
  },

  async getSessionLogs(
    sessionId: string,
    options: LogQueryOptions = {}
  ): Promise<LogEvent[]> {
    const params = new URLSearchParams();
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, String(value));
      }
    });

    const endpoint = `/api/v1/logs/sessions/${sessionId}`;
    const url = params.toString() ? `${endpoint}?${params.toString()}` : endpoint;
    return httpClient.get<LogEvent[]>(url);
  },

  async getSessionSummary(sessionId: string): Promise<SessionSummary> {
    return httpClient.get<SessionSummary>(`/api/v1/logs/sessions/${sessionId}/summary`);
  },

  async getSessionPerformance(sessionId: string): Promise<PerformanceMetrics> {
    return httpClient.get<PerformanceMetrics>(`/api/v1/logs/sessions/${sessionId}/performance`);
  },

  async deleteSessionLogs(sessionId: string): Promise<void> {
    return httpClient.delete<void>(`/api/v1/logs/sessions/${sessionId}`);
  },

  // Log export
  async exportSessionLogs(
    sessionId: string,
    format: 'json' | 'zip' = 'json'
  ): Promise<any> {
    const endpoint = `/api/v1/logs/export/${sessionId}?format=${format}`;

    if (format === 'zip') {
      // Handle file download - return blob for download
      const response = await fetch(`${httpClient['baseURL']}${endpoint}`);
      return response.blob();
    } else {
      return httpClient.get(endpoint);
    }
  },

  // Application logs
  async getApplicationLogs(
    limit: number = 100,
    level?: string
  ): Promise<ApplicationLog[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (level) params.append('level', level);

    return httpClient.get<ApplicationLog[]>(`/api/v1/logs/application?${params.toString()}`);
  },

  async getStartupLogs(): Promise<StartupLog[]> {
    return httpClient.get<StartupLog[]>('/api/v1/logs/startup');
  },

  // Frontend error logging
  async logFrontendError(errorData: FrontendErrorLog): Promise<void> {
    return httpClient.post<void>('/api/v1/logs/frontend-error', errorData);
  },
};