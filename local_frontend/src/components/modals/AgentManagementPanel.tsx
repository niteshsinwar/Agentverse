import React, { useState, useEffect } from 'react';
import {
  CheckIcon,
  WrenchIcon,
  ServerIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';
import { toast } from 'react-hot-toast';
import { apiService } from '@/lib/api';
import { ProgressBar, useProgressSteps } from '../shared/ProgressBar';
import { BrandedButton } from '../shared/BrandedComponents';
import { BrandLogo } from '../shared/BrandLogo';
import { SlidingPanel } from '../core/SlidingPanel';

// Pre-built tools and MCP configurations will be loaded from API

interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
  llm?: {
    provider: string;
    model: string;
  };
}

interface ToolSelection {
  id: string;
  enabled: boolean;
}

interface MCPSelection {
  id: string;
  enabled: boolean;
  config?: Record<string, unknown>;
}

interface AgentManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
  agentToEdit?: Agent | null;
  onAgentCreated?: () => void;
  onAgentUpdated?: () => void;
}

export const AgentManagementPanel: React.FC<AgentManagementPanelProps> = ({
  isOpen,
  onClose,
  agentToEdit,
  onAgentCreated,
  onAgentUpdated,
}) => {
  const [loading, setLoading] = useState(false);
  const isEditing = !!agentToEdit;

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    emoji: '🤖',
    key: '',
    llm: {
      provider: 'openai',
      model: 'gpt-4o-mini'
    }
  });

  // Tool and MCP selections
  const [selectedTools, setSelectedTools] = useState<ToolSelection[]>([]);
  const [selectedMCPs, setSelectedMCPs] = useState<MCPSelection[]>([]);
  const [customToolsCode, setCustomToolsCode] = useState('');
  const [customMCPConfig, setCustomMCPConfig] = useState('{}');
  const [selectedTabIndex, setSelectedTabIndex] = useState(0);

  // Configuration data loaded from API
  const [prebuiltTools, setPrebuiltTools] = useState<Record<string, any>>({});
  const [prebuiltMCPs, setPrebuiltMCPs] = useState<Record<string, any>>({});

  // Progress bar for creation/editing
  const agentSteps = ['Verifying Configuration', 'Validating Tools & MCP', 'Deploying Agent'];
  const progressSteps = useProgressSteps(agentSteps);

  useEffect(() => {
    loadConfigurations();
  }, []);

  useEffect(() => {
    if (agentToEdit && isOpen) {
      // Ensure configurations are loaded before populating agent data
      if (Object.keys(prebuiltTools).length > 0 || Object.keys(prebuiltMCPs).length > 0) {
        loadAgentConfiguration(agentToEdit);
      } else {
        // If configurations haven't loaded yet, try again after a short delay
        const timer = setTimeout(() => {
          loadAgentConfiguration(agentToEdit);
        }, 500);
        return () => clearTimeout(timer);
      }
    } else if (!agentToEdit && isOpen) {
      resetForm();
    }
  }, [agentToEdit, isOpen, prebuiltTools, prebuiltMCPs]);

  const loadConfigurations = async () => {
    try {
      setLoading(true);

      // Load tools and MCPs separately to better handle errors
      let tools = {};
      let mcps = {};

      try {
        const toolsResponse = await apiService.getTools();
        console.log('Tools API response:', toolsResponse);
        tools = (toolsResponse as any)?.tools || toolsResponse || {};
      } catch (error) {
        console.error('Failed to load tools:', error);
        toast.error('Failed to load pre-built tools');
      }

      try {
        const mcpsResponse = await apiService.getMcpServers();
        console.log('MCPs API response:', mcpsResponse);
        mcps = (mcpsResponse as any)?.mcpServers || mcpsResponse || {};
      } catch (error) {
        console.error('Failed to load MCP servers:', error);
        toast.error('Failed to load MCP servers');
      }

      console.log('Final processed tools:', tools);
      console.log('Final processed MCPs:', mcps);

      setPrebuiltTools(tools);
      setPrebuiltMCPs(mcps);
      initializeSelections(tools, mcps);

      if (Object.keys(tools).length === 0 && Object.keys(mcps).length === 0) {
        toast('⚠️ No pre-built tools or MCP servers found', {
          style: {
            background: '#FEF3C7',
            color: '#92400E',
            border: '1px solid #F59E0B'
          }
        });
      }
    } catch (error) {
      console.error('Failed to load configurations:', error);
      toast.error('Failed to load tools and MCP configurations');
    } finally {
      setLoading(false);
    }
  };

  const initializeSelections = (tools = prebuiltTools, mcps = prebuiltMCPs) => {
    const toolSelections = Object.keys(tools).map(id => ({
      id,
      enabled: false
    }));
    const mcpSelections = Object.keys(mcps).map(id => ({
      id,
      enabled: false
    }));

    setSelectedTools(toolSelections);
    setSelectedMCPs(mcpSelections);
  };

  const loadAgentConfiguration = async (agent: Agent) => {
    try {
      // Populate basic form data
      setFormData({
        name: agent.name,
        description: agent.description,
        emoji: agent.emoji,
        key: agent.key,
        llm: agent.llm || { provider: 'openai', model: 'gpt-4o-mini' }
      });

      // Try to load the complete agent data to get tools and MCP configurations
      try {
        const completeAgentData = await apiService.getAvailableAgents() as any[];
        const fullAgent = completeAgentData.find((a: any) => a.key === agent.key) || agent;
        
        // Load selected tools if available
        if (fullAgent.selected_tools && Array.isArray(fullAgent.selected_tools)) {
          setSelectedTools(prev => prev.map(tool => ({
            ...tool,
            enabled: fullAgent.selected_tools.includes(tool.id)
          })));
        }

        // Load selected MCPs if available
        if (fullAgent.selected_mcps && Array.isArray(fullAgent.selected_mcps)) {
          setSelectedMCPs(prev => prev.map(mcp => ({
            ...mcp,
            enabled: fullAgent.selected_mcps.includes(mcp.id)
          })));
        }

        // Load custom tools code if available (legacy support)
        if (fullAgent.tools_code) {
          setCustomToolsCode(fullAgent.tools_code);
          setSelectedTabIndex(3); // Switch to Custom Code tab
        }

        // Load custom MCP config if available (legacy support)
        if (fullAgent.mcp_config) {
          const mcpConfigStr = typeof fullAgent.mcp_config === 'string'
            ? fullAgent.mcp_config
            : JSON.stringify(fullAgent.mcp_config, null, 2);
          setCustomMCPConfig(mcpConfigStr);
          if (!fullAgent.tools_code) {
            setSelectedTabIndex(3); // Switch to Custom Code tab
          }
        }

        console.log('Agent configuration loaded successfully:', fullAgent);
      } catch (error) {
        console.warn('Could not load complete agent data, using basic info only:', error);
      }
    } catch (error) {
      console.error('Failed to load agent configuration:', error);
    }
  };


  const generateToolsCode = () => {
    const enabledTools = selectedTools.filter(t => t.enabled);
    let code = '';

    enabledTools.forEach(tool => {
      const toolData = prebuiltTools[tool.id as keyof typeof prebuiltTools];
      if (toolData) {
        code += `# ${toolData.name}\n# ${toolData.description}\n\n${toolData.code}\n\n\n`;
      }
    });

    if (customToolsCode.trim()) {
      code += `# Custom Tools\n${customToolsCode}\n`;
    }

    return code;
  };

  const generateMCPConfig = () => {
    const enabledMCPs = selectedMCPs.filter(m => m.enabled);
    const mcpServers: any = {};

    enabledMCPs.forEach(mcp => {
      const mcpData = prebuiltMCPs[mcp.id as keyof typeof prebuiltMCPs];
      if (mcpData) {
        // In the new format, mcpData IS the server config (command, args, env)
        mcpServers[mcp.id] = {
          ...mcpData,
          ...mcp.config
        };
      }
    });

    // Add custom MCP config
    try {
      const customConfig = JSON.parse(customMCPConfig);
      // If custom config has mcpServers wrapper, merge it
      if (customConfig.mcpServers) {
        Object.assign(mcpServers, customConfig.mcpServers);
      } else {
        // Otherwise assume the custom config is direct server configs
        Object.assign(mcpServers, customConfig);
      }
    } catch (error) {
      console.warn('Invalid custom MCP config:', error);
    }

    // Return in the expected format with mcpServers wrapper
    return { mcpServers };
  };

  const handleCreateAgent = async () => {
    try {
      setLoading(true);
      progressSteps.startProgress();

      // Step 1: Verifying Configuration
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      const agentData = {
        ...formData,
        key: formData.key || formData.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
        tools_code: generateToolsCode(),
        mcp_config: generateMCPConfig(),
        selected_tools: selectedTools.filter(t => t.enabled).map(t => t.id),
        selected_mcps: selectedMCPs.filter(m => m.enabled).map(m => m.id)
      };

      // Step 2: Validating Tools & MCP
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Step 3: Deploying Agent
      await new Promise(resolve => setTimeout(resolve, 500));
      await apiService.createAgent(agentData);

      progressSteps.completeProgress();
      toast.success(`Agent "${formData.name}" created successfully!`);
      resetForm();
      onClose();
      onAgentCreated?.();

    } catch (error: any) {
      progressSteps.hideProgress();

      // Show specific error message
      if (error?.validation_errors) {
        const validationData = error.validation_errors;
        if (validationData?.errors?.length > 0) {
          const errorMessage = validationData.errors.map((err: any) => `${err.field}: ${err.message}`).join(', ');
          toast.error(`Validation failed: ${errorMessage}`);
        } else {
          toast.error('Agent configuration validation failed');
        }
      } else if (error?.message) {
        toast.error(`Failed to create agent: ${error.message}`);
      } else {
        toast.error('Failed to create agent');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAgent = async () => {
    if (!agentToEdit) return;

    try {
      setLoading(true);
      progressSteps.startProgress();

      // Step 1: Verifying Configuration
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      const agentData = {
        ...formData,
        tools_code: generateToolsCode(),
        mcp_config: generateMCPConfig(),
        selected_tools: selectedTools.filter(t => t.enabled).map(t => t.id),
        selected_mcps: selectedMCPs.filter(m => m.enabled).map(m => m.id)
      };

      // Step 2: Validating Tools & MCP
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Step 3: Deploying Agent
      await new Promise(resolve => setTimeout(resolve, 500));
      await apiService.updateAgent(agentToEdit.key, agentData);

      progressSteps.completeProgress();
      toast.success(`Agent "${formData.name}" updated successfully!`);
      resetForm();
      onClose();
      onAgentUpdated?.();

    } catch (error: any) {
      progressSteps.hideProgress();

      // Show specific error message
      if (error?.validation_errors) {
        const validationData = error.validation_errors;
        if (validationData?.errors?.length > 0) {
          const errorMessage = validationData.errors.map((err: any) => `${err.field}: ${err.message}`).join(', ');
          toast.error(`Validation failed: ${errorMessage}`);
        } else {
          toast.error('Agent configuration validation failed');
        }
      } else if (error?.message) {
        toast.error(`Failed to update agent: ${error.message}`);
      } else {
        toast.error('Failed to update agent');
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      emoji: '🤖',
      key: '',
      llm: {
        provider: 'openai',
        model: 'gpt-4o-mini'
      }
    });
    initializeSelections();
    setCustomToolsCode('');
    setCustomMCPConfig('{}');
  };

  const toggleTool = (toolId: string) => {
    setSelectedTools(prev => prev.map(tool =>
      tool.id === toolId ? { ...tool, enabled: !tool.enabled } : tool
    ));
  };

  const toggleMCP = (mcpId: string) => {
    setSelectedMCPs(prev => prev.map(mcp =>
      mcp.id === mcpId ? { ...mcp, enabled: !mcp.enabled } : mcp
    ));
  };

  return (
    <>
      <SlidingPanel
        isOpen={isOpen}
        onClose={onClose}
        title={isEditing ? 'Edit Agent' : 'Create New Agent'}
        subtitle="Configure your AI agent with custom tools and MCP servers"
        icon={<BrandLogo variant="icon" size="sm" />}
        size="medium"
        contentClassName="flex flex-col overflow-hidden"
      >
        <div className="flex-1 overflow-auto">
          <div className="p-6">
            <Tab.Group selectedIndex={selectedTabIndex} onChange={setSelectedTabIndex}>
                  <Tab.List className="flex space-x-1 rounded-2xl brand-glass p-1 mb-6">
                    {['Basic Info', 'Pre-built Tools', 'Pre-built MCP', 'Custom Code'].map((tab) => (
                      <Tab
                        key={tab}
                        className={({ selected }) =>
                          `w-full rounded-xl py-2.5 text-sm font-semibold leading-5 text-center transition-all duration-200 ${
                            selected
                              ? 'brand-gradient text-white shadow-lg shadow-sky-500/25'
                              : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-white/60 dark:hover:bg-slate-800/60'
                          }`
                        }
                      >
                        {tab}
                      </Tab>
                    ))}
                  </Tab.List>

                  <Tab.Panels>
                    {/* Basic Info Tab */}
                    <Tab.Panel className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                            Agent Name
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="brand-field w-full rounded-xl px-3 py-2 text-sm"
                            placeholder="My Agent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                            Agent Key
                          </label>
                          <input
                            type="text"
                            value={formData.key}
                            onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
                            className="brand-field w-full rounded-xl px-3 py-2 text-sm font-mono"
                            placeholder="my_agent"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={3}
                          className="brand-field w-full rounded-xl px-3 py-2 text-sm"
                          placeholder="Describe what this agent does..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                          Emoji
                        </label>
                        <input
                          type="text"
                          value={formData.emoji}
                          onChange={(e) => setFormData(prev => ({ ...prev, emoji: e.target.value }))}
                          className="brand-field w-20 rounded-xl px-3 py-2 text-lg text-center"
                          maxLength={2}
                        />
                      </div>

                      {/* LLM Configuration */}
                      <div className="border-t border-transparent pt-4">
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-3">
                          LLM Configuration
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                              Provider
                            </label>
                            <select
                              value={formData.llm.provider}
                              onChange={(e) => {
                                const provider = e.target.value;
                                let defaultModel = 'gpt-4o-mini';
                                if (provider === 'gemini') defaultModel = 'gemini-1.5-flash';
                                if (provider === 'claude') defaultModel = 'claude-3-5-sonnet-20241022';

                                setFormData(prev => ({
                                  ...prev,
                                  llm: { provider, model: defaultModel }
                                }));
                              }}
                              className="brand-field w-full rounded-xl px-3 py-2 text-sm"
                            >
                              <option value="openai">OpenAI</option>
                              <option value="gemini">Google Gemini</option>
                              <option value="claude">Anthropic Claude</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                              Model
                            </label>
                            <select
                              value={formData.llm.model}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                llm: { ...prev.llm, model: e.target.value }
                              }))}
                              className="brand-field w-full rounded-xl px-3 py-2 text-sm"
                            >
                              {formData.llm.provider === 'openai' && (
                                <>
                                  <option value="gpt-5">GPT-5 (Latest)</option>
                                  <option value="gpt-4o">GPT-4o</option>
                                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                                  <option value="o1-preview">o1-preview</option>
                                  <option value="o1-mini">o1-mini</option>
                                </>
                              )}
                              {formData.llm.provider === 'gemini' && (
                                <>
                                  <option value="gemini-1.5-flash">Gemini 1.5 Flash (Default)</option>
                                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                                  <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
                                  <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                                </>
                              )}
                              {formData.llm.provider === 'claude' && (
                                <>
                                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                                  <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                                  <option value="claude-3-haiku-20240307">Claude 3 Haiku</option>
                                </>
                              )}
                            </select>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-slate-500 dark:text-slate-300">
                          Choose the LLM provider and model for this agent. Document processing uses GPT-4o by default (configurable globally).
                        </div>
                      </div>
                    </Tab.Panel>

                    {/* Pre-built Tools Tab */}
                    <Tab.Panel className="space-y-4">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Select Pre-built Tools
                      </h3>

                      {loading ? (
                        <div className="flex items-center justify-center py-8 text-slate-500 dark:text-slate-300">
                          <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-sky-500 mr-3" />
                          <span>Loading tools...</span>
                        </div>
                      ) : Object.keys(prebuiltTools).length === 0 ? (
                        <div className="text-center py-8 text-slate-500 dark:text-slate-300">
                          <WrenchIcon className="mx-auto h-12 w-12 text-sky-400" />
                          <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">No tools available</h3>
                          <p className="mt-1 text-sm opacity-80">
                            Create tools first in the Tools Management panel
                          </p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(prebuiltTools).map(([id, tool]) => {
                            const isSelected = selectedTools.find(t => t.id === id)?.enabled || false;
                            return (
                            <div
                              key={id}
                              className={`p-4 rounded-2xl border-2 cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-transparent brand-gradient text-white shadow-lg shadow-sky-500/25'
                                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-500 bg-white/80 dark:bg-slate-900/60'
                              }`}
                              onClick={() => toggleTool(id)}
                            >
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${isSelected ? 'border-white/40 bg-white/20 text-white' : 'border-slate-200/80 bg-white/70 text-slate-500 dark:border-slate-600/70 dark:bg-slate-900/70 dark:text-slate-300'}`}>
                                    {isSelected ? (
                                      <CheckIcon className="w-5 h-5" />
                                    ) : (
                                      <WrenchIcon className="w-5 h-5" />
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1">
                                  <h4 className={`font-semibold ${isSelected ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
                                    {tool.name}
                                  </h4>
                                  <p className={`text-sm mt-1 ${isSelected ? 'text-white/80' : 'text-slate-500 dark:text-slate-300'}`}>
                                    {tool.description}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-2">
                                    <span className={`px-2 py-1 text-xs rounded-lg ${isSelected ? 'bg-white/20 text-white' : 'brand-chip'}`}>
                                      {tool.category || 'uncategorized'}
                                    </span>
                                    <span className={`text-xs ${isSelected ? 'text-white/75' : 'text-slate-400 dark:text-slate-500'}`}>
                                      {tool.functions?.length || 0} functions
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                            );
                          })}
                        </div>
                      )}
                    </Tab.Panel>

                    {/* Pre-built MCP Tab */}
                    <Tab.Panel className="space-y-4">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        Select Pre-built MCP Servers
                      </h3>

                      {loading ? (
                        <div className="flex items-center justify-center py-8 text-slate-500 dark:text-slate-300">
                          <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-sky-500 mr-3" />
                          <span>Loading MCP servers...</span>
                        </div>
                      ) : Object.keys(prebuiltMCPs).length === 0 ? (
                        <div className="text-center py-8 text-slate-500 dark:text-slate-300">
                          <ServerIcon className="mx-auto h-12 w-12 text-sky-400" />
                          <h3 className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">No MCP servers available</h3>
                          <p className="mt-1 text-sm opacity-80">
                            Create MCP servers first in the MCP Management panel
                          </p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {Object.entries(prebuiltMCPs).map(([id, mcp]) => {
                            const isSelected = selectedMCPs.find(m => m.id === id)?.enabled || false;
                            return (
                            <div
                              key={id}
                              className={`p-4 rounded-2xl border-2 cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-transparent brand-gradient text-white shadow-lg shadow-sky-500/25'
                                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-500 bg-white/80 dark:bg-slate-900/60'
                              }`}
                              onClick={() => toggleMCP(id)}
                            >
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl border ${isSelected ? 'border-white/40 bg-white/20 text-white' : 'border-slate-200/80 bg-white/70 text-slate-500 dark:border-slate-600/70 dark:bg-slate-900/70 dark:text-slate-300'}`}>
                                    {isSelected ? (
                                      <CheckIcon className="w-5 h-5" />
                                    ) : (
                                      <ServerIcon className="w-5 h-5" />
                                    )}
                                  </div>
                                </div>
                                <div className="flex-1">
                                  <h4 className={`font-semibold ${isSelected ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
                                    {id}
                                  </h4>
                                  <p className={`text-sm mt-1 ${isSelected ? 'text-white/80' : 'text-slate-500 dark:text-slate-300'}`}>
                                    {mcp.command} {mcp.args?.join(' ')}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-2">
                                    <span className={`px-2 py-1 text-xs rounded-lg ${isSelected ? 'bg-white/20 text-white' : 'brand-chip'}`}>
                                      mcp
                                    </span>
                                    <span className={`text-xs ${isSelected ? 'text-white/75' : 'text-slate-400 dark:text-slate-500'}`}>
                                      {mcp.args?.length || 0} args
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                            );
                          })}
                        </div>
                      )}
                    </Tab.Panel>

                    {/* Custom Code Tab */}
                    <Tab.Panel className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                          Custom Tools Code (Python)
                        </label>
                        <textarea
                          value={customToolsCode}
                          onChange={(e) => setCustomToolsCode(e.target.value)}
                          rows={8}
                          className="brand-field w-full rounded-xl px-3 py-2 font-mono text-sm"
                          placeholder="# Add your custom tools here..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
                          Custom MCP Configuration (JSON)
                        </label>
                        <textarea
                          value={customMCPConfig}
                          onChange={(e) => setCustomMCPConfig(e.target.value)}
                          rows={8}
                          className="brand-field w-full rounded-xl px-3 py-2 font-mono text-sm"
                          placeholder='{\n  "my_custom_server": {\n    "command": "python",\n    "args": ["server.py"]\n  }\n}'
                        />
                      </div>
                    </Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-transparent">
                  <BrandedButton
                    onClick={() => {
                      resetForm();
                      onClose();
                    }}
                    variant="ghost"
                  >
                    Cancel
                  </BrandedButton>
                  <BrandedButton
                    onClick={isEditing ? handleUpdateAgent : handleCreateAgent}
                    variant="primary"
                    loading={loading}
                    disabled={loading || !formData.name.trim()}
                  >
                    {loading ? 'Saving...' : (isEditing ? 'Update Agent' : 'Create Agent')}
                  </BrandedButton>
                </div>
              </div>
            </div>
          </SlidingPanel>

      {/* Progress Bar */}
      <ProgressBar
        currentStep={progressSteps.currentStep}
        steps={agentSteps}
        isVisible={progressSteps.isVisible}
      />
    </>
  );
};
