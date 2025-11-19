import React, { useState, useEffect } from 'react';
import { Group, Agent } from '@/lib/types';
import { motion } from 'framer-motion';
import { Dialog, Combobox } from '@headlessui/react';
import { 
  MagnifyingGlassIcon,
  CommandLineIcon,
  UserGroupIcon,
  PlusIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  groups: Group[];
  agents: Agent[];
  onSelectGroup: (group: Group) => void;
  onCreateGroup: (name: string) => void;
}

interface Command {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  action: () => void;
  category: 'workspace' | 'agent' | 'action';
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  groups,
  agents,
  onSelectGroup,
  onCreateGroup,
}) => {
  const [query, setQuery] = useState('');

  // Build commands dynamically
  const commands: Command[] = [
    // Workspace commands
    ...groups.map(group => ({
      id: `group-${group.id}`,
      title: group.name,
      subtitle: 'Switch to workspace',
      icon: <UserGroupIcon className="w-5 h-5 text-indigo-500" />,
      action: () => {
        onSelectGroup(group);
        onClose();
      },
      category: 'workspace' as const,
    })),
    
    // Agent commands
    ...agents.map(agent => ({
      id: `agent-${agent.key}`,
      title: agent.name,
      subtitle: agent.description,
      icon: <span className="text-lg">{agent.emoji}</span>,
      action: () => {
        // Could implement direct agent interaction
        onClose();
      },
      category: 'agent' as const,
    })),
    
    // Action commands
    {
      id: 'create-workspace',
      title: 'Create New Workspace',
      subtitle: 'Set up a new collaboration space',
      icon: <PlusIcon className="w-5 h-5 text-green-500" />,
      action: () => {
        const name = prompt('Workspace name:');
        if (name) {
          onCreateGroup(name);
        }
        onClose();
      },
      category: 'action',
    },
  ];

  const filteredCommands = commands.filter(command => {
    if (!query) return true;
    
    const searchText = `${command.title} ${command.subtitle}`.toLowerCase();
    return searchText.includes(query.toLowerCase());
  });

  const groupedCommands = {
    workspace: filteredCommands.filter(c => c.category === 'workspace'),
    agent: filteredCommands.filter(c => c.category === 'agent'),
    action: filteredCommands.filter(c => c.category === 'action'),
  };

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onClose={onClose} className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4 sm:p-6">
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-md" onClick={onClose} />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          className="relative w-full max-w-2xl mx-auto overflow-hidden rounded-3xl brand-surface shadow-[0_35px_120px_rgba(15,23,42,0.45)] border border-transparent"
        >
          <Combobox onChange={(command: Command) => command.action()}>
            {/* Header */}
            <div className="relative flex items-center px-6 py-4 border-b border-transparent">
              <div className="pointer-events-none absolute inset-0 brand-gradient-soft opacity-40" />
              <CommandLineIcon className="relative w-5 h-5 text-indigo-500 dark:text-indigo-300 mr-3" />
              <Dialog.Title className="relative text-lg font-semibold text-slate-900 dark:text-white">
                Command Palette
              </Dialog.Title>
              <div className="relative ml-auto">
                <kbd className="px-2 py-1 text-xs font-semibold text-slate-500 bg-white/70 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 rounded-lg">
                  ESC
                </kbd>
              </div>
            </div>

            {/* Search Input */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-6 top-4 w-5 h-5 text-slate-400 dark:text-slate-500" />
              <Combobox.Input
                className="w-full pl-14 pr-6 py-4 text-lg bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400/70 focus:outline-none"
                placeholder="Search workspaces, agents, and actions..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                autoComplete="off"
              />
            </div>

            {/* Results */}
            <div className="max-h-96 overflow-y-auto border-t border-transparent">
              <Combobox.Options static className="py-4">
                {Object.entries(groupedCommands).map(([category, commands]) => {
                  if (commands.length === 0) return null;

                  const categoryLabels = {
                    workspace: 'Workspaces',
                    agent: 'Agents',
                    action: 'Actions',
                  };

                  return (
                    <div key={category} className="mb-6 last:mb-0">
                      <div className="px-6 py-2">
                        <h3 className="text-xs font-semibold uppercase tracking-[0.45em] text-slate-500 dark:text-slate-400">
                          {categoryLabels[category as keyof typeof categoryLabels]}
                        </h3>
                      </div>
                      
                      <div className="space-y-1">
                        {commands.map((command) => (
                          <Combobox.Option
                            key={command.id}
                            value={command}
                            className={({ active }) =>
                              `relative cursor-pointer select-none px-6 py-3 flex items-center space-x-4 rounded-2xl mx-2 transition-all duration-200 ${
                                active
                                  ? 'brand-gradient text-white shadow-lg shadow-indigo-500/25'
                                  : 'text-slate-900 dark:text-white hover:bg-white/60 dark:hover:bg-slate-800/60'
                              }`
                            }
                          >
                            {({ active }) => (
                              <>
                                <div className="flex-shrink-0">
                                  {command.icon}
                                </div>
                                
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-semibold truncate">
                                    {command.title}
                                  </div>
                                  <div className="text-xs text-slate-500 dark:text-slate-300 truncate">
                                    {command.subtitle}
                                  </div>
                                </div>
                                
                                {active && (
                                  <ArrowRightIcon className="w-4 h-4 text-white flex-shrink-0" />
                                )}
                              </>
                            )}
                          </Combobox.Option>
                        ))}
                      </div>
                    </div>
                  );
                })}

                {filteredCommands.length === 0 && (
                  <div className="px-6 py-12 text-center text-slate-500 dark:text-slate-300">
                    <MagnifyingGlassIcon className="w-8 h-8 text-indigo-400 mx-auto mb-4" />
                    <p className="text-sm">
                      No results found for "{query}"
                    </p>
                    <p className="text-xs opacity-70 mt-1">
                      Try searching for workspaces, agents, or actions
                    </p>
                  </div>
                )}
              </Combobox.Options>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-transparent bg-white/60 dark:bg-slate-900/60">
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-300">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <kbd className="px-1.5 py-0.5 bg-white/80 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 rounded-lg text-xs">↵</kbd>
                    <span>to select</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <kbd className="px-1.5 py-0.5 bg-white/80 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 rounded-lg text-xs">↑↓</kbd>
                    <span>to navigate</span>
                  </div>
                </div>
                
                <div>
                  <span>{filteredCommands.length} result{filteredCommands.length !== 1 ? 's' : ''}</span>
                </div>
              </div>
            </div>
          </Combobox>
        </motion.div>
      </div>
    </Dialog>
  );
};
