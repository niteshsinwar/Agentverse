/**
 * Settings API
 * API endpoints for application settings management
 */

import { httpClient } from '../client/http-client';
import type {
  Settings,
  UpdateSettingsRequest,
  SystemInfo,
  ConfigStatus,
} from '../types/entities';

export interface SettingsValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  config_preview?: Settings;
}

export const settingsApi = {
  // Settings CRUD operations
  async getSettings(): Promise<Settings> {
    return httpClient.get<Settings>('/api/v1/config/settings/');
  },

  async updateSettings(data: UpdateSettingsRequest): Promise<Settings> {
    return httpClient.post<Settings>('/api/v1/config/settings/', data);
  },

  async resetSettings(): Promise<void> {
    return httpClient.delete<void>('/api/v1/config/settings/');
  },

  // Settings validation
  async validateSettings(): Promise<SettingsValidationResult> {
    return httpClient.get<SettingsValidationResult>('/api/v1/config/settings/validate/');
  },

  // System information
  async getSystemInfo(): Promise<SystemInfo> {
    return httpClient.get<SystemInfo>('/api/v1/analytics/system/modules/');
  },

  async getConfigStatus(): Promise<ConfigStatus> {
    return httpClient.get<ConfigStatus>('/api/v1/config/status/');
  },

  // Configuration backup
  async createConfigBackup(): Promise<{ backup_id: string; created_at: string }> {
    return httpClient.post<{ backup_id: string; created_at: string }>('/api/v1/config/backup/');
  },
};