import React, { useState, useEffect } from 'react';
import {
  Cog6ToothIcon,
  KeyIcon,
  ServerIcon,
  CpuChipIcon,
  CircleStackIcon,
  DocumentIcon,
  ShieldCheckIcon,
  SwatchIcon,
  UserGroupIcon,
  BoltIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';
import { toast } from 'react-hot-toast';
import { settingsApi, EmbeddingCompatibility } from "@/lib/api";
import { useAppStore } from '@/lib/stores/app';
import { useAuthStore } from '@/lib/stores/auth';
import { notificationService } from '@/lib/services/notification.service';
import { debugLogger } from '@/lib/utils/debugLogger';
import { BrandedBadge } from '../shared/BrandedComponents';
import { BrandLogo } from '../shared/BrandLogo';
import { SlidingPanel } from '../core/SlidingPanel';

// Hot-reload indicator component
const HotReloadBadge: React.FC<{ requiresRestart?: boolean }> = ({ requiresRestart = false }) => {
  if (requiresRestart) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 ml-2 text-xs font-medium rounded-full bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
        <ArrowPathIcon className="h-3 w-3 mr-1" />
        Restart Required
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 ml-2 text-xs font-medium rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
      <BoltIcon className="h-3 w-3 mr-1" />
      Hot-Reload
    </span>
  );
};

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

  // Embedding Configuration
  embedding_provider?: string;
  embedding_model?: string;
  embedding_dimensions?: number;
  vision_model?: string;
  rag_similarity_threshold?: number;
  rag_top_k?: number;
  rag_decay_enabled?: boolean;
  rag_decay_alpha?: number;
  rag_decay_half_life_messages?: number;
  rag_decay_min_factor?: number;
  conversation_summary_enabled?: boolean;
  conversation_summary_trigger_count?: number;
  conversation_summary_window_size?: number;
  conversation_summary_max_tokens?: number;
  // Note: Summarizer uses llm_model from default LLM settings

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
  app_name: "AgentVerse",
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
  embedding_provider: "openai",
  embedding_model: "text-embedding-3-small",
  embedding_dimensions: 1536,
  vision_model: "gpt-4o",
  rag_similarity_threshold: 0.35,
  rag_top_k: 5,
  rag_decay_enabled: true,
  rag_decay_alpha: 0.7,
  rag_decay_half_life_messages: 50,
  rag_decay_min_factor: 0.1,
  conversation_summary_enabled: true,
  conversation_summary_trigger_count: 20,
  conversation_summary_window_size: 10,
  conversation_summary_max_tokens: 500,
  theme: "system",
  notifications_enabled: true,
  auto_save_interval: 30,
  sidebar_expanded: true
};

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ isOpen, onClose }) => {
  const { theme, setTheme, setSidebarExpanded } = useAppStore();
  const { canManageUsers, setAdminDashboardOpen } = useAuthStore();
  const [settings, setSettings] = useState<SettingsConfig>(defaultSettings);
  const [isDirty, setIsDirty] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState(notificationService.getSettings());
  const [embeddingCompatibility, setEmbeddingCompatibility] = useState<EmbeddingCompatibility | null>(null);
  const [showCompatibilityWarning, setShowCompatibilityWarning] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      // Don't check compatibility on every panel open - only when user interacts with Embeddings tab
      // This prevents unnecessary API calls and 500 errors
      // Load frontend settings from localStorage
      try {
        const frontendSettings = localStorage.getItem('frontend_settings');
        if (frontendSettings) {
          const parsed = JSON.parse(frontendSettings);
          setSettings(prev => ({
            ...prev,
            theme: parsed.theme || 'system',
            notifications_enabled: parsed.notifications_enabled ?? true,
            sidebar_expanded: parsed.sidebar_expanded ?? true,
            auto_save_interval: parsed.auto_save_interval || 30
          }));
        }
        // Refresh notification settings
        setNotificationSettings(notificationService.getSettings());
      } catch (error) {
        console.error('Failed to load frontend settings:', error);
      }
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // Try to load settings from backend using correct endpoint
      const response = await settingsApi.getSettings();

      // Merge backend settings with frontend settings (separate storage)
      const frontendSettings = JSON.parse(localStorage.getItem('frontend_settings') || '{}');

      if (response && (response as any).settings) {
        setSettings({ ...defaultSettings, ...(response as any).settings, ...frontendSettings });
      } else {
        setSettings({ ...defaultSettings, ...frontendSettings });
      }
    } catch (error) {
      console.warn('Failed to load backend settings, using defaults:', error);
      const frontendSettings = JSON.parse(localStorage.getItem('frontend_settings') || '{}');
      setSettings({ ...defaultSettings, ...frontendSettings });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);

      // Step 0: Check embedding compatibility BEFORE saving (critical check)
      // Only check if embedding-related settings were changed
      try {
        const compatibility = await settingsApi.checkEmbeddingCompatibility();
        if (!compatibility.compatible && compatibility.has_documents) {
          const confirmSave = window.confirm(
            `⚠️ WARNING: Embedding Provider Mismatch!\n\n` +
            `Your settings will change embedding provider from:\n` +
            `  ${compatibility.stored_provider} (${compatibility.stored_dimensions}d)\n` +
            `to:\n` +
            `  ${compatibility.current_provider} (${compatibility.current_dimensions}d)\n\n` +
            `This will make ${compatibility.document_count} existing documents UNSEARCHABLE!\n\n` +
            `Do you want to save these settings?\n\n` +
            `Click CANCEL to review settings\n` +
            `Click OK to proceed (you'll need to re-upload documents)`
          );

          if (!confirmSave) {
            setLoading(false);
            return; // User cancelled save
          }
        }
      } catch (compatError) {
        console.warn('Embedding compatibility check failed:', compatError);
        // Continue with save if compatibility check fails (database might be empty)
      }

      // Step 1: Validate settings before saving
      try {
        const validation = await settingsApi.validateSettings();
        if (!validation.is_valid) {
          const errors = validation.errors || [];
          const warnings = validation.warnings || [];

          if (errors.length > 0) {
            toast.error(`Settings validation failed: ${errors[0]}`);
            return;
          } else if (warnings.length > 0) {
            // Show warning but continue saving
            toast(`⚠️ Settings warning: ${warnings[0]}`, {
              style: {
                background: '#FEF3C7',
                color: '#92400E',
                border: '1px solid #F59E0B'
              }
            });
          }
        }
      } catch (validationError) {
        console.warn('Settings validation failed, continuing with save:', validationError);
        toast(`⚠️ Validation unavailable, saving anyway`, {
          style: {
            background: '#FEF3C7',
            color: '#92400E',
            border: '1px solid #F59E0B'
          }
        });
      }

      // Step 2: Save UI-specific settings to localStorage (frontend.json)
      const uiSettings = {
        theme: settings.theme,
        notifications_enabled: settings.notifications_enabled,
        auto_save_interval: settings.auto_save_interval
      };
      localStorage.setItem('frontend_settings', JSON.stringify(uiSettings));

      // Step 3: Apply changes ONLY when saving
      setTheme(settings.theme);

      // Apply sidebar setting
      if (settings.sidebar_expanded !== undefined) {
        setSidebarExpanded(settings.sidebar_expanded);
      }

      // Apply notification setting
      if (settings.notifications_enabled !== undefined) {
        notificationService.setEnabled(settings.notifications_enabled);
        if (settings.notifications_enabled) {
          const granted = await notificationService.requestPermission();
          if (granted) {
            await notificationService.notifySuccess(
              'Notifications Enabled',
              'You will now receive notifications when agents mention you'
            );
          }
        }
      }

      // Apply debug mode
      debugLogger.setDebugMode(settings.debug);

      setIsDirty(false);

      // Step 3: Prepare backend settings (exclude UI-only settings)
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
        log_file_max_size_mb: settings.log_file_max_size_mb,
        embedding_provider: settings.embedding_provider,
        embedding_model: settings.embedding_model,
        embedding_dimensions: settings.embedding_dimensions,
        vision_model: settings.vision_model,
        rag_similarity_threshold: settings.rag_similarity_threshold,
        rag_top_k: settings.rag_top_k,
        rag_decay_enabled: settings.rag_decay_enabled,
        rag_decay_alpha: settings.rag_decay_alpha,
        rag_decay_half_life_messages: settings.rag_decay_half_life_messages,
        rag_decay_min_factor: settings.rag_decay_min_factor,
        conversation_summary_enabled: settings.conversation_summary_enabled,
        conversation_summary_trigger_count: settings.conversation_summary_trigger_count,
        conversation_summary_window_size: settings.conversation_summary_window_size,
        conversation_summary_max_tokens: settings.conversation_summary_max_tokens
      };

      // Step 4: Save backend settings via API
      await settingsApi.updateSettings({ settings: backendSettings });

      setIsDirty(false);
      toast.success('Settings validated and saved successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const checkEmbeddingCompatibility = async () => {
    try {
      const compatibility = await settingsApi.checkEmbeddingCompatibility();
      setEmbeddingCompatibility(compatibility);

      // Show warning if incompatible and has documents
      if (!compatibility.compatible && compatibility.has_documents) {
        setShowCompatibilityWarning(true);
      }
    } catch (error) {
      console.error('Failed to check embedding compatibility:', error);
    }
  };

  const updateSetting = <K extends keyof SettingsConfig>(key: K, value: SettingsConfig[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setIsDirty(true);
  };

  const resetToDefaults = async () => {
    try {
      setSettings(defaultSettings);

      // Clear localStorage frontend settings
      localStorage.removeItem('frontend_settings');

      // Reset backend settings to defaults
      try {
        await settingsApi.resetSettings();
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


  const tabs = [
    { name: 'General', icon: Cog6ToothIcon },
    { name: 'API Keys', icon: KeyIcon },
    { name: 'Server', icon: ServerIcon },
    { name: 'LLM', icon: CpuChipIcon },
    { name: 'Embeddings', icon: CpuChipIcon },
    { name: 'Database', icon: CircleStackIcon },
    { name: 'Documents', icon: DocumentIcon },
    { name: 'Security', icon: ShieldCheckIcon },
    { name: 'Interface', icon: SwatchIcon },
  ];

  if (!isOpen) return null;

  const headerMeta = isDirty ? (
    <BrandedBadge variant="warning" size="sm">
      Unsaved Changes
    </BrandedBadge>
  ) : null;

  return (
    <SlidingPanel
      isOpen={isOpen}
      onClose={onClose}
      title="AgentVerse Settings"
      subtitle="Configure your multiverse of agents"
      icon={<BrandLogo variant="icon" size="md" />}
      meta={headerMeta}
      size="large"
      containerClassName="bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-3xl border border-violet-200/30 dark:border-violet-800/30 shadow-2xl"
      headerClassName="rounded-t-3xl border-b border-violet-200/30 dark:border-violet-800/30"
      contentClassName="flex flex-col flex-1 overflow-hidden"
    >
      <div className="flex-1 flex overflow-hidden">
          <Tab.Group vertical>
            <div className="flex w-full h-full">
              {/* Sidebar */}
              <div className="w-64 bg-gradient-to-b from-violet-50/50 to-indigo-50/30 dark:from-violet-950/30 dark:to-indigo-950/20 border-r border-violet-200/30 dark:border-violet-800/30">
                <Tab.List className="flex flex-col space-y-2 p-4">
                {tabs.map((tab) => (
                  <Tab
                    key={tab.name}
                    className={({ selected }) =>
                      `flex items-center space-x-3 w-full px-4 py-3 text-left rounded-xl transition-all duration-200 ${
                        selected
                          ? 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white shadow-lg shadow-violet-500/25'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-violet-100/50 dark:hover:bg-violet-900/30 hover:text-violet-600 dark:hover:text-violet-400'
                      }`
                    }
                  >
                    <tab.icon className="w-5 h-5" />
                    <span className="font-semibold">{tab.name}</span>
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
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                      LLM Configuration
                      <HotReloadBadge />
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
                        Model Name
                      </label>
                      <select
                        value={settings.llm_model || ''}
                        onChange={(e) => updateSetting('llm_model', e.target.value || undefined)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      >
                        {settings.llm_provider === 'openai' && (
                          <>
                            <option value="gpt-4o">GPT-4o (Latest)</option>
                            <option value="gpt-4o-mini">GPT-4o Mini (Fast & Cheap)</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                            <option value="gpt-4">GPT-4</option>
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                          </>
                        )}
                        {settings.llm_provider === 'anthropic' && (
                          <>
                            <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (Latest)</option>
                            <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (Fast)</option>
                            <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                            <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                            <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                          </>
                        )}
                        {settings.llm_provider === 'gemini' && (
                          <>
                            <option value="gemini-2.5-flash">Gemini 2.5 Flash (Latest)</option>
                            <option value="gemini-2.0-flash">Gemini 2.0 Flash (Stable)</option>
                            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                          </>
                        )}
                        {!['openai', 'anthropic', 'gemini'].includes(settings.llm_provider) && (
                          <option value="">Select a provider first</option>
                        )}
                      </select>
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

                {/* Embeddings Settings */}
                <Tab.Panel className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                      Embedding Configuration
                      <HotReloadBadge requiresRestart={true} />
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      Configure vector embeddings for Multi-Modal RAG (document search & retrieval)
                    </p>
                    <div className="mb-4 p-3 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                      <p className="text-sm text-orange-800 dark:text-orange-300">
                        <strong>⚠️ Server Restart Required:</strong> Changing embedding settings requires a server restart because vector database collections are initialized at startup.
                      </p>
                    </div>

                    {/* Check compatibility when Embeddings tab is viewed */}
                    <button
                      onClick={checkEmbeddingCompatibility}
                      className="mb-4 px-4 py-2 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                    >
                      🔍 Check Embedding Compatibility
                    </button>

                    {/* Compatibility Warning Banner */}
                    {embeddingCompatibility && !embeddingCompatibility.compatible && embeddingCompatibility.has_documents && (
                      <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-lg">
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <div className="ml-3">
                            <h4 className="text-sm font-bold text-red-800 dark:text-red-300">
                              ⚠️ Embedding Provider Mismatch Detected!
                            </h4>
                            <div className="mt-2 text-sm text-red-700 dark:text-red-400">
                              <p className="font-semibold mb-2">
                                Your vector database contains {embeddingCompatibility.document_count} documents indexed with:
                              </p>
                              <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Provider: <strong>{embeddingCompatibility.stored_provider}</strong></li>
                                <li>Model: <strong>{embeddingCompatibility.stored_model}</strong></li>
                                <li>Dimensions: <strong>{embeddingCompatibility.stored_dimensions}d</strong></li>
                              </ul>
                              <p className="mt-3 font-semibold">
                                Current settings use: <strong>{embeddingCompatibility.current_provider}</strong> ({embeddingCompatibility.current_dimensions}d)
                              </p>
                              <p className="mt-3 text-red-800 dark:text-red-300 font-bold">
                                🔴 CRITICAL: Existing documents will NOT be searchable with different embedding providers!
                              </p>
                              <p className="mt-2">
                                <strong>Recommendation:</strong> {embeddingCompatibility.recommendation}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Embedding Provider
                        </label>
                        <select
                          value={settings.embedding_provider || 'openai'}
                          onChange={(e) => {
                            const provider = e.target.value;

                            // Just update the UI - warning will show when user clicks Save
                            // This allows users to explore options without constant warnings
                            updateSetting('embedding_provider', provider);

                            // Auto-update dependent fields based on provider
                            if (provider === 'openai') {
                              updateSetting('embedding_model', 'text-embedding-3-small');
                              updateSetting('embedding_dimensions', 1536);
                              updateSetting('vision_model', 'gpt-4o');
                            } else if (provider === 'anthropic') {
                              updateSetting('embedding_model', 'voyage-3');
                              updateSetting('embedding_dimensions', 1024);
                              updateSetting('vision_model', 'claude-3-5-sonnet-20241022');
                            } else if (provider === 'gemini') {
                              updateSetting('embedding_model', 'gemini-embedding-001');
                              updateSetting('embedding_dimensions', 768);
                              updateSetting('vision_model', 'gemini-2.5-flash');
                            }
                          }}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          <option value="openai">OpenAI</option>
                          <option value="anthropic">Anthropic (Voyage AI)</option>
                          <option value="gemini">Google Gemini</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Text Embedding Model
                        </label>
                        <select
                          value={settings.embedding_model || ''}
                          onChange={(e) => {
                            const model = e.target.value;
                            updateSetting('embedding_model', model);

                            // Auto-update dimensions based on model
                            const dimensionsMap: Record<string, number> = {
                              'text-embedding-3-small': 1536,
                              'text-embedding-3-large': 3072,
                              'voyage-3': 1024,
                              'voyage-3-large': 1024,
                              'voyage-3-lite': 1024,
                              'voyage-code-3': 1024,
                              'gemini-embedding-001': 768,
                              'text-embedding-004': 768
                            };

                            if (dimensionsMap[model]) {
                              updateSetting('embedding_dimensions', dimensionsMap[model]);
                            }
                          }}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          {settings.embedding_provider === 'openai' && (
                            <>
                              <option value="text-embedding-3-small">text-embedding-3-small (1536d)</option>
                              <option value="text-embedding-3-large">text-embedding-3-large (3072d)</option>
                            </>
                          )}
                          {settings.embedding_provider === 'anthropic' && (
                            <>
                              <option value="voyage-3">voyage-3 (1024d) - Recommended</option>
                              <option value="voyage-3-large">voyage-3-large (1024d) - Best quality</option>
                              <option value="voyage-3-lite">voyage-3-lite (1024d) - Fast</option>
                              <option value="voyage-code-3">voyage-code-3 (1024d) - For code</option>
                            </>
                          )}
                          {settings.embedding_provider === 'gemini' && (
                            <>
                              <option value="gemini-embedding-001">gemini-embedding-001 (768d) - Latest</option>
                              <option value="text-embedding-004">text-embedding-004 (768d) - Deprecated 2026</option>
                            </>
                          )}
                        </select>
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Embedding Dimensions (Auto-configured)
                      </label>
                      <input
                        type="number"
                        value={settings.embedding_dimensions || 1536}
                        readOnly
                        disabled
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 cursor-not-allowed"
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Automatically set based on selected model
                      </p>
                    </div>

                    <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3">
                        Vision Configuration
                      </h4>
                      <div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Vision Model (Auto-configured)
                          </label>
                          <select
                            value={settings.vision_model || ''}
                            onChange={(e) => updateSetting('vision_model', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            {settings.embedding_provider === 'openai' && (
                              <>
                                <option value="gpt-4o">gpt-4o (Recommended)</option>
                                <option value="gpt-4-turbo">gpt-4-turbo</option>
                              </>
                            )}
                            {settings.embedding_provider === 'anthropic' && (
                              <>
                                <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet (Recommended)</option>
                                <option value="claude-3-opus-20240229">claude-3-opus</option>
                                <option value="claude-3-sonnet-20240229">claude-3-sonnet</option>
                              </>
                            )}
                            {settings.embedding_provider === 'gemini' && (
                              <>
                                <option value="gemini-2.5-flash">gemini-2.5-flash (Recommended, Latest)</option>
                                <option value="gemini-2.5-pro">gemini-2.5-pro (Best Quality)</option>
                                <option value="gemini-2.0-flash">gemini-2.0-flash (Stable)</option>
                              </>
                            )}
                          </select>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Matches embedding provider automatically
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* RAG Retrieval Settings */}
                    <div className="mt-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                        RAG Retrieval Configuration
                        <HotReloadBadge />
                      </h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                        Control how documents are retrieved and matched to queries • <span className="text-green-600 dark:text-green-400 font-semibold">Changes apply instantly</span>
                      </p>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Similarity Threshold
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={settings.rag_similarity_threshold || 0.35}
                            onChange={(e) => updateSetting('rag_similarity_threshold', parseFloat(e.target.value) || 0.35)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Minimum similarity (0-1). Higher = stricter filtering.
                          </p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Top K Results
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="20"
                            value={settings.rag_top_k || 5}
                            onChange={(e) => updateSetting('rag_top_k', parseInt(e.target.value) || 5)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Max chunks to retrieve per query
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Position-Based Decay (ArXiv 2509.19376) */}
                    <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center">
                          Position-Based Document Decay
                          <HotReloadBadge />
                        </h4>
                        <label className="inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.rag_decay_enabled ?? true}
                            onChange={(e) => updateSetting('rag_decay_enabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 dark:peer-focus:ring-green-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
                        </label>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                        Documents naturally lose relevance as conversation progresses (ArXiv 2509.19376 formula)
                      </p>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Alpha (α)
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={settings.rag_decay_alpha || 0.7}
                            onChange={(e) => updateSetting('rag_decay_alpha', parseFloat(e.target.value) || 0.7)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.rag_decay_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">Semantic weight (0.7 = 70%)</p>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Half-Life (messages)
                          </label>
                          <input
                            type="number"
                            min="10"
                            max="200"
                            step="10"
                            value={settings.rag_decay_half_life_messages || 50}
                            onChange={(e) => updateSetting('rag_decay_half_life_messages', parseInt(e.target.value) || 50)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.rag_decay_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">50% relevance after N msgs</p>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Min Factor
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="0.5"
                            step="0.05"
                            value={settings.rag_decay_min_factor || 0.1}
                            onChange={(e) => updateSetting('rag_decay_min_factor', parseFloat(e.target.value) || 0.1)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.rag_decay_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">Never below 10%</p>
                        </div>
                      </div>
                    </div>

                    {/* Conversation Summarization */}
                    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center">
                          Conversation Summarization
                          <HotReloadBadge requiresRestart={true} />
                        </h4>
                        <label className="inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.conversation_summary_enabled ?? true}
                            onChange={(e) => updateSetting('conversation_summary_enabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-4">
                        Progressive summarization: First 10 messages → Summary, Keep last 10 raw
                      </p>
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Trigger Count
                          </label>
                          <input
                            type="number"
                            min="10"
                            max="50"
                            value={settings.conversation_summary_trigger_count || 20}
                            onChange={(e) => updateSetting('conversation_summary_trigger_count', parseInt(e.target.value) || 20)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.conversation_summary_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">Start summarizing after N messages</p>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Window Size
                          </label>
                          <input
                            type="number"
                            min="5"
                            max="15"
                            value={settings.conversation_summary_window_size || 10}
                            onChange={(e) => updateSetting('conversation_summary_window_size', parseInt(e.target.value) || 10)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.conversation_summary_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">Summarize first N messages</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Summary Model
                            <span className="ml-2 text-xs text-gray-500">(Uses default LLM)</span>
                          </label>
                          <div className="px-3 py-2 text-sm bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">
                            {settings.llm_provider === 'openai' && (settings.llm_model || 'gpt-4o-mini')}
                            {settings.llm_provider === 'anthropic' && (settings.llm_model || 'claude-3-5-sonnet-20241022')}
                            {settings.llm_provider === 'gemini' && (settings.llm_model || 'gemini-2.5-flash')}
                            {!['openai', 'anthropic', 'gemini'].includes(settings.llm_provider) && (settings.llm_model || 'default')}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">Configure in LLM Settings tab</p>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Max Tokens
                          </label>
                          <input
                            type="number"
                            min="200"
                            max="2000"
                            step="100"
                            value={settings.conversation_summary_max_tokens || 500}
                            onChange={(e) => updateSetting('conversation_summary_max_tokens', parseInt(e.target.value) || 500)}
                            className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            disabled={!settings.conversation_summary_enabled}
                          />
                          <p className="text-xs text-gray-500 mt-1">Summary length limit</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        <strong>ℹ️ Recommended Settings (2025):</strong><br/>
                        • OpenAI: text-embedding-3-small (1536d) - Cost-effective<br/>
                        • Voyage AI: voyage-3 (1024d) - State-of-the-art (Anthropic partner)<br/>
                        • Gemini: gemini-embedding-001 (768d) - Latest model<br/><br/>
                        <strong>Vision Models:</strong> gpt-4o, claude-3-5-sonnet-20241022, gemini-2.5-flash<br/>
                        <strong>Image Processing:</strong> Vision LLM with 10K token limit (comprehensive OCR)<br/>
                        <em className="text-xs">Note: Gemini 1.5 deprecated - use Gemini 2.5 (latest) or 2.0 (stable)</em>
                      </p>
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
                          checked={settings.sidebar_expanded || false}
                          onChange={(e) => updateSetting('sidebar_expanded', e.target.checked)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <label htmlFor="sidebar_expanded" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Sidebar Expanded by Default
                        </label>
                      </div>
                      {/* Enable Notifications */}
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="notifications_enabled"
                          checked={notificationSettings.enabled}
                          onChange={(e) => {
                            const enabled = e.target.checked;
                            notificationService.setEnabled(enabled);
                            setNotificationSettings(notificationService.getSettings());
                          }}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                        <label htmlFor="notifications_enabled" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Enable Notifications
                        </label>
                      </div>

                      {/* Permission Status */}
                      <div className="mt-3 text-xs text-gray-600 dark:text-gray-400">
                        Permission: <span className="font-mono">
                          {typeof Notification !== 'undefined' ? Notification.permission : 'not supported'}
                        </span>
                      </div>

                      {/* Request Permission Button */}
                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={async () => {
                            try {
                              const granted = await notificationService.requestPermission();
                              if (granted) {
                                toast.success('Notification permission granted!');
                              } else {
                                toast.error('Notification permission denied. Please allow notifications in your browser settings.');
                              }
                            } catch (error) {
                              toast.error('Permission error: ' + String(error));
                            }
                          }}
                          className="px-3 py-1.5 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-lg transition-colors"
                        >
                          Request Permission
                        </button>
                      </div>

                      {/* Sound Selection */}
                      <div className="mt-4 space-y-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Notification Sound
                        </label>
                        <select
                          value={notificationSettings.sound}
                          onChange={(e) => {
                            const sound = e.target.value as any;
                            notificationService.setSound(sound);
                            setNotificationSettings(notificationService.getSettings());
                          }}
                          className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="none">None (Silent)</option>
                          <option value="bell">Bell</option>
                          <option value="chime">Chime</option>
                          <option value="beep">Beep</option>
                          <option value="ding">Ding</option>
                        </select>
                      </div>

                      {/* Volume Control */}
                      <div className="mt-4 space-y-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          Volume: {Math.round(notificationSettings.volume * 100)}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={notificationSettings.volume}
                          onChange={(e) => {
                            const volume = parseFloat(e.target.value);
                            notificationService.setVolume(volume);
                            setNotificationSettings(notificationService.getSettings());
                          }}
                          className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>

                      {/* Test Selected Sound */}
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={() => {
                            notificationService.playNotificationSound();
                            toast.success('Playing selected sound!');
                          }}
                          disabled={notificationSettings.sound === 'none'}
                          className="px-3 py-1.5 text-xs bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:hover:bg-green-900/50 text-green-700 dark:text-green-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Test Selected Sound
                        </button>
                      </div>
                    </div>
                  </div>
                </Tab.Panel>

                {/* Admin Tab (Enterprise Admins Only) */}
                {canManageUsers() && (
                  <Tab.Panel className="space-y-6">
                    <div>
                      <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 flex items-center space-x-2">
                        <span>👑</span>
                        <span>Enterprise Admin Controls</span>
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Manage users, groups, and resource permissions for your organization
                      </p>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">5</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Team Members</div>
                      </div>
                      <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
                        <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-1">4</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Active Groups</div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800">
                        <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">6</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Protected Resources</div>
                      </div>
                    </div>

                    {/* Admin Dashboard Button */}
                    <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border border-purple-200 dark:border-purple-800 rounded-2xl p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-lg font-bold text-gray-900 dark:text-white mb-2 flex items-center space-x-2">
                            <UserGroupIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                            <span>Full Admin Dashboard</span>
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                            Access the complete admin interface to manage users, groups, permissions, and resource access control. 
                            View detailed analytics, audit logs, and configure enterprise settings.
                          </p>
                          <ul className="space-y-2 mb-6">
                            <li className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                              <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
                              User & Group Management
                            </li>
                            <li className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                              <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
                              Access Control Matrix
                            </li>
                            <li className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                              <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
                              Resource Permissions (MCPs, Agents, Tools)
                            </li>
                            <li className="flex items-center text-sm text-gray-700 dark:text-gray-300">
                              <span className="w-5 h-5 bg-green-500 text-white rounded-full flex items-center justify-center mr-2 text-xs">✓</span>
                              Protected Resource Management
                            </li>
                          </ul>
                          <button
                            onClick={() => {
                              onClose();
                              setAdminDashboardOpen(true);
                            }}
                            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-xl font-semibold transition-all transform hover:scale-105 shadow-lg flex items-center justify-center space-x-2"
                          >
                            <ShieldCheckIcon className="w-5 h-5" />
                            <span>Open Admin Dashboard</span>
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Additional Info */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                      <p className="text-sm text-blue-900 dark:text-blue-300">
                        <strong>Note:</strong> The Admin Dashboard provides a full-screen interface for managing all aspects of your enterprise account. 
                        This includes advanced features like bulk user operations, group access matrices, and granular resource permissions.
                      </p>
                    </div>
                  </Tab.Panel>
                )}

              </Tab.Panels>
              </div>
            </div>
          </Tab.Group>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Settings Info */}
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-600 dark:text-gray-400">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span>📱 Interface settings save automatically</span>
                <span>⚙️ Backend settings require "Save Settings"</span>
              </div>
              {isDirty && <span className="text-orange-600 dark:text-orange-400 font-medium">● Unsaved backend changes</span>}
            </div>
          </div>

          <div className="flex items-center justify-between p-6">
          <div className="flex space-x-3">
            <button
              onClick={resetToDefaults}
              className="px-4 py-2 text-red-600 hover:text-red-700 border border-red-300 hover:border-red-400 rounded-lg transition-colors"
            >
              Reset to Defaults
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
              title={!isDirty ? 'No changes to save' : 'Save backend settings'}
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
          </div>
        </div>
    </SlidingPanel>
  );
};
