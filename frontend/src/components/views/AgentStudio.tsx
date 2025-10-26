import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiService } from '@/lib/api';
import { BrandedButton, BrandedCard } from '../shared/BrandedComponents';
import { BrandLogo } from '../shared/BrandLogo';

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

interface AgentStudioProps {
  onCreateAgent: () => void;
  onEditAgent: (agent: Agent) => void;
  onAgentDeleted?: () => void;
}

export const AgentStudio: React.FC<AgentStudioProps> = ({
  onCreateAgent,
  onEditAgent,
  onAgentDeleted
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAvailableAgents();
      setAgents(response || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
      toast.error('Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agentKey: string) => {
    if (!confirm(`Are you sure you want to delete agent "${agentKey}"?`)) {
      return;
    }

    try {
      await apiService.deleteAgent(agentKey);
      toast.success(`Agent "${agentKey}" deleted successfully`);
      loadAgents();
      onAgentDeleted?.();
    } catch (error) {
      console.error('Failed to delete agent:', error);
      toast.error('Failed to delete agent');
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20">
      {/* Content */}
      <div className="flex-1 p-6 overflow-auto">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
              Existing Agents ({agents.length})
            </h2>
            <BrandedButton
              variant="primary"
              onClick={onCreateAgent}
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
                onClick={onCreateAgent}
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
                  className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700 h-[200px] flex flex-col"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3 min-w-0 flex-1">
                      <span className="text-2xl flex-shrink-0">{agent.emoji}</span>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                          {agent.name}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {agent.key}
                        </p>
                      </div>
                    </div>
                    <div className="flex space-x-1 flex-shrink-0 ml-2">
                      <button
                        onClick={() => onEditAgent(agent)}
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
                  <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 flex-1 line-clamp-3 overflow-hidden">
                    {agent.description}
                  </p>
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-auto">
                    <span>Agent • Ready</span>
                    <button
                      onClick={() => onEditAgent(agent)}
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
      </div>
    </div>
  );
};
