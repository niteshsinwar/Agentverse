import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Cog6ToothIcon,
  XMarkIcon,
  KeyIcon,
  ServerIcon,
  CpuChipIcon,
  CircleStackIcon,
  DocumentIcon,
  ShieldCheckIcon,
  SwatchIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';
import { toast } from 'react-hot-toast';
import { apiService } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';

interface SettingsConfig {
  // Application Core Settings
  app_name: string;
  version: string;
  environment: 'development' | 'staging' | 'production' | 'testing';
  debug: boolean;

  // Server Configuration
  host: string;
  port: number;
  allowed_origins: string[];

  // LLM Provider API Keys
  openai_api_key?: string;
  anthropic_api_key?: string;
  gemini_api_key?: string;
  github_token?: string;

  // Database Configuration
  database_url: string;

  // Document Processing
  max_upload_size_mb: number;
  supported_file_formats: string[];

  // Agent Configuration
  max_agent_iterations: number;
  default_temperature: number;
  default_max_tokens: number;

  // LLM Configuration
  llm_provider: string;
  llm_model?: string;
  llm_temperature: number;
  llm_max_tokens: number;
  llm_fallback_provider?: string;

  // Security Settings
  secret_key: string;
  session_timeout_hours: number;

  // Logging Configuration
  log_level: string;
  enable_file_logging: boolean;
  log_file_max_size_mb: number;

  // UI Settings (frontend only)
  theme: 'light' | 'dark' | 'system';
  sidebar_expanded: boolean;
  notifications_enabled: boolean;
  auto_save_interval: number;
}

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const defaultSettings: SettingsConfig = {
  app_name: "Agentic SF Developer Backend",
  version: "1.0.0",
  environment: "development",
  debug: false,
  host: "0.0.0.0",
  port: 8000,
  allowed_origins: ["http://localhost:1420", "https://tauri.localhost"],
  database_url: "sqlite:///./data/app.db",
  max_upload_size_mb: 10,
  supported_file_formats: ["txt", "csv", "json", "pdf", "docx", "md","png"],
  max_agent_iterations: 5,
  default_temperature: 0.2,
  default_max_tokens: 4096,
  llm_provider: "openai",
  llm_temperature: 0.2,
  llm_max_tokens: 4096,
  secret_key: "dev-key-change-in-production",
  session_timeout_hours: 24,
  log_level: "INFO",
  enable_file_logging: true,
  log_file_max_size_mb: 10,
  theme: "system",
  sidebar_expanded: true,
  notifications_enabled: true,
  auto_save_interval: 30
};

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose }) => {
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState<SettingsConfig>(defaultSettings);
  const [isDirty, setIsDirty] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // Try to load settings from backend using correct endpoint
      const response = await apiService.getSettings();

      // Merge backend settings with local UI settings
      const localSettings = JSON.parse(localStorage.getItem('app_settings') || '{}');

      if (response && response.settings) {
        setSettings({ ...defaultSettings, ...response.settings, ...localSettings });
      } else {
        setSettings({ ...defaultSettings, ...localSettings });
      }
    } catch (error) {
      console.warn('Failed to load backend settings, using defaults:', error);
      const localSettings = JSON.parse(localStorage.getItem('app_settings') || '{}');
      setSettings({ ...defaultSettings, ...localSettings });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);

      // Save UI-specific settings to localStorage
      const uiSettings = {
        theme: settings.theme,
        sidebar_expanded: settings.sidebar_expanded,
        notifications_enabled: settings.notifications_enabled,
        auto_save_interval: settings.auto_save_interval
      };
      localStorage.setItem('app_settings', JSON.stringify(uiSettings));

      // Prepare backend settings (exclude UI-only settings)
      const backendSettings = {
        app_name: settings.app_name,
        version: settings.version,
        environment: settings.environment,
        debug: settings.debug,
        host: settings.host,
        port: settings.port,
        allowed_origins: settings.allowed_origins,
        openai_api_key: settings.openai_api_key,
        anthropic_api_key: settings.anthropic_api_key,
        gemini_api_key: settings.gemini_api_key,
        github_token: settings.github_token,
        database_url: settings.database_url,
        max_upload_size_mb: settings.max_upload_size_mb,
        supported_file_formats: settings.supported_file_formats,
        max_agent_iterations: settings.max_agent_iterations,
        default_temperature: settings.default_temperature,
        default_max_tokens: settings.default_max_tokens,
        llm_provider: settings.llm_provider,
        llm_model: settings.llm_model,
        llm_temperature: settings.llm_temperature,
        llm_max_tokens: settings.llm_max_tokens,
        llm_fallback_provider: settings.llm_fallback_provider,
        secret_key: settings.secret_key,
        session_timeout_hours: settings.session_timeout_hours,
        log_level: settings.log_level,
        enable_file_logging: settings.enable_file_logging,
        log_file_max_size_mb: settings.log_file_max_size_mb
      };

      // Save backend settings via API using correct endpoint
      await apiService.updateSettings(backendSettings);

      setIsDirty(false);
      toast.success('Settings saved successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = <K extends keyof SettingsConfig>(key: K, value: SettingsConfig[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setIsDirty(true);
  };

  const resetToDefaults = async () => {
    try {
      setSettings(defaultSettings);

      // Clear localStorage UI settings
      localStorage.removeItem('app_settings');

      // Reset backend settings to defaults
      try {
        await apiService.resetSettings();
      } catch (error) {
        console.warn('Failed to reset backend settings:', error);
      }

      setIsDirty(false);
      toast.success('Settings reset to defaults');
    } catch (error) {
      console.error('Failed to reset settings:', error);
      toast.error('Failed to reset settings');
    }
  };

  const validateSettings = async () => {
    try {
      const validation = await apiService.validateSettings();
      if (validation.valid) {
        toast.success('All settings are valid');
      } else {
        const errors = validation.errors || [];
        const warnings = validation.warnings || [];

        if (errors.length > 0) {
          toast.error(`Settings validation failed: ${errors[0]}`);
        } else if (warnings.length > 0) {
          // Use toast with custom style for warnings since react-hot-toast doesn't have warning by default
          toast(`⚠️ Settings warnings: ${warnings[0]}`, {
            style: {
              background: '#FEF3C7',
              color: '#92400E',
              border: '1px solid #F59E0B'
            }
          });
        }
      }
      return validation;
    } catch (error) {
      console.error('Failed to validate settings:', error);
      toast.error('Failed to validate settings');
      return { valid: false, errors: ['Validation failed'], warnings: [] };
    }
  };

  const tabs = [
    { name: 'General', icon: Cog6ToothIcon },
    { name: 'API Keys', icon: KeyIcon },
    { name: 'Server', icon: ServerIcon },
    { name: 'LLM', icon: CpuChipIcon },
    { name: 'Database', icon: CircleStackIcon },
    { name: 'Documents', icon: DocumentIcon },
    { name: 'Security', icon: ShieldCheckIcon },
    { name: 'Interface', icon: SwatchIcon }
  ];

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Cog6ToothIcon className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
            {isDirty && (
              <span className="px-2 py-1 bg-amber-100 text-amber-800 text-xs rounded-full">
                Unsaved Changes
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          <Tab.Group vertical>
            <div className="flex w-full h-full">
              {/* Sidebar */}
              <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700">
                <Tab.List className="flex flex-col space-y-1 p-4">
                {tabs.map((tab) => (
                  <Tab
                    key={tab.name}
                    className={({ selected }) =>
                      `flex items-center space-x-3 w-full px-4 py-3 text-left rounded-xl transition-colors ${
                        selected
                          ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`
                    }
                  >
                    <tab.icon className="w-5 h-5" />
                    <span className="font-medium">{tab.name}</span>
                  </Tab>
                ))}
              </Tab.List>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto">
              <Tab.Panels className="p-6">
                {/* General Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      General Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Application Name
                        </label>
                        <input
                          type="text"
                          value={settings.app_name}
                          onChange={(e) => updateSetting('app_name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Environment
                        </label>
                        <select
                          value={settings.environment}
                          onChange={(e) => updateSetting('environment', e.target.value as any)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="development">Development</option>
                          <option value="staging">Staging</option>
                          <option value="production">Production</option>
                          <option value="testing">Testing</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 mt-4">
                      <input
                        type="checkbox"
                        id="debug"
                        checked={settings.debug}
                        onChange={(e) => updateSetting('debug', e.target.checked)}
                        className="rounded border-gray-300 dark:border-gray-600"
                      />
                      <label htmlFor="debug" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Enable Debug Mode
                      </label>
                    </div>
                  </div>
                </Tab.Panel>

                {/* API Keys */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      API Keys Configuration
                    </h3>
                    <div className="space-y-4">
                      {[
                        { key: 'openai_api_key', label: 'OpenAI API Key', placeholder: 'sk-...' },
                        { key: 'anthropic_api_key', label: 'Anthropic API Key', placeholder: 'sk-ant-...' },
                        { key: 'gemini_api_key', label: 'Google Gemini API Key', placeholder: 'AIza...' },
                        { key: 'github_token', label: 'GitHub Token', placeholder: 'ghp_...' }
                      ].map(({ key, label, placeholder }) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            {label}
                          </label>
                          <input
                            type="password"
                            value={settings[key as keyof SettingsConfig] as string || ''}
                            onChange={(e) => updateSetting(key as keyof SettingsConfig, e.target.value)}
                            placeholder={placeholder}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </Tab.Panel>

                {/* Server Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Server Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Host
                        </label>
                        <input
                          type="text"
                          value={settings.host}
                          onChange={(e) => updateSetting('host', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Port
                        </label>
                        <input
                          type="number"
                          value={settings.port}
                          onChange={(e) => updateSetting('port', parseInt(e.target.value) || 8000)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Allowed Origins (comma-separated)
                      </label>
                      <input
                        type="text"
                        value={Array.isArray(settings.allowed_origins) ? settings.allowed_origins.join(', ') : ''}
                        onChange={(e) => updateSetting('allowed_origins', e.target.value.split(',').map(s => s.trim()))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="http://localhost:1420, https://tauri.localhost"
                      />
                    </div>
                  </div>
                </Tab.Panel>

                {/* LLM Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      LLM Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Primary Provider
                        </label>
                        <select
                          value={settings.llm_provider}
                          onChange={(e) => updateSetting('llm_provider', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic</option>
                          <option value="gemini">Google Gemini</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Fallback Provider
                        </label>
                        <select
                          value={settings.llm_fallback_provider || ''}
                          onChange={(e) => updateSetting('llm_fallback_provider', e.target.value || undefined)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="">None</option>
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic</option>
                          <option value="gemini">Google Gemini</option>
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Temperature ({settings.llm_temperature})
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="2"
                          step="0.1"
                          value={settings.llm_temperature}
                          onChange={(e) => updateSetting('llm_temperature', parseFloat(e.target.value))}
                          className="w-full"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Max Tokens
                        </label>
                        <input
                          type="number"
                          value={settings.llm_max_tokens}
                          onChange={(e) => updateSetting('llm_max_tokens', parseInt(e.target.value) || 4096)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Model Name (Optional)
                      </label>
                      <input
                        type="text"
                        value={settings.llm_model || ''}
                        onChange={(e) => updateSetting('llm_model', e.target.value || undefined)}
                        placeholder="e.g., gpt-4, claude-3-sonnet, gemini-pro"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>

                    <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                        Agent Configuration
                      </h4>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Max Iterations
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="20"
                            value={settings.max_agent_iterations}
                            onChange={(e) => updateSetting('max_agent_iterations', parseInt(e.target.value) || 5)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Default Temperature ({settings.default_temperature})
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="2"
                            step="0.1"
                            value={settings.default_temperature}
                            onChange={(e) => updateSetting('default_temperature', parseFloat(e.target.value))}
                            className="w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Default Max Tokens
                          </label>
                          <input
                            type="number"
                            value={settings.default_max_tokens}
                            onChange={(e) => updateSetting('default_max_tokens', parseInt(e.target.value) || 4096)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </Tab.Panel>

                {/* Database Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Database Configuration
                    </h3>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Database URL
                      </label>
                      <input
                        type="text"
                        value={settings.database_url}
                        onChange={(e) => updateSetting('database_url', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                      />
                    </div>
                  </div>
                </Tab.Panel>

                {/* Documents Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Document Processing
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Max Upload Size (MB)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="100"
                          value={settings.max_upload_size_mb}
                          onChange={(e) => updateSetting('max_upload_size_mb', parseInt(e.target.value) || 10)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                        <p className="text-xs text-gray-500 mt-1">Maximum file size for document uploads</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Supported File Formats (comma-separated)
                      </label>
                      <input
                        type="text"
                        value={Array.isArray(settings.supported_file_formats) ? settings.supported_file_formats.join(', ') : ''}
                        onChange={(e) => updateSetting('supported_file_formats', e.target.value.split(',').map(s => s.trim().toLowerCase()))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="txt, csv, json, pdf, docx, md, png"
                      />
                      <p className="text-xs text-gray-500 mt-1">File extensions allowed for upload (without dots)</p>
                    </div>

                    <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                        Logging Configuration
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Log Level
                          </label>
                          <select
                            value={settings.log_level}
                            onChange={(e) => updateSetting('log_level', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="DEBUG">Debug</option>
                            <option value="INFO">Info</option>
                            <option value="WARNING">Warning</option>
                            <option value="ERROR">Error</option>
                            <option value="CRITICAL">Critical</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Max Log File Size (MB)
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="100"
                            value={settings.log_file_max_size_mb}
                            onChange={(e) => updateSetting('log_file_max_size_mb', parseInt(e.target.value) || 10)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      </div>
                      <div className="mt-3">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="enable_file_logging"
                            checked={settings.enable_file_logging}
                            onChange={(e) => updateSetting('enable_file_logging', e.target.checked)}
                            className="rounded border-gray-300 dark:border-gray-600"
                          />
                          <label htmlFor="enable_file_logging" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Enable File Logging
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </Tab.Panel>

                {/* Security Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Security Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Secret Key
                        </label>
                        <input
                          type="password"
                          value={settings.secret_key}
                          onChange={(e) => updateSetting('secret_key', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Session Timeout (hours)
                        </label>
                        <input
                          type="number"
                          value={settings.session_timeout_hours}
                          onChange={(e) => updateSetting('session_timeout_hours', parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                  </div>
                </Tab.Panel>

                {/* Interface Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Interface Configuration
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Theme
                        </label>
                        <select
                          value={theme}
                          onChange={(e) => {
                            const newTheme = e.target.value as 'light' | 'dark' | 'system';
                            setTheme(newTheme);
                            updateSetting('theme', newTheme);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="light">Light</option>
                          <option value="dark">Dark</option>
                          <option value="system">System</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Auto-save Interval (seconds)
                        </label>
                        <input
                          type="number"
                          value={settings.auto_save_interval}
                          onChange={(e) => updateSetting('auto_save_interval', parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                      </div>
                    </div>
                    <div className="space-y-3 mt-4">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="sidebar_expanded"
                          checked={settings.sidebar_expanded}
                          onChange={(e) => updateSetting('sidebar_expanded', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <label htmlFor="sidebar_expanded" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Sidebar Expanded by Default
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="notifications_enabled"
                          checked={settings.notifications_enabled}
                          onChange={(e) => updateSetting('notifications_enabled', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <label htmlFor="notifications_enabled" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Enable Notifications
                        </label>
                      </div>
                    </div>
                  </div>
                </Tab.Panel>
              </Tab.Panels>
              </div>
            </div>
          </Tab.Group>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex space-x-3">
            <button
              onClick={resetToDefaults}
              className="px-4 py-2 text-red-600 hover:text-red-700 border border-red-300 hover:border-red-400 rounded-lg transition-colors"
            >
              Reset to Defaults
            </button>
            <button
              onClick={validateSettings}
              className="px-4 py-2 text-blue-600 hover:text-blue-700 border border-blue-300 hover:border-blue-400 rounded-lg transition-colors"
            >
              Validate Settings
            </button>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-6 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={saveSettings}
              disabled={loading || !isDirty}
              className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};