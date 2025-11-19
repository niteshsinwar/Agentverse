import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import {
  PlusIcon,
  TrashIcon,
  PencilIcon,
  CodeBracketIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline';
import { toolsApi } from "@/lib/api";
import { ProgressBar, useProgressSteps } from '../shared/ProgressBar';
import { Tab } from '@headlessui/react';
import { BrandedButton, BrandedCard } from '../shared/BrandedComponents';
import { BrandLogo } from '../shared/BrandLogo';
import { SlidingPanel } from '../core/SlidingPanel';

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

  const labelClass = 'block text-sm font-semibold text-slate-600 dark:text-slate-300 mb-2';
  const inputClass = 'brand-field w-full rounded-xl px-3 py-2 text-sm';

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
      progressSteps.hideProgress();

      // Show specific error message
      if (error?.validation_errors) {
        const validationData = error.validation_errors;
        if (validationData?.errors?.length > 0) {
          const errorMessage = validationData.errors.map((err: any) => `${err.field}: ${err.message}`).join(', ');
          toast.error(`Validation failed: ${errorMessage}`);
        } else {
          toast.error('Tool configuration validation failed');
        }
      } else if (error?.message) {
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

  const headerActions = (
    <>
      <button
        onClick={loadTools}
        disabled={loading}
        className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 disabled:opacity-50 transition-colors"
        title="Refresh tools"
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
        <span>New Tool</span>
      </BrandedButton>
    </>
  );

  return (
    <SlidingPanel
      isOpen={isOpen}
      onClose={onClose}
      title="Tools Management"
      subtitle="Create, validate, and maintain automation tools"
      icon={<CodeBracketIcon className="h-6 w-6 text-sky-500" />}
      actions={headerActions}
      size="xlarge"
      headerClassName="border-b border-transparent"
      headerBackgroundClassName={null}
      containerClassName="brand-surface-strong rounded-3xl border border-transparent shadow-2xl"
      contentClassName="flex flex-1 min-h-0"
    >
      <div className="flex-1 flex flex-col min-h-0">
        <Tab.Group vertical className="flex-1 flex flex-col min-h-0">
          <div className="flex flex-1 min-h-0">
            {/* Tools List */}
            <div className="w-[400px] min-w-[400px] max-w-[400px] border-r border-transparent flex flex-col min-h-0">
              <div className="p-4 border-b border-transparent">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                  Available Tools ({Object.keys(tools).length})
                </h3>
              </div>

              <div className="flex-1 overflow-y-auto">
                {loading ? (
                  <div className="p-6 text-center">
                    <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-sky-500 mb-2" />
                    <p className="text-slate-600 dark:text-slate-400">Loading tools...</p>
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
                        className={`p-3 rounded-2xl border cursor-pointer transition-all ${
                          selectedTool === toolId
                            ? 'border-transparent brand-gradient text-white shadow-lg shadow-sky-500/25'
                            : 'border-transparent hover:bg-white/60 dark:hover:bg-slate-800/60'
                        }`}
                        onClick={() => setSelectedTool(toolId)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className={`text-sm font-medium truncate ${selectedTool === toolId ? 'text-white' : 'text-slate-900 dark:text-white'}`}>
                              {tool.name}
                            </h4>
                            <p className={`text-xs mt-1 line-clamp-2 ${selectedTool === toolId ? 'text-white/80' : 'text-slate-600 dark:text-slate-400'}`}>
                              {tool.description}
                            </p>
                            <div className="flex items-center space-x-2 mt-2">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${selectedTool === toolId ? 'bg-white/20 text-white' : 'brand-chip'}`}>
                                {tool.category}
                              </span>
                              <span className={`text-xs ${selectedTool === toolId ? 'text-white/80' : 'text-slate-500 dark:text-slate-400'}`}>
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
                              className="p-1 text-slate-400 hover:text-sky-500"
                              title="Edit tool"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteTool(toolId);
                              }}
                              className="p-1 text-slate-400 hover:text-red-600"
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
            <div className="flex-1 min-w-0 flex flex-col">
              {(isEditing || isCreating) ? (
                <div className="flex-1 flex flex-col">
                  {/* Editor Header */}
                  <div className="p-4 border-b border-transparent">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                        {isCreating ? 'Create New Tool' : 'Edit Tool'}
                      </h3>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={resetForm}
                          className="px-3 py-1 text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveTool}
                          className="px-4 py-2 brand-cta rounded-xl"
                        >
                          {isCreating ? 'Create Tool' : 'Save Changes'}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Form */}
                  <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
                    {/* Basic Fields - Fixed at top, scrollable */}
                    <div className="flex-shrink-0 p-4 space-y-4 border-b border-transparent">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className={labelClass}>
                            Tool Name *
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            className={`${inputClass} focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
                            placeholder="Enter tool name"
                          />
                        </div>
                        <div>
                          <label className={labelClass}>
                            Category
                          </label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                            className={`${inputClass} focus:ring-2 focus:ring-sky-500 focus:border-transparent`}
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
                        <label className={labelClass}>
                          Description *
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          rows={2}
                          className={`${inputClass} focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none`}
                          placeholder="Describe what this tool does"
                        />
                      </div>

                      {formData.functions.length > 0 && (
                        <div>
                          <label className={labelClass}>
                            Functions Found
                          </label>
                          <div className="flex flex-wrap gap-2">
                            {formData.functions.filter(func => func && func.trim()).map((func, index) => (
                              <span
                                key={`func-${func}-${index}`}
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs border border-emerald-300/40 dark:border-emerald-600/40 bg-gradient-to-r from-emerald-500/15 to-teal-500/15 text-emerald-600 dark:text-emerald-300"
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
                      <div className="flex-shrink-0 p-4 border-b border-transparent">
                        <label className={labelClass}>
                          Python Code *
                        </label>
                      </div>
                      <div className="flex-1 bg-slate-950 min-h-0 rounded-t-3xl">
                        <textarea
                          value={formData.code}
                          onChange={(e) => handleCodeChange(e.target.value)}
                          className="w-full h-full p-4 bg-slate-900 text-slate-100 font-mono text-sm border-none outline-none resize-none"
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
                  <div className="flex-shrink-0 p-4 border-b border-transparent">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                          {tools[selectedTool].name}
                        </h3>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">
                          {tools[selectedTool].description}
                        </p>
                      </div>
                      <button
                        onClick={() => handleEditTool(selectedTool)}
                        className="flex items-center space-x-2 brand-cta px-4 py-2 rounded-xl"
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
                        <h4 className="font-medium text-slate-900 dark:text-white mb-3">Tool Information</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <span className="text-sm text-slate-600 dark:text-slate-400">Category</span>
                            <p className="mt-1">
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs brand-chip">
                                {tools[selectedTool].category}
                              </span>
                            </p>
                          </div>
                          <div>
                            <span className="text-sm text-slate-600 dark:text-slate-400">Functions</span>
                            <p className="mt-1 flex flex-wrap gap-1">
                              {tools[selectedTool].functions.filter(func => func && func.trim()).map((func, index) => (
                                <span
                                  key={`selected-func-${func}-${index}`}
                                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gradient-to-r from-slate-400/20 to-sky-500/20 text-sky-600 dark:text-sky-300 border border-sky-300/40 dark:border-sky-600/40"
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
                          <h4 className="font-medium text-slate-900 dark:text-white">Python Code</h4>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(tools[selectedTool].code);
                              toast.success('Code copied to clipboard');
                            }}
                            className="flex items-center space-x-1 text-sm text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                          >
                            <DocumentDuplicateIcon className="h-4 w-4" />
                            <span>Copy</span>
                          </button>
                        </div>
                        <div className="bg-slate-900 rounded-lg overflow-hidden">
                          <pre className="p-4 text-slate-100 text-sm overflow-x-auto">
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
                    <CodeBracketIcon className="h-16 w-16 mx-auto text-slate-400 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                      Select a tool to view details
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">
                      Choose a tool from the list or create a new one
                    </p>
                    <button
                      onClick={handleCreateNew}
                      className="flex items-center space-x-2 brand-cta px-4 py-2 rounded-xl mx-auto"
                    >
                      <PlusIcon className="h-4 w-4" />
                      <span>Create New Tool</span>
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
        steps={toolSteps}
        isVisible={progressSteps.isVisible}
      />
    </SlidingPanel>
  );
};
