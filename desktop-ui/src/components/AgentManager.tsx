import React, { useState } from 'react';
import { Agent } from '../types';
import { Bot, Plus, Minus, ChevronDown, ChevronRight } from 'lucide-react';

interface AgentManagerProps {
  agents: Agent[];
  groupAgents: Agent[];
  onAddAgent: (agentKey: string) => void;
  onRemoveAgent: (agentKey: string) => void;
}

export const AgentManager: React.FC<AgentManagerProps> = ({
  agents,
  groupAgents,
  onAddAgent,
  onRemoveAgent,
}) => {
  const [showAvailableAgents, setShowAvailableAgents] = useState(false);
  
  const availableAgents = agents.filter(
    agent => !groupAgents.find(ga => ga.key === agent.key)
  );

  return (
    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
      {/* Group Members */}
      <div className="mb-6">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Group Members ({groupAgents.length})
        </h4>
        
        {groupAgents.length > 0 ? (
          <div className="space-y-2">
            {groupAgents.map((agent) => (
              <div
                key={agent.key}
                className="flex items-center justify-between p-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
              >
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-lg">{agent.emoji}</span>
                  <div>
                    <div className="font-medium text-sm text-gray-900 dark:text-white">
                      {agent.name}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-300">
                      {agent.description}
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => onRemoveAgent(agent.key)}
                  className="p-1 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                  title="Remove agent"
                >
                  <Minus className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <Bot className="w-6 h-6 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No agents in this group</p>
            <p className="text-xs">Add agents from the available list below</p>
          </div>
        )}
      </div>

      {/* Available Agents */}
      {availableAgents.length > 0 && (
        <div>
          <button
            onClick={() => setShowAvailableAgents(!showAvailableAgents)}
            className="w-full flex items-center justify-between p-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Available Agents ({availableAgents.length})
            </span>
            {showAvailableAgents ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
          
          {showAvailableAgents && (
            <div className="mt-2 space-y-1">
              {availableAgents.map((agent) => (
                <div
                  key={agent.key}
                  className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <div className="flex items-center gap-2 flex-1">
                    <span className="text-lg">{agent.emoji}</span>
                    <div>
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {agent.name}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">
                        {agent.description}
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => onAddAgent(agent.key)}
                    className="p-1 text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
                    title="Add agent"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};