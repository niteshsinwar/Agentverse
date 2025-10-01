import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckIcon,
  WrenchIcon,
  ServerIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';
import { toast } from 'react-hot-toast';
import { apiService } from '@/shared/api';
import { ProgressBar, useProgressSteps } from './ProgressBar';
import { BrandedButton, BrandedCard, BrandedBadge, BrandedAlert } from './BrandedComponents';
import { BrandLogo } from './BrandLogo';

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
  config?: any;
}

interface EnhancedAgentCreationPanelProps {
  selectedAgent?: Agent;
  onAgentCreated?: () => void;
  onAgentUpdated?: () => void;
  onClose?: () => void;
}

export const EnhancedAgentCreationPanel: React.FC<EnhancedAgentCreationPanelProps> = ({
  selectedAgent,
  onAgentCreated,
  onAgentUpdated,
  onClose: _onClose
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(false);

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
    loadAgents();
    loadConfigurations();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      // Use the same logic as startEditing to ensure we get complete data
      startEditing(selectedAgent);
    }
  }, [selectedAgent]);

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

  const loadAgents = async () => {
    try {
      setLoading(true);
      const agentsData = await apiService.getAvailableAgents();
      setAgents(Array.isArray(agentsData) ? agentsData : []);
    } catch (error) {
      console.error('Failed to load agents:', error);
      toast.error('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const loadAgentConfiguration = async (agent: Agent) => {
    try {
      // Note: The /agents/{key}/config endpoint was removed as unused
      // Agent configuration is now managed through the simplified agent.yaml
      // which only contains: name, description, emoji, llm (provider, model)
      console.log('Agent configuration loaded from simplified YAML structure:', agent);
    } catch (error) {
      console.warn('Could not load agent configuration:', error);
    }
  };

  const updateSelectionsFromConfig = (config: any) => {
    // Update tool selections
    if (config.tools) {
      setSelectedTools(prev => prev.map(tool => ({
        ...tool,
        enabled: config.tools.includes(tool.id)
      })));
    }

    // Update MCP selections
    const mcpServers = config.mcp_config?.mcpServers || config.mcp_servers || {};
    if (mcpServers && typeof mcpServers === 'object') {
      setSelectedMCPs(prev => prev.map(mcp => ({
        ...mcp,
        enabled: Object.keys(mcpServers).includes(mcp.id),
        config: mcpServers[mcp.id] || {}
      })));
    }

    // Load custom code
    if (config.custom_tools) {
      setCustomToolsCode(config.custom_tools);
    }
    if (config.custom_mcp) {
      setCustomMCPConfig(JSON.stringify(config.custom_mcp, null, 2));
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
      setShowCreateForm(false);
      loadAgents();
      onAgentCreated?.();

    } catch (error) {
      console.error('Failed to create agent:', error);
      progressSteps.hideProgress();
      toast.error('Failed to create agent');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAgent = async () => {
    if (!editingAgent) return;

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
      await apiService.updateAgent(editingAgent.key, agentData);

      progressSteps.completeProgress();
      toast.success(`Agent "${formData.name}" updated successfully!`);
      setIsEditing(false);
      setEditingAgent(null);
      loadAgents();
      onAgentUpdated?.();

    } catch (error: any) {
      console.error('Failed to update agent:', error);
      progressSteps.hideProgress();

      // Show specific error message
      if (error.validation_errors) {
        toast.error(`Validation failed: ${JSON.stringify(error.validation_errors)}`);
      } else if (error.message) {
        toast.error(`Failed to update agent: ${error.message}`);
      } else {
        toast.error('Failed to update agent');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agentKey: string) => {
    if (!confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      await apiService.deleteAgent(agentKey);
      toast.success('Agent deleted successfully');
      loadAgents();
    } catch (error: any) {
      console.error('Failed to delete agent:', error);

      // Show specific error message
      if (error.message?.includes('Cannot delete the TEMPLATE agent')) {
        toast.error('Cannot delete the TEMPLATE agent - it is required for the system');
      } else if (error.validation_errors) {
        toast.error(`Validation failed: ${JSON.stringify(error.validation_errors)}`);
      } else if (error.message) {
        toast.error(`Failed to delete agent: ${error.message}`);
      } else {
        toast.error('Failed to delete agent');
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

  const startEditing = async (agent: Agent) => {
    try {
      // Fetch the complete agent data to ensure we have tools_code and mcp_config
      const completeAgentData = await apiService.getAvailableAgents() as Agent[];
      const fullAgent = completeAgentData.find((a: Agent) => a.key === agent.key) || agent;

      setEditingAgent(fullAgent);
      setFormData({
        name: fullAgent.name,
        description: fullAgent.description,
        emoji: fullAgent.emoji,
        key: fullAgent.key,
        llm: fullAgent.llm || { provider: 'openai', model: 'gpt-4o-mini' }
      });

      // Load custom code directly from the complete agent data (legacy support)
      // Note: tools_code and mcp_config are no longer part of simplified schema
      // but may exist in legacy agent data
      try {
        const legacyAgent = fullAgent as any;
        if (legacyAgent.tools_code) {
          setCustomToolsCode(legacyAgent.tools_code);
          setSelectedTabIndex(3); // Switch to Custom Code tab
        }
        if (legacyAgent.mcp_config) {
          setCustomMCPConfig(typeof legacyAgent.mcp_config === 'string'
            ? legacyAgent.mcp_config
            : JSON.stringify(legacyAgent.mcp_config, null, 2)
          );
          if (!legacyAgent.tools_code) {
            setSelectedTabIndex(3); // Switch to Custom Code tab
          }
        }
      } catch (e) {
        // Ignore legacy field access errors
      }

      setIsEditing(true);
      loadAgentConfiguration(fullAgent);
    } catch (error) {
      console.error('Failed to load complete agent data:', error);
      // Fallback to the original agent data
      setEditingAgent(agent);
      setFormData({
        name: agent.name,
        description: agent.description,
        emoji: agent.emoji,
        key: agent.key,
        llm: agent.llm || { provider: 'openai', model: 'gpt-4o-mini' }
      });
      setIsEditing(true);
      loadAgentConfiguration(agent);
    }
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
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20">
      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        {showCreateForm || isEditing ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-4xl mx-auto"
          >
            <BrandedCard variant="glass" className="overflow-hidden">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-6">
                  <BrandLogo variant="icon" size="sm" />
                  <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                    {isEditing ? 'Edit Agent' : 'Create New Agent'}
                  </h2>
                </div>

                <Tab.Group selectedIndex={selectedTabIndex} onChange={setSelectedTabIndex}>
                  <Tab.List className="flex space-x-1 rounded-xl bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 border border-violet-200/30 dark:border-violet-700/30 p-1 mb-6">
                    {['Basic Info', 'Pre-built Tools', 'Pre-built MCP', 'Custom Code'].map((tab) => (
                      <Tab
                        key={tab}
                        className={({ selected }) =>
                          `w-full rounded-lg py-2.5 text-sm font-semibold leading-5 text-center transition-all duration-200 ${
                            selected
                              ? 'bg-gradient-to-r from-violet-500 to-indigo-600 text-white shadow-lg shadow-violet-500/25'
                              : 'text-slate-600 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 hover:bg-violet-100/50 dark:hover:bg-violet-900/20'
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
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Agent Name
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="My Agent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Agent Key
                          </label>
                          <input
                            type="text"
                            value={formData.key}
                            onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
                            placeholder="my_agent"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="Describe what this agent does..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Emoji
                        </label>
                        <input
                          type="text"
                          value={formData.emoji}
                          onChange={(e) => setFormData(prev => ({ ...prev, emoji: e.target.value }))}
                          className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center text-lg"
                          maxLength={2}
                        />
                      </div>

                      {/* LLM Configuration */}
                      <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                          LLM Configuration
                        </h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            >
                              <option value="openai">OpenAI</option>
                              <option value="gemini">Google Gemini</option>
                              <option value="claude">Anthropic Claude</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Model
                            </label>
                            <select
                              value={formData.llm.model}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                llm: { ...prev.llm, model: e.target.value }
                              }))}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          Choose the LLM provider and model for this agent. Document processing uses GPT-4o by default (configurable globally).
                        </div>
                      </div>
                    </Tab.Panel>

                    {/* Pre-built Tools Tab */}
                    <Tab.Panel className="space-y-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Select Pre-built Tools
                      </h3>

                      {loading ? (
                        <div className="flex items-center justify-center py-8">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading tools...</span>
                        </div>
                      ) : Object.keys(prebuiltTools).length === 0 ? (
                        <div className="text-center py-8">
                          <WrenchIcon className="mx-auto h-12 w-12 text-gray-400" />
                          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No tools available</h3>
                          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
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
                              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                              }`}
                              onClick={() => toggleTool(id)}
                            >
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                  {isSelected ? (
                                    <CheckIcon className="w-5 h-5 text-blue-600" />
                                  ) : (
                                    <WrenchIcon className="w-5 h-5 text-gray-400" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-medium text-gray-900 dark:text-white">
                                    {tool.name}
                                  </h4>
                                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {tool.description}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-2">
                                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded">
                                      {tool.category || 'uncategorized'}
                                    </span>
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
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
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Select Pre-built MCP Servers
                      </h3>

                      {loading ? (
                        <div className="flex items-center justify-center py-8">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading MCP servers...</span>
                        </div>
                      ) : Object.keys(prebuiltMCPs).length === 0 ? (
                        <div className="text-center py-8">
                          <ServerIcon className="mx-auto h-12 w-12 text-gray-400" />
                          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No MCP servers available</h3>
                          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
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
                              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                                isSelected
                                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                              }`}
                              onClick={() => toggleMCP(id)}
                            >
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0">
                                  {isSelected ? (
                                    <CheckIcon className="w-5 h-5 text-purple-600" />
                                  ) : (
                                    <ServerIcon className="w-5 h-5 text-gray-400" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-medium text-gray-900 dark:text-white">
                                    {id}
                                  </h4>
                                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                    {mcp.command} {mcp.args?.join(' ')}
                                  </p>
                                  <div className="flex items-center space-x-2 mt-2">
                                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded">
                                      mcp
                                    </span>
                                    <span className="text-xs text-gray-500 dark:text-gray-400">
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
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Custom Tools Code (Python)
                        </label>
                        <textarea
                          value={customToolsCode}
                          onChange={(e) => setCustomToolsCode(e.target.value)}
                          rows={8}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                          placeholder="# Add your custom tools here..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Custom MCP Configuration (JSON)
                        </label>
                        <textarea
                          value={customMCPConfig}
                          onChange={(e) => setCustomMCPConfig(e.target.value)}
                          rows={8}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                          placeholder='{\n  "my_custom_server": {\n    "command": "python",\n    "args": ["server.py"]\n  }\n}'
                        />
                      </div>
                    </Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <BrandedButton
                    onClick={() => {
                      setShowCreateForm(false);
                      setIsEditing(false);
                      setEditingAgent(null);
                      resetForm();
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
            </BrandedCard>
          </motion.div>
        ) : (
          /* Agent List */
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                Existing Agents ({agents.length})
              </h2>
              <BrandedButton
                variant="primary"
                onClick={() => {
                  resetForm();
                  setShowCreateForm(true);
                }}
                className="flex items-center space-x-2"
              >
                <PlusIcon className="w-5 h-5" />
                <span>Create Agent</span>
              </BrandedButton>
            </div>

            {loading ? (
              <BrandedCard variant="glass" className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-violet-500 border-r-indigo-600 mx-auto"></div>
                <p className="text-slate-600 dark:text-slate-400 font-medium mt-3">Loading agents...</p>
              </BrandedCard>
            ) : agents.length === 0 ? (
              <BrandedCard variant="glass" className="text-center py-12">
                <div className="flex justify-center mb-6">
                  <BrandLogo variant="icon" size="lg" />
                </div>
                <h3 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent mb-2">
                  No agents yet
                </h3>
                <p className="text-slate-500 dark:text-slate-400 font-medium mb-6">
                  Get started by creating your first AI agent in the AgentVerse.
                </p>
                <BrandedButton
                  variant="primary"
                  onClick={() => {
                    resetForm();
                    setShowCreateForm(true);
                  }}
                  className="flex items-center space-x-2 mx-auto"
                >
                  <PlusIcon className="w-5 h-5" />
                  <span>Create Your First Agent</span>
                </BrandedButton>
              </BrandedCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.map((agent) => (
                  <motion.div
                    key={agent.key}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{agent.emoji}</span>
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">
                            {agent.name}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {agent.key}
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <button
                          onClick={() => startEditing(agent)}
                          className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteAgent(agent.key)}
                          disabled={agent.key === 'TEMPLATE'}
                          className={`p-2 transition-colors ${
                            agent.key === 'TEMPLATE'
                              ? 'text-gray-300 cursor-not-allowed'
                              : 'text-gray-400 hover:text-red-600'
                          }`}
                          title={agent.key === 'TEMPLATE' ? 'Cannot delete TEMPLATE agent' : 'Delete agent'}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                      {agent.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                      <span>Agent • Ready</span>
                      <button
                        onClick={() => startEditing(agent)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Edit
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <ProgressBar
        currentStep={progressSteps.currentStep}
        steps={agentSteps}
        isVisible={progressSteps.isVisible}
      />
    </div>
  );
};