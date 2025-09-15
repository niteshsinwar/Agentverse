import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
import { apiService } from '../services/api';
import { ProgressBar, useProgressSteps } from './ProgressBar';

interface McpServer {
  command: string;
  args: string[];
  env?: Record<string, string>;
}

interface McpData {
  mcpServers: Record<string, McpServer>;
}

interface McpManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const McpManagementPanel: React.FC<McpManagementPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const [mcpServers, setMcpServers] = useState<Record<string, McpServer>>({});
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


  useEffect(() => {
    if (isOpen) {
      loadMcpServers();
    }
  }, [isOpen]);

  const loadMcpServers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getMcpServers() as McpData;
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
        name: mcpId, // Use the key as the name
        description: 'MCP Server Configuration',
        category: 'mcp',
      });
      setRawJsonConfig(JSON.stringify(mcp, null, 2)); // The entire mcp object is the config
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

      // Step 2: Validating Connectivity
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Step 3: Deploying MCP Server
      await new Promise(resolve => setTimeout(resolve, 500));

      if (isCreating) {
        const mcpId = formData.mcpId || formData.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
        await apiService.addMcpServer(mcpId, mcpData);
        progressSteps.completeProgress();
        toast.success(`MCP server "${mcpId}" created successfully`);
      } else if (selectedMcp) {
        await apiService.updateMcpServer(selectedMcp, mcpData);
        progressSteps.completeProgress();
        toast.success(`MCP server "${selectedMcp}" updated successfully`);
      }

      await loadMcpServers();
      resetForm();
    } catch (error: any) {
      console.error('Failed to save MCP server:', error);
      progressSteps.hideProgress();

      // Handle validation errors from backend
      if (error?.validation_errors) {
        toast.error(`Validation failed: ${JSON.stringify(error.validation_errors)}`);
      } else if (error?.message?.includes('validation failed') || error?.response?.data?.validation_errors) {
        const validationData = error.response?.data?.validation_errors || error.validation_errors;
        if (validationData?.errors?.length > 0) {
          const errorMessage = validationData.errors.map((err: any) => `${err.field}: ${err.message}`).join(', ');
          toast.error(`Validation failed: ${errorMessage}`);
        } else {
          toast.error('Configuration validation failed. Please check your inputs.');
        }
      } else if (error.message) {
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
      await apiService.deleteMcpServer(mcpId);
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


  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="mcp-modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        onClick={onClose}
      >
        <motion.div
          key="mcp-modal-content"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-7xl h-5/6 max-h-[90vh] flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <ServerIcon className="h-6 w-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                MCP Servers Management
              </h2>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadMcpServers}
                disabled={loading}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                title="Refresh MCP servers"
              >
                <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={handleCreateNew}
                className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                <span>New MCP Server</span>
              </button>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="flex-1 flex min-h-0">
            {/* MCP Servers List */}
            <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 flex flex-col">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  MCP Servers ({Object.keys(mcpServers).length})
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="p-6 text-center">
                    <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-purple-600 mb-2" />
                    <p className="text-gray-600 dark:text-gray-400">Loading MCP servers...</p>
                  </div>
                ) : Object.keys(mcpServers).length === 0 ? (
                  <div className="p-6 text-center">
                    <ServerIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">No MCP servers configured</p>
                    <button
                      onClick={handleCreateNew}
                      className="mt-2 text-purple-600 hover:text-purple-700"
                    >
                      Create your first MCP server
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2 p-4">
                    {Object.entries(mcpServers).filter(([mcpId, mcp]) => mcpId && mcp).map(([mcpId, mcp]) => (
                      <div
                        key={`mcp-${mcpId}`}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedMcp === mcpId
                            ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                        onClick={() => setSelectedMcp(mcpId)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {mcpId}
                            </h4>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                              {mcp.command} {mcp.args?.join(' ')}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
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
                              className="p-1 text-gray-400 hover:text-purple-600"
                              title="Edit MCP server"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteMcp(mcpId);
                              }}
                              className="p-1 text-gray-400 hover:text-red-600"
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
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {isCreating ? 'Create New MCP Server' : 'Edit MCP Server'}
                      </h3>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={resetForm}
                          className="px-3 py-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveMcp}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
                        >
                          {isCreating ? 'Create Server' : 'Save Changes'}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Form */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-6 min-h-0">
                    {/* Basic Information */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-4">Basic Information</h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Server Name *
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Enter server name"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Description *
                          </label>
                          <textarea
                            value={formData.description}
                            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Describe what this MCP server provides"
                          />
                        </div>
                      </div>
                    </div>

                    {/* MCP Configuration - Free JSON */}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white mb-4">MCP Configuration (JSON)</h4>
                      <div className="mb-3">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          Write any valid JSON configuration for your MCP server. You have complete flexibility to define the structure.
                        </p>
                        <details className="text-xs text-gray-500 dark:text-gray-500 bg-gray-50 dark:bg-gray-800 p-2 rounded border">
                          <summary className="cursor-pointer font-medium">Show Examples</summary>
                          <div className="mt-2 space-y-2">
                            <div>
                              <p className="font-medium mb-1">Simple MCP:</p>
                              <pre className="whitespace-pre-wrap">{`{
  "command": "npx",
  "args": ["@playwright/mcp@latest"]
}`}</pre>
                            </div>
                            <div>
                              <p className="font-medium mb-1">Complex MCP:</p>
                              <pre className="whitespace-pre-wrap">{`{
  "command": "/bin/bash",
  "args": [
    "-lc",
    "cd '/path/to/project' && source venv/bin/activate && python -m app.main --mcp-stdio"
  ],
  "env": {
    "API_KEY": "your-key",
    "DEBUG": "true"
  },
  "capabilities": ["read", "write"],
  "timeout": 30000
}`}</pre>
                            </div>
                          </div>
                        </details>
                      </div>
                      <textarea
                        value={rawJsonConfig}
                        onChange={(e) => setRawJsonConfig(e.target.value)}
                        rows={12}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm resize-none"
                        placeholder="Write any JSON configuration here..."
                      />
                      {(() => {
                        try {
                          if (rawJsonConfig && rawJsonConfig.trim()) {
                            JSON.parse(rawJsonConfig);
                            return (
                              <div className="mt-2 flex items-center text-green-600 dark:text-green-400">
                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                <span className="text-sm">Valid JSON</span>
                              </div>
                            );
                          }
                          return null;
                        } catch (error) {
                          return rawJsonConfig && rawJsonConfig.trim() ? (
                            <div className="mt-2 flex items-center text-red-600 dark:text-red-400">
                              <XCircleIcon className="h-4 w-4 mr-1" />
                              <span className="text-sm">Invalid JSON syntax</span>
                            </div>
                          ) : null;
                        }
                      })()}
                    </div>
                  </div>
                </div>
              ) : selectedMcp && mcpServers[selectedMcp] ? (
                <div className="flex-1 flex flex-col">
                  {/* MCP Details Header */}
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {selectedMcp}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400 mt-1">
                          MCP Server Configuration
                        </p>
                      </div>
                      <button
                        onClick={() => handleEditMcp(selectedMcp)}
                        className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
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
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3">Server Information</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-gray-600 dark:text-gray-400">Command</span>
                          <p className="mt-1 font-mono text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                            {mcpServers[selectedMcp].command}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Arguments */}
                    {mcpServers[selectedMcp].args && mcpServers[selectedMcp].args.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Arguments</h4>
                        <div className="flex flex-wrap gap-2">
                          {mcpServers[selectedMcp].args.filter(arg => arg && arg.trim()).map((arg, index) => (
                            <span
                              key={`arg-${arg}-${index}`}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
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
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Environment Variables</h4>
                        <div className="space-y-2">
                          {Object.entries(mcpServers[selectedMcp].env!).map(([key, value], index) => (
                            <div
                              key={`${key}-${index}`}
                              className="flex items-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                            >
                              <span className="font-mono text-sm text-gray-900 dark:text-white">{key}</span>
                              <span className="mx-2 text-gray-400">=</span>
                              <span className="font-mono text-sm text-gray-600 dark:text-gray-400">{value}</span>
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
                    <ServerIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Select an MCP server to view details
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Choose an MCP server from the list or create a new one
                    </p>
                    <button
                      onClick={handleCreateNew}
                      className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg mx-auto"
                    >
                      <PlusIcon className="h-4 w-4" />
                      <span>Create New MCP Server</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Progress Bar */}
      <ProgressBar
        currentStep={progressSteps.currentStep}
        steps={mcpSteps}
        isVisible={progressSteps.isVisible}
      />
    </AnimatePresence>
  );
};