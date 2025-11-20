/**
 * Tenant Settings Panel
 *
 * Admin-only interface for managing tenant-wide settings including:
 * - Branding (logo, colors, website)
 * - Feature flags
 * - Notification preferences
 * - Integrations
 */

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/stores/auth';
import { getTenantSettings, updateTenantSettings, type TenantSettings, type UpdateTenantSettingsRequest } from '@/lib/api/tenants';
import { PermissionDenied } from '@/components/shared/PermissionDenied';
import { toast } from 'react-hot-toast';
import { CogIcon, PaintBrushIcon, BellIcon, LinkIcon, SaveIcon, XMarkIcon } from '@heroicons/react/24/outline';

export function TenantSettingsPanel() {
  const { isAdmin } = useAuthStore();
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  // Form state
  const [logoUrl, setLogoUrl] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#6366f1');
  const [companyWebsite, setCompanyWebsite] = useState('');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [weeklyReports, setWeeklyReports] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getTenantSettings();
      setSettings(data);

      // Populate form
      setLogoUrl(data.logo_url || '');
      setPrimaryColor(data.primary_color || '#6366f1');
      setCompanyWebsite(data.company_website || '');
      setNotificationsEnabled(data.notifications_enabled);
      setEmailNotifications(data.email_notifications);
      setWeeklyReports(data.weekly_reports);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load settings';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!isAdmin()) {
      toast.error('Only admins can modify settings');
      return;
    }

    setSaving(true);
    setError(null);

    const updates: UpdateTenantSettingsRequest = {
      logo_url: logoUrl || undefined,
      primary_color: primaryColor,
      company_website: companyWebsite || undefined,
      notifications_enabled: notificationsEnabled,
      email_notifications: emailNotifications,
      weekly_reports: weeklyReports,
    };

    try {
      const updated = await updateTenantSettings(updates);
      setSettings(updated);
      setIsDirty(false);
      toast.success('Settings saved successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (!settings) return;

    setLogoUrl(settings.logo_url || '');
    setPrimaryColor(settings.primary_color || '#6366f1');
    setCompanyWebsite(settings.company_website || '');
    setNotificationsEnabled(settings.notifications_enabled);
    setEmailNotifications(settings.email_notifications);
    setWeeklyReports(settings.weekly_reports);
    setIsDirty(false);
  };

  const markDirty = () => {
    if (!isDirty) setIsDirty(true);
  };

  // Permission check
  if (!isAdmin()) {
    return (
      <PermissionDenied
        message="Only administrators can access tenant settings"
        action="manage tenant settings"
      />
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            Tenant Settings
          </h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Configure branding, features, and preferences for your organization
          </p>
        </div>

        <div className="flex gap-2">
          {isDirty && (
            <button
              onClick={handleReset}
              className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              <XMarkIcon className="h-4 w-4" />
              Reset
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={saving || !isDirty}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <SaveIcon className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Branding Section */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-4 flex items-center gap-2">
          <PaintBrushIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Branding
          </h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Logo URL
            </label>
            <input
              type="url"
              value={logoUrl}
              onChange={(e) => { setLogoUrl(e.target.value); markDirty(); }}
              placeholder="https://example.com/logo.png"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Primary Color
            </label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={primaryColor}
                onChange={(e) => { setPrimaryColor(e.target.value); markDirty(); }}
                className="h-10 w-20 cursor-pointer rounded-lg border border-slate-300 dark:border-slate-600"
              />
              <input
                type="text"
                value={primaryColor}
                onChange={(e) => { setPrimaryColor(e.target.value); markDirty(); }}
                placeholder="#6366f1"
                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Company Website
            </label>
            <input
              type="url"
              value={companyWebsite}
              onChange={(e) => { setCompanyWebsite(e.target.value); markDirty(); }}
              placeholder="https://example.com"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
            />
          </div>
        </div>
      </section>

      {/* Notifications Section */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <div className="mb-4 flex items-center gap-2">
          <BellIcon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Notifications
          </h3>
        </div>

        <div className="space-y-3">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Enable Notifications
            </span>
            <input
              type="checkbox"
              checked={notificationsEnabled}
              onChange={(e) => { setNotificationsEnabled(e.target.checked); markDirty(); }}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Email Notifications
            </span>
            <input
              type="checkbox"
              checked={emailNotifications}
              onChange={(e) => { setEmailNotifications(e.target.checked); markDirty(); }}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm text-slate-700 dark:text-slate-300">
              Weekly Reports
            </span>
            <input
              type="checkbox"
              checked={weeklyReports}
              onChange={(e) => { setWeeklyReports(e.target.checked); markDirty(); }}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
          </label>
        </div>
      </section>

      {/* Metadata */}
      {settings && (
        <div className="text-xs text-slate-500 dark:text-slate-500">
          Last updated: {new Date(settings.updated_at).toLocaleString()}
        </div>
      )}
    </div>
  );
}
