import React, { useState } from 'react';
import { Group, Agent } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  PlusIcon,
  EllipsisVerticalIcon,
  UserGroupIcon,
  CpuChipIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';

interface SidebarProps {
  groups: Group[];
  selectedGroup: Group | null;
  agents: Agent[];
  groupAgents: Agent[];
  expanded: boolean;
  currentView: 'chat' | 'agent-management';
  onToggleExpanded: () => void;
  onSelectGroup: (group: Group) => void;
  onCreateGroup: (name: string) => void;
  onDeleteGroup: (groupId: string) => void;
  onAddAgent: (agentKey: string) => void;
  onRemoveAgent: (agentKey: string) => void;
  onViewChange: (view: 'chat' | 'agent-management') => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  groups,
  selectedGroup,
  agents,
  groupAgents,
  expanded,
  currentView,
  onToggleExpanded,
  onSelectGroup,
  onCreateGroup,
  onDeleteGroup,
  onAddAgent,
  onRemoveAgent,
  onViewChange,
}) => {
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [showAgentsPanel, setShowAgentsPanel] = useState(false);

  const availableAgents = agents.filter(
    agent => !groupAgents.find(ga => ga.key === agent.key)
  );

  const handleCreateGroup = (e: React.FormEvent) => {
    e.preventDefault();
    if (newGroupName.trim()) {
      onCreateGroup(newGroupName.trim());
      setNewGroupName('');
      setShowCreateGroup(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <motion.div
            initial={{ opacity: expanded ? 1 : 0 }}
            animate={{ opacity: expanded ? 1 : 0 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-purple-600 via-blue-500 to-cyan-400 rounded-lg flex items-center justify-center animate-pulse">
              <SparklesIcon className="w-5 h-5 text-white" />
            </div>
            {expanded && (
              <div>
                <h1 className="text-lg font-bold bg-gradient-to-r from-purple-600 via-blue-500 to-cyan-400 bg-clip-text text-transparent">
                  Agentverse
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Agent Multiverse 🌌
                </p>
              </div>
            )}
          </motion.div>
          
          <button
            onClick={onToggleExpanded}
            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            {expanded ? (
              <ChevronLeftIcon className="w-5 h-5" />
            ) : (
              <ChevronRightIcon className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      {expanded && (
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
          <div className="flex space-x-1 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <button
              onClick={() => onViewChange('chat')}
              className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                currentView === 'chat'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <UserGroupIcon className="w-4 h-4 mr-2" />
              Chat
            </button>
            <button
              onClick={() => onViewChange('agent-management')}
              className={`flex-1 flex items-center justify-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                currentView === 'agent-management'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <CpuChipIcon className="w-4 h-4 mr-2" />
              Agents
            </button>
          </div>
        </div>
      )}

      {/* Groups Section - Only show in chat view */}
      {currentView === 'chat' && (
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            {expanded && (
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                🌌 Universes
              </h2>
            )}
            
            <button
              onClick={() => setShowCreateGroup(true)}
              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
              title="Create new universe"
            >
              <PlusIcon className="w-4 h-4" />
            </button>
          </div>

          {/* Create Group Form */}
          <AnimatePresence>
            {showCreateGroup && expanded && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                onSubmit={handleCreateGroup}
                className="mb-4"
              >
                <div className="space-y-2">
                  <input
                    type="text"
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                    placeholder="Universe name..."
                    className="w-full px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    autoFocus
                  />
                  <div className="flex space-x-2">
                    <button
                      type="submit"
                      className="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Create
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateGroup(false);
                        setNewGroupName('');
                      }}
                      className="flex-1 px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Groups List */}
          <div className="space-y-1">
            {groups.map((group) => (
              <motion.div
                key={group.id}
                whileHover={{ x: 2 }}
                className={`group relative flex items-center space-x-3 p-3 rounded-xl cursor-pointer transition-all ${
                  selectedGroup?.id === group.id
                    ? 'bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 border-l-4 border-blue-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
                onClick={() => onSelectGroup(group)}
              >
                <div className={`w-3 h-3 rounded-full ${
                  selectedGroup?.id === group.id 
                    ? 'bg-green-500' 
                    : 'bg-gray-300 dark:bg-gray-600'
                }`} />
                
                {expanded && (
                  <>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {group.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(group.created_at * 1000).toLocaleDateString()}
                      </p>
                    </div>

                    <Menu as="div" className="relative opacity-0 group-hover:opacity-100 transition-opacity">
                      <Menu.Button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <EllipsisVerticalIcon className="w-4 h-4" />
                      </Menu.Button>
                      <Transition
                        enter="transition duration-100 ease-out"
                        enterFrom="transform scale-95 opacity-0"
                        enterTo="transform scale-100 opacity-100"
                        leave="transition duration-75 ease-in"
                        leaveFrom="transform scale-100 opacity-100"
                        leaveTo="transform scale-95 opacity-0"
                      >
                        <Menu.Items className="absolute right-0 top-full mt-1 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                          <Menu.Item>
                            {({ active }) => (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (confirm(`Delete universe "${group.name}"?`)) {
                                    onDeleteGroup(group.id);
                                  }
                                }}
                                className={`w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md ${
                                  active ? 'bg-red-50 dark:bg-red-900/20' : ''
                                }`}
                              >
                                Delete
                              </button>
                            )}
                          </Menu.Item>
                        </Menu.Items>
                      </Transition>
                    </Menu>
                  </>
                )}
              </motion.div>
            ))}

            {groups.length === 0 && expanded && (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <UserGroupIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No universes yet</p>
                <p className="text-xs">Create your first agent universe 🌌</p>
              </div>
            )}
          </div>
        </div>

        {/* Agents Section */}
        {selectedGroup && expanded && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                Agents ({groupAgents.length})
              </h3>
              <button
                onClick={() => setShowAgentsPanel(!showAgentsPanel)}
                className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
                title="Manage agents"
              >
                <CpuChipIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Active Agents */}
            <div className="space-y-2">
              {groupAgents.map((agent) => (
                <motion.div
                  key={agent.key}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center space-x-3 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800"
                >
                  <span className="text-lg">{agent.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {agent.name}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      {agent.description}
                    </p>
                  </div>
                  <button
                    onClick={() => onRemoveAgent(agent.key)}
                    className="text-red-400 hover:text-red-600 transition-colors"
                    title="Remove agent"
                  >
                    <PlusIcon className="w-4 h-4 transform rotate-45" />
                  </button>
                </motion.div>
              ))}
            </div>

            {/* Available Agents Panel */}
            <AnimatePresence>
              {showAgentsPanel && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700"
                >
                  <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">
                    AVAILABLE AGENTS
                  </h4>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {availableAgents.map((agent) => (
                      <motion.div
                        key={agent.key}
                        whileHover={{ x: 2 }}
                        className="flex items-center space-x-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg cursor-pointer"
                        onClick={() => onAddAgent(agent.key)}
                      >
                        <span className="text-lg">{agent.emoji}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {agent.name}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {agent.description}
                          </p>
                        </div>
                        <PlusIcon className="w-4 h-4 text-green-500" />
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
      )}
    </div>
  );
};