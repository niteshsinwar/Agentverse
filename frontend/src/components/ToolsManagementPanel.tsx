import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  TrashIcon,
  PencilIcon,
  CodeBracketIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { toolsApi } from "@/shared/api";
import { ProgressBar, useProgressSteps } from './ProgressBar';
import { BrandedButton, BrandedCard } from './BrandedComponents';
import { BrandLogo } from './BrandLogo';

// Backend response structure (matches backend exactly)
interface BackendTool {
  name: string;
  description: string;
  category: string;
  code: string;
  functions: string[];
}


interface ToolsManagementPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ToolsManagementPanel: React.FC<ToolsManagementPanelProps> = ({
  isOpen,
  onClose,
}) => {
  const [tools, setTools] = useState<Record<string, BackendTool>>({});
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    toolId: '',
    name: '',
    description: '',
    category: '',
    code: '',
    functions: [] as string[],
  });

  // Progress bar for creation/editing
  const toolSteps = ['Verifying Code Syntax', 'Validating Functions', 'Deploying Tool'];
  const progressSteps = useProgressSteps(toolSteps);

  // Categories for organization
  const categories = [
    'filesystem',
    'web',
    'data_processing',
    'database',
    'automation',
    'api',
    'utility',
    'custom'
  ];

  useEffect(() => {
    if (isOpen) {
      loadTools();
    }
  }, [isOpen]);

  const loadTools = async () => {
    try {
      setLoading(true);
      const response = await toolsApi.getTools();
      setTools(response.tools || {});
    } catch (error) {
      console.error('Failed to load tools:', error);
      toast.error('Failed to load tools');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      toolId: '',
      name: '',
      description: '',
      category: '',
      code: '',
      functions: [],
    });
    setSelectedTool(null);
    setIsEditing(false);
    setIsCreating(false);
  };

  const handleCreateNew = () => {
    resetForm();
    setIsCreating(true);
    setFormData({
      ...formData,
      code: `def example_function():
    """
    Example function - replace with your tool implementation
    """
    pass
`
    });
  };

  const handleEditTool = (toolId: string) => {
    const tool = tools[toolId];
    if (tool) {
      setFormData({
        toolId,
        name: tool.name,
        description: tool.description,
        category: tool.category,
        code: tool.code,
        functions: [...tool.functions],
      });
      setSelectedTool(toolId);
      setIsEditing(true);
      setIsCreating(false);
    }
  };

  const handleSaveTool = async () => {
    try {
      if (!formData.name.trim() || !formData.description.trim() || !formData.code.trim()) {
        toast.error('Please fill in all required fields');
        return;
      }

      progressSteps.startProgress();

      // Step 1: Verifying Code Syntax
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      const toolData = {
        name: formData.name,
        description: formData.description,
        category: formData.category || 'custom',
        code: formData.code,
        functions: formData.functions.filter(f => f.trim()),
      };

      // Step 2: Validating Functions
      await new Promise(resolve => setTimeout(resolve, 800));
      progressSteps.nextStep();

      // Step 3: Deploying Tool
      await new Promise(resolve => setTimeout(resolve, 500));

      if (isCreating) {
        const toolId = formData.toolId || formData.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
        await toolsApi.createTool(toolId, toolData);
        progressSteps.completeProgress();
        toast.success(`Tool "${formData.name}" created successfully`);
      } else if (selectedTool) {
        await toolsApi.updateTool(selectedTool, toolData);
        progressSteps.completeProgress();
        toast.success(`Tool "${formData.name}" updated successfully`);
      }

      await loadTools();
      resetForm();
    } catch (error: any) {
      console.error('Failed to save tool:', error);
      progressSteps.hideProgress();

      // Show detailed error message if available
      if (error.validation_errors) {
        toast.error(`Validation failed: ${JSON.stringify(error.validation_errors)}`);
      } else if (error.message) {
        toast.error(`Failed to save tool: ${error.message}`);
      } else {
        toast.error('Failed to save tool');
      }
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!window.confirm(`Are you sure you want to delete "${tools[toolId]?.name}"?`)) {
      return;
    }

    try {
      await toolsApi.deleteTool(toolId);
      toast.success('Tool deleted successfully');
      await loadTools();
      if (selectedTool === toolId) {
        resetForm();
      }
    } catch (error) {
      console.error('Failed to delete tool:', error);
      toast.error('Failed to delete tool');
    }
  };

  const extractFunctionsFromCode = (code: string) => {
    const functionMatches = code.match(/def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g);
    if (functionMatches) {
      const functions = functionMatches.map(match =>
        match.replace(/def\s+|\s*\(/g, '')
      );
      setFormData(prev => ({ ...prev, functions }));
    }
  };

  const handleCodeChange = (code: string) => {
    setFormData(prev => ({ ...prev, code }));
    extractFunctionsFromCode(code);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="tools-modal-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-gradient-to-br from-slate-900/80 via-violet-900/50 to-cyan-900/30 backdrop-blur-sm flex items-center justify-center p-4 z-[60]"
        onClick={onClose}
      >
        <motion.div
          key="tools-modal-content"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-7xl h-5/6 flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <CodeBracketIcon className="h-6 w-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Tools Management
              </h2>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={loadTools}
                disabled={loading}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                title="Refresh tools"
              >
                <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={handleCreateNew}
                className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                <span>New Tool</span>
              </button>
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title="Close"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          <div className="flex-1 flex min-h-0">
            {/* Tools List */}
            <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 flex flex-col">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Available Tools ({Object.keys(tools).length})
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="p-6 text-center">
                    <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-2" />
                    <p className="text-gray-600 dark:text-gray-400">Loading tools...</p>
                  </div>
                ) : Object.keys(tools).length === 0 ? (
                  <BrandedCard variant="glass" className="p-6 text-center m-4">
                    <div className="flex justify-center mb-4">
                      <BrandLogo variant="icon" size="md" />
                    </div>
                    <p className="text-slate-600 dark:text-slate-400 font-medium mb-4">No tools configured yet</p>
                    <BrandedButton
                      onClick={handleCreateNew}
                      variant="primary"
                      size="sm"
                    >
                      Create your first tool
                    </BrandedButton>
                  </BrandedCard>
                ) : (
                  <div className="space-y-2 p-4">
                    {Object.entries(tools).filter(([toolId, tool]) => toolId && tool).map(([toolId, tool]) => (
                      <div
                        key={`tool-${toolId}`}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedTool === toolId
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                        onClick={() => setSelectedTool(toolId)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                              {tool.name}
                            </h4>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                              {tool.description}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                {tool.category}
                              </span>
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {tool.functions.length} functions
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1 ml-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditTool(toolId);
                              }}
                              className="p-1 text-gray-400 hover:text-blue-600"
                              title="Edit tool"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteTool(toolId);
                              }}
                              className="p-1 text-gray-400 hover:text-red-600"
                              title="Delete tool"
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

            {/* Tool Editor */}
            <div className="flex-1 flex flex-col">
              {(isEditing || isCreating) ? (
                <div className="flex-1 flex flex-col">
                  {/* Editor Header */}
                  <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {isCreating ? 'Create New Tool' : 'Edit Tool'}
                      </h3>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={resetForm}
                          className="px-3 py-1 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveTool}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                        >
                          {isCreating ? 'Create Tool' : 'Save Changes'}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Form */}
                  <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
                    {/* Basic Fields - Fixed at top, scrollable */}
                    <div className="flex-shrink-0 p-4 space-y-4 border-b border-gray-200 dark:border-gray-700">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Tool Name *
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                            placeholder="Enter tool name"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Category
                          </label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          >
                            <option value="">Select category</option>
                            {categories.map(cat => (
                              <option key={cat} value={cat}>
                                {cat.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Description *
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={2}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
                          placeholder="Describe what this tool does"
                        />
                      </div>

                      {formData.functions.length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Functions Found
                          </label>
                          <div className="flex flex-wrap gap-2">
                            {formData.functions.filter(func => func && func.trim()).map((func, index) => (
                              <span
                                key={`func-${func}-${index}`}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400"
                              >
                                <CheckCircleIcon className="h-3 w-3 mr-1" />
                                {func}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Code Editor - Takes remaining space */}
                    <div className="flex-1 flex flex-col min-h-0">
                      <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                          Python Code *
                        </label>
                      </div>
                      <div className="flex-1 bg-gray-900 min-h-0">
                        <textarea
                          value={formData.code}
                          onChange={(e) => handleCodeChange(e.target.value)}
                          className="w-full h-full p-4 bg-gray-900 text-gray-100 font-mono text-sm border-none outline-none resize-none"
                          placeholder="# Write your Python tool code here
def example_function():
    '''
    Example function - replace with your tool implementation
    '''
    pass"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ) : selectedTool && tools[selectedTool] ? (
                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                  {/* Tool Details Header */}
                  <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {tools[selectedTool].name}
                        </h3>
                        <p className="text-gray-600 dark:text-gray-400 mt-1">
                          {tools[selectedTool].description}
                        </p>
                      </div>
                      <button
                        onClick={() => handleEditTool(selectedTool)}
                        className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                      >
                        <PencilIcon className="h-4 w-4" />
                        <span>Edit Tool</span>
                      </button>
                    </div>
                  </div>

                  {/* Tool Details */}
                  <div className="flex-1 overflow-y-auto min-h-0">
                    <div className="p-4 space-y-6">
                      {/* Metadata */}
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-3">Tool Information</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-sm text-gray-600 dark:text-gray-400">Category</span>
                            <p className="mt-1">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                {tools[selectedTool].category}
                              </span>
                            </p>
                          </div>
                          <div>
                            <span className="text-sm text-gray-600 dark:text-gray-400">Functions</span>
                            <p className="mt-1 flex flex-wrap gap-1">
                              {tools[selectedTool].functions.filter(func => func && func.trim()).map((func, index) => (
                                <span
                                  key={`selected-func-${func}-${index}`}
                                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                                >
                                  {func}
                                </span>
                              ))}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Code Preview */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium text-gray-900 dark:text-white">Python Code</h4>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(tools[selectedTool].code);
                              toast.success('Code copied to clipboard');
                            }}
                            className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                          >
                            <DocumentDuplicateIcon className="h-4 w-4" />
                            <span>Copy</span>
                          </button>
                        </div>
                        <div className="bg-gray-900 rounded-lg overflow-hidden">
                          <pre className="p-4 text-gray-100 text-sm overflow-x-auto">
                            <code>{tools[selectedTool].code}</code>
                          </pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <CodeBracketIcon className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Select a tool to view details
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Choose a tool from the list or create a new one
                    </p>
                    <button
                      onClick={handleCreateNew}
                      className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg mx-auto"
                    >
                      <PlusIcon className="h-4 w-4" />
                      <span>Create New Tool</span>
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
        steps={toolSteps}
        isVisible={progressSteps.isVisible}
      />
    </AnimatePresence>
  );
};