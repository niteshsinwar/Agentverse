/**
 * Tenant API Client
 *
 * Handles all tenant and tenant settings related API calls.
 */

import { cloudHttpClient } from '../cloud/httpClient';

/**
 * Tenant Settings Interface
 * Matches cloud_backend/apps/tenants/models.py::TenantSettings
 */
export interface TenantSettings {
  id: string;
  tenant_id: string;
  tenant_name: string;

  // Branding
  logo_url?: string;
  primary_color: string;
  company_website?: string;

  // Feature flags
  features_enabled: Record<string, boolean>;

  // Notification settings
  notifications_enabled: boolean;
  email_notifications: boolean;
  weekly_reports: boolean;

  // Integration settings
  integrations: Record<string, unknown>;

  // Custom settings
  custom_settings: Record<string, unknown>;

  // Metadata
  created_at: string;
  updated_at: string;
}

/**
 * Tenant Settings Update Request
 */
export interface UpdateTenantSettingsRequest {
  logo_url?: string;
  primary_color?: string;
  company_website?: string;
  features_enabled?: Record<string, boolean>;
  notifications_enabled?: boolean;
  email_notifications?: boolean;
  weekly_reports?: boolean;
  integrations?: Record<string, unknown>;
  custom_settings?: Record<string, unknown>;
}

/**
 * Get current tenant's settings
 *
 * GET /api/v1/tenants/settings/current/
 */
export async function getTenantSettings(): Promise<TenantSettings> {
  return cloudHttpClient.get('/api/v1/tenants/settings/current/');
}

/**
 * Update current tenant's settings (Admin only)
 *
 * PATCH /api/v1/tenants/settings/update_current/
 */
export async function updateTenantSettings(
  data: UpdateTenantSettingsRequest
): Promise<TenantSettings> {
  return cloudHttpClient.patch('/api/v1/tenants/settings/update_current/', data);
}
