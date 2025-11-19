import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ServerIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';
import { mcpApi } from "@/lib/api";
import { ProgressBar, useProgressSteps } from '../shared/ProgressBar';
import { BrandedButton, BrandedCard } from '../shared/BrandedComponents';
import { BrandLogo } from '../shared/BrandLogo';
import { SlidingPanel } from '../core/SlidingPanel';

// Backend MCP structure (matches backend exactly)
interface BackendMcpServer {
  command: string;
  args: string[];
  env?: Record<string, string>;
}


interface McpManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const McpManagementPanel: React.FC<McpManagementPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const [mcpServers, setMcpServers] = useState<Record<string, BackendMcpServer>>({});
  const [loading, setLoading] = useState(true);
  const [selectedMcp, setSelectedMcp] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [rawJsonConfig, setRawJsonConfig] = useState('');

  // Form state for basic info
  const [formData, setFormData] = useState({
    mcpId: '',
    name: '',
    description: '',
    category: '',
  });

  // Progress bar for creation/editing
  const mcpSteps = ['Verifying Configuration', 'Validating Connectivity', 'Deploying MCP Server'];
  const progressSteps = useProgressSteps(mcpSteps);

  const labelClass = 'block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2';
  const inputClass = 'brand-field w-full rounded-xl px-3 py-2 text-sm';

  useEffect(() => {
    if (isOpen) {
      loadMcpServers();
    }
  }, [isOpen]);

  const loadMcpServers = async () => {
    try {
      setLoading(true);
      const response = await mcpApi.getMcpServers();
      setMcpServers(response.mcpServers || {});
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
      toast.error('Failed to load MCP servers');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      mcpId: '',
      name: '',
      description: '',
      category: '',
    });
    setSelectedMcp(null);
    setIsEditing(false);
    setIsCreating(false);
    setRawJsonConfig('');
  };

  const handleCreateNew = () => {
    resetForm();
    setRawJsonConfig('{\n  "command": "",\n  "args": []\n}');
    setIsCreating(true);
  };

  const handleEditMcp = (mcpId: string) => {
    const mcp = mcpServers[mcpId];
    if (mcp) {
      setFormData({
        mcpId,
        name: mcpId,
        description: 'MCP Server Configuration',
        category: 'mcp',
      });
      setRawJsonConfig(JSON.stringify(mcp, null, 2));
      setSelectedMcp(mcpId);
      setIsEditing(true);
      setIsCreating(false);
    }
  };

  const handleSaveMcp = async () => {
    try {
      if (!formData.name.trim() || !formData.description.trim()) {
        toast.error('Please fill in all required fields');
        return;
      }

      progressSteps.startProgress();

      // Step 1: Verifying Configuration
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Parse raw JSON configuration
      let configData;
      try {
        if (!rawJsonConfig || !rawJsonConfig.trim()) {
          toast.error('Please provide a JSON configuration');
          progressSteps.hideProgress();
          return;
        }

        configData = JSON.parse(rawJsonConfig);

        // Basic validation - at minimum should have command
        if (typeof configData !== 'object' || configData === null) {
          throw new Error('Configuration must be a valid JSON object');
        }
        if (!configData.command) {
          throw new Error('Configuration must include a "command" field');
        }
      } catch (parseError) {
        toast.error('Invalid JSON configuration. Please check your syntax.');
        progressSteps.hideProgress();
        return;
      }

      // Use the new simplified format - send the config directly
      const mcpData = configData;
      const mcpId = formData.mcpId || formData.name.toLowerCase().replace(/[^a-z0-9]/g, '_');

      // Check if OAuth might be required (informational only)
      try {
        const oauthCheck = await mcpApi.checkOAuthRequirement(mcpId, mcpData);

        if (oauthCheck.requires_oauth && !oauthCheck.has_token) {
          // Show info that OAuth will be handled later
          toast('Remote MCP server - OAuth will be requested when tools are used', {
            duration: 3000,
            icon: 'ℹ️'
          });
        }

        progressSteps.nextStep();
      } catch (error) {
        // OAuth check is non-critical, continue anyway
        progressSteps.nextStep();
      }

      // Step 2/3: Validating Connectivity
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Step 3: Deploying MCP Server
      await new Promise(resolve => setTimeout(resolve, 500));

      if (isCreating) {
        await mcpApi.createMcpServer(mcpId, mcpData);
        progressSteps.completeProgress();
        toast.success(`MCP server "${mcpId}" created successfully`);
      } else if (selectedMcp) {
        await mcpApi.updateMcpServer(selectedMcp, mcpData);
        progressSteps.completeProgress();
        toast.success(`MCP server "${selectedMcp}" updated successfully`);
      }

      await loadMcpServers();
      resetForm();
    } catch (error: any) {
      progressSteps.hideProgress();

      // Show specific error message
      if (error?.validation_errors) {
        const validationData = error.validation_errors;
        if (validationData?.errors?.length > 0) {
          const errorMessage = validationData.errors.map((err: any) => `${err.field}: ${err.message}`).join(', ');
          toast.error(`Validation failed: ${errorMessage}`);
        } else {
          toast.error('MCP configuration validation failed');
        }
      } else if (error?.message) {
        toast.error(`Failed to save MCP server: ${error.message}`);
      } else {
        toast.error('Failed to save MCP server');
      }
    }
  };

  const handleDeleteMcp = async (mcpId: string) => {
    if (!window.confirm(`Are you sure you want to delete "${mcpId}"?`)) {
      return;
    }

    try {
      await mcpApi.deleteMcpServer(mcpId);
      toast.success('MCP server deleted successfully');
      await loadMcpServers();
      if (selectedMcp === mcpId) {
        resetForm();
      }
    } catch (error) {
      console.error('Failed to delete MCP server:', error);
      toast.error('Failed to delete MCP server');
    }
  };
  const headerActions = (
    <>
      <button
        onClick={loadMcpServers}
        disabled={loading}
        className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 disabled:opacity-50 transition-colors"
        title="Refresh MCP servers"
      >
        <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
      </button>
      <BrandedButton
        variant="primary"
        size="sm"
        onClick={handleCreateNew}
        className="flex items-center space-x-2"
      >
        <PlusIcon className="h-4 w-4" />
        <span>New MCP Server</span>
      </BrandedButton>
    </>
  );

  return (
    <SlidingPanel
      isOpen={isOpen}
      onClose={onClose}
      title="MCP Servers Management"
      subtitle="Configure and monitor Model Context Protocol servers"
      icon={<ServerIcon className="h-6 w-6 text-sky-500" />}
      actions={headerActions}
      size="xlarge"
      headerClassName="border-b border-transparent"
      headerBackgroundClassName={null}
      containerClassName="brand-surface-strong rounded-3xl border border-transparent shadow-2xl"
      contentClassName="flex flex-1 min-h-0"
    >
      <div className="flex-1 flex min-h-0">
        <Tab.Group vertical>
          <div className="flex w-full h-full">
            {/* MCP Servers List */}
            <div className="w-1/3 border-r border-transparent flex flex-col brand-shell">
              <div className="p-4 border-b border-transparent">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  MCP Servers ({Object.keys(mcpServers).length})
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="p-6 text-center">
                    <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-sky-500 mb-2" />
                    <p className="text-slate-600 dark:text-slate-400">Loading MCP servers...</p>
                  </div>
                ) : Object.keys(mcpServers).length === 0 ? (
                  <BrandedCard variant="glass" className="p-6 text-center m-4">
                    <div className="flex justify-center mb-4">
                      <BrandLogo variant="icon" size="md" />
                    </div>
                    <p className="text-slate-600 dark:text-slate-400 font-medium mb-4">No MCP servers configured yet</p>
                    <BrandedButton
                      onClick={handleCreateNew}
                      variant="primary"
                      size="sm"
                    >
                      Create your first MCP server
                    </BrandedButton>
                  </BrandedCard>
                ) : (
                  <div className="space-y-2 p-4">
                    {Object.entries(mcpServers).filter(([mcpId, mcp]) => mcpId && mcp).map(([mcpId, mcp]) => (
                      <div
                        key={`mcp-${mcpId}`}
                        className={`p-3 rounded-2xl border cursor-pointer transition-all ${
                          selectedMcp === mcpId
                            ? 'border-transparent brand-gradient text-white shadow-lg shadow-sky-500/25'
                            : 'border-transparent hover:bg-white/60 dark:hover:bg-slate-800/60'
                        }`}
                        onClick={() => setSelectedMcp(mcpId)}
                      >
                      <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className={`text-sm font-medium truncate ${selectedMcp === mcpId ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
                              {mcpId}
                            </h4>
                            <p className={`text-xs mt-1 line-clamp-2 ${selectedMcp === mcpId ? 'text-white/80' : 'text-slate-600 dark:text-slate-400'}`}>
                              {mcp.command} {mcp.args?.join(' ')}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <span className={`text-xs ${selectedMcp === mcpId ? 'text-white/75' : 'text-slate-500 dark:text-slate-400'}`}>
                                {mcp.args?.length || 0} args • {mcp.command}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1 ml-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditMcp(mcpId);
                              }}
                              className="p-1 text-slate-400 hover:text-sky-500"
                              title="Edit MCP server"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteMcp(mcpId);
                              }}
                              className="p-1 text-slate-400 hover:text-red-600"
                              title="Delete MCP server"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* MCP Editor */}
            <div className="flex-1 flex flex-col">
              {(isEditing || isCreating) ? (
                <div className="flex-1 flex flex-col">
                  {/* Editor Header */}
                  <div className="p-4 border-b border-transparent">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        {isCreating ? 'Create New MCP Server' : 'Edit MCP Server'}
                      </h3>
                      <div className="flex items-center space-x-2">
                        <BrandedButton variant="ghost" size="sm" onClick={resetForm}>
                          Cancel
                        </BrandedButton>
                        <BrandedButton
                          onClick={handleSaveMcp}
                          variant="primary"
                          size="sm"
                          loading={loading}
                        >
                          {isCreating ? 'Create Server' : 'Save Changes'}
                        </BrandedButton>
                      </div>
                    </div>
                  </div>

                  {/* Form */}
                  <div className="flex-1 flex flex-col min-h-0">
                    <div className="flex-1 overflow-y-auto p-4 space-y-6">
                      {/* Basic Information */}
                      <div>
                        <h4 className="font-medium text-slate-900 dark:text-white mb-4">Basic Information</h4>
                        <div className="space-y-4">
                          <div>
                            <label className={labelClass}>
                              Server Name *
                            </label>
                            <input
                              type="text"
                              value={formData.name}
                              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                              className={`${inputClass} focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
                              placeholder="Enter server name"
                            />
                          </div>
                          <div>
                            <label className={labelClass}>
                              Description *
                            </label>
                            <textarea
                              value={formData.description}
                              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                              rows={3}
                              className={`${inputClass} focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none`}
                              placeholder="Describe what this MCP server provides"
                            />
                          </div>
                        </div>
                      </div>

                      {/* MCP Configuration - Free JSON */}
                      <div>
                        <h4 className="font-medium text-slate-900 dark:text-white mb-4">MCP Configuration (JSON)</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                          Write any valid JSON configuration for your MCP server. You have complete flexibility to define the structure.
                        </p>
                        <textarea
                          value={rawJsonConfig}
                          onChange={(e) => setRawJsonConfig(e.target.value)}
                          rows={12}
                          className={`${inputClass} font-mono text-sm min-h-[260px] resize-none overflow-y-auto focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
                          placeholder="Write any JSON configuration here..."
                        />
                      </div>
                    </div>

                    {/* JSON Validation Indicator - Fixed at bottom */}
                    <div className="p-4 border-t border-transparent">
                      {(() => {
                        try {
                          if (rawJsonConfig && rawJsonConfig.trim()) {
                            JSON.parse(rawJsonConfig);
                            return (
                              <div className="flex items-center text-green-600 dark:text-green-400">
                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                <span className="text-sm">Valid JSON</span>
                              </div>
                            );
                          }
                          return <div className="text-sm text-slate-400">Enter JSON configuration above</div>;
                        } catch (error) {
                          return rawJsonConfig && rawJsonConfig.trim() ? (
                            <div className="flex items-center text-red-600 dark:text-red-400">
                              <XCircleIcon className="h-4 w-4 mr-1" />
                              <span className="text-sm">Invalid JSON syntax</span>
                            </div>
                          ) : <div className="text-sm text-slate-400">Enter JSON configuration above</div>;
                        }
                      })()}
                    </div>
                  </div>
                </div>
              ) : selectedMcp && mcpServers[selectedMcp] ? (
                <div className="flex-1 flex flex-col">
                  {/* MCP Details Header */}
                  <div className="p-4 border-b border-transparent">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                          {selectedMcp}
                        </h3>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">
                          MCP Server Configuration
                        </p>
                      </div>
                      <button
                        onClick={() => handleEditMcp(selectedMcp)}
                        className="flex items-center space-x-2 brand-cta px-4 py-2 rounded-xl"
                      >
                        <PencilIcon className="h-4 w-4" />
                        <span>Edit Server</span>
                      </button>
                    </div>
                  </div>

                  {/* MCP Details */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {/* Basic Info */}
                    <div>
                      <h4 className="font-medium text-slate-900 dark:text-white mb-3">Server Information</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-slate-600 dark:text-slate-400">Command</span>
                          <p className="mt-1 font-mono text-sm brand-field px-2 py-1 rounded">
                            {mcpServers[selectedMcp].command}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Arguments */}
                    {mcpServers[selectedMcp].args && mcpServers[selectedMcp].args.length > 0 && (
                      <div>
                        <h4 className="font-medium text-slate-900 dark:text-white mb-3">Arguments</h4>
                        <div className="flex flex-wrap gap-2">
                          {mcpServers[selectedMcp].args.filter(arg => arg && arg.trim()).map((arg, index) => (
                            <span
                              key={`arg-${arg}-${index}`}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-sky-100 dark:bg-sky-900/20 text-sky-700 dark:text-sky-400"
                            >
                              {arg}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Environment Variables */}
                    {mcpServers[selectedMcp].env && Object.keys(mcpServers[selectedMcp].env!).length > 0 && (
                      <div>
                        <h4 className="font-medium text-slate-900 dark:text-white mb-3">Environment Variables</h4>
                        <div className="space-y-2">
                          {Object.entries(mcpServers[selectedMcp].env!).map(([key, value], index) => (
                            <div
                              key={`${key}-${index}`}
                              className="flex items-center p-2 brand-field rounded-lg"
                            >
                              <span className="font-mono text-sm text-slate-900 dark:text-white">{key}</span>
                              <span className="mx-2 text-slate-400">=</span>
                              <span className="font-mono text-sm text-slate-600 dark:text-slate-400">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Note: Capabilities removed from new simplified format */}
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <ServerIcon className="h-16 w-16 mx-auto text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      Select an MCP server to view details
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                      Choose an MCP server from the list or create a new one
                    </p>
                    <button
                      onClick={handleCreateNew}
                      className="flex items-center space-x-2 brand-cta px-4 py-2 rounded-xl mx-auto"
                    >
                      <PlusIcon className="h-4 w-4" />
                      <span>Create New MCP Server</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Tab.Group>
      </div>

      <ProgressBar
        currentStep={progressSteps.currentStep}
        steps={mcpSteps}
        isVisible={progressSteps.isVisible}
      />
    </SlidingPanel>
  );
};
