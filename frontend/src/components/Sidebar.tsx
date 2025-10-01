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
  SparklesIcon,
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';
import { BrandLogo } from './BrandLogo';

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
      {/* Premium Header with Brand Logo */}
      <div className="relative p-4 border-b border-violet-200/30 dark:border-violet-800/30">
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
        <div className="relative flex items-center justify-between">
          <motion.div
            initial={{ opacity: expanded ? 1 : 0 }}
            animate={{ opacity: expanded ? 1 : 0 }}
            transition={{ duration: 0.3 }}
            className="flex items-center"
          >
            {expanded ? (
              <BrandLogo variant="horizontal" size="sm" showText={true} />
            ) : (
              <BrandLogo variant="icon" size="sm" showText={false} />
            )}
          </motion.div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onToggleExpanded}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-violet-100/50 dark:hover:bg-violet-900/30 transition-all duration-200"
          >
            {expanded ? (
              <ChevronLeftIcon className="w-4 h-4" />
            ) : (
              <ChevronRightIcon className="w-4 h-4" />
            )}
          </motion.button>
        </div>
      </div>

      {/* Premium Navigation Tabs */}
      {expanded && (
        <div className="relative px-4 py-3 border-b border-violet-200/30 dark:border-violet-800/30">
          <div className="absolute inset-0 bg-gradient-to-r from-violet-50/30 to-cyan-50/20 dark:from-violet-950/30 dark:to-cyan-950/20" />
          <div className="relative flex space-x-1 p-1 bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-violet-200/20 dark:border-violet-800/20">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onViewChange('chat')}
              className={`flex-1 flex items-center justify-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                currentView === 'chat'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-violet-100/60 dark:hover:bg-violet-900/40 hover:text-slate-800 dark:hover:text-slate-100'
              }`}
            >
              <UserGroupIcon className="w-4 h-4 mr-2" />
              Conversations
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onViewChange('agent-management')}
              className={`flex-1 flex items-center justify-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                currentView === 'agent-management'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-violet-100/60 dark:hover:bg-violet-900/40 hover:text-slate-800 dark:hover:text-slate-100'
              }`}
            >
              <CpuChipIcon className="w-4 h-4 mr-2" />
              Agent Studio
            </motion.button>
          </div>
        </div>
      )}

      {/* Enhanced Groups Section - Only show in chat view */}
      {currentView === 'chat' && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Groups Header - Fixed */}
          <div className="p-4 border-b border-violet-200/30 dark:border-violet-800/30">
            <div className="flex items-center justify-between">
              {expanded && (
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 animate-pulse" />
                  <h2 className="text-sm font-bold bg-gradient-to-r from-slate-700 to-slate-500 dark:from-slate-200 dark:to-slate-400 bg-clip-text text-transparent uppercase tracking-wider">
                    Conversations
                  </h2>
                </div>
              )}

              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setShowCreateGroup(true)}
                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-gradient-to-r hover:from-indigo-50 hover:to-purple-50 dark:hover:from-indigo-950/50 dark:hover:to-purple-950/50 rounded-lg transition-all duration-200 shadow-sm hover:shadow-lg hover:shadow-indigo-500/20"
                title="Create new conversation"
              >
                <PlusIcon className="w-4 h-4" />
              </motion.button>
            </div>

            {/* Enhanced Create Group Form */}
            <AnimatePresence>
              {showCreateGroup && expanded && (
                <motion.form
                  initial={{ opacity: 0, height: 0, y: -10 }}
                  animate={{ opacity: 1, height: 'auto', y: 0 }}
                  exit={{ opacity: 0, height: 0, y: -10 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  onSubmit={handleCreateGroup}
                  className="relative mt-4"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 rounded-xl" />
                  <div className="relative space-y-3 p-4 bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl border border-violet-200/20 dark:border-violet-800/20">
                    <input
                      type="text"
                      value={newGroupName}
                      onChange={(e) => setNewGroupName(e.target.value)}
                      placeholder="Conversation name..."
                      className="w-full px-4 py-3 text-sm bg-white/80 dark:bg-slate-700/80 border border-violet-200/30 dark:border-violet-800/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 placeholder-slate-400 transition-all duration-200"
                      autoFocus
                    />
                    <div className="flex space-x-2">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="submit"
                        className="flex-1 px-4 py-2.5 text-sm font-medium bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all duration-200 shadow-lg shadow-indigo-500/25"
                      >
                        Create
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="button"
                        onClick={() => {
                          setShowCreateGroup(false);
                          setNewGroupName('');
                        }}
                        className="flex-1 px-4 py-2.5 text-sm font-medium bg-white/80 dark:bg-slate-700/80 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 transition-all duration-200 border border-violet-200/30 dark:border-violet-800/30"
                      >
                        Cancel
                      </motion.button>
                    </div>
                  </div>
                </motion.form>
              )}
            </AnimatePresence>
          </div>

          {/* Groups List - Scrollable, limited height to show ~3-4 items */}
          <div className="overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-violet-300 dark:scrollbar-thumb-violet-700 scrollbar-track-transparent hover:scrollbar-thumb-violet-400 dark:hover:scrollbar-thumb-violet-600" style={{ maxHeight: '280px' }}>
            {groups.map((group) => (
              <motion.div
                key={group.id}
                whileHover={{ x: 3, scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                className={`group relative flex items-center space-x-3 p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                  selectedGroup?.id === group.id
                    ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/50 dark:to-purple-950/50 border border-indigo-200/50 dark:border-indigo-800/50 shadow-lg shadow-indigo-500/10'
                    : 'bg-white/40 dark:bg-slate-800/40 hover:bg-white/70 dark:hover:bg-slate-800/70 hover:shadow-lg hover:shadow-violet-500/10 border border-violet-200/20 dark:border-violet-800/20'
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

          {/* Agents Section - Fixed at bottom with scrollable content */}
          {selectedGroup && expanded && (
            <div className="border-t border-gray-200 dark:border-gray-700 flex flex-col" style={{ maxHeight: '45vh' }}>
              {/* Agents Header */}
              <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
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
              </div>

              {/* Active Agents - Scrollable independently */}
              <div className="flex-shrink-0 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-violet-300 dark:scrollbar-thumb-violet-700 scrollbar-track-transparent" style={{ maxHeight: showAgentsPanel ? '150px' : '250px' }}>
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

              {/* Available Agents Panel - Scrollable independently */}
              <AnimatePresence>
                {showAgentsPanel && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 flex flex-col"
                  >
                    <div className="flex-shrink-0 p-4 pb-2">
                      <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                        AVAILABLE AGENTS
                      </h4>
                    </div>
                    <div className="overflow-y-auto p-4 pt-2 space-y-1 scrollbar-thin scrollbar-thumb-violet-300 dark:scrollbar-thumb-violet-700 scrollbar-track-transparent" style={{ maxHeight: '150px' }}>
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