import React from 'react';
import { motion } from 'framer-motion';
import { Menu, Transition } from '@headlessui/react';
import { BrandLogo } from './BrandLogo';

interface UnifiedHeaderProps {
  currentView: 'chat' | 'agent-management';
  onViewChange: (view: 'chat' | 'agent-management') => void;
  onOpenCommandPalette: () => void;
  onOpenSettings: () => void;
  onOpenToolsManagement: () => void;
  onOpenMcpManagement: () => void;
}

export const UnifiedHeader: React.FC<UnifiedHeaderProps> = ({
  currentView,
  onViewChange,
  onOpenCommandPalette,
  onOpenSettings,
  onOpenToolsManagement,
  onOpenMcpManagement,
}) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="relative bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-violet-200/30 dark:border-violet-800/30 shadow-lg shadow-violet-500/5 z-50"
    >
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />

      <div className="relative flex items-center justify-between px-6 py-4">
        {/* Left Section - Logo & Navigation */}
        <div className="flex items-center space-x-8">
          <BrandLogo variant="horizontal" size="md" className="flex-shrink-0" />

          <div className="h-6 w-px bg-gradient-to-b from-transparent via-violet-300 to-transparent dark:via-violet-700" />

          <nav className="hidden md:flex items-center space-x-6">
            <motion.button
              onClick={() => onViewChange('chat')}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                currentView === 'chat'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-violet-100 dark:hover:bg-violet-900/50'
              }`}
            >
              Conversations
            </motion.button>
            <motion.button
              onClick={() => onViewChange('agent-management')}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                currentView === 'agent-management'
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-violet-100 dark:hover:bg-violet-900/50'
              }`}
            >
              Agent Studio
            </motion.button>
          </nav>
        </div>

        {/* Right Section - Actions */}
        <div className="flex items-center space-x-3">
          {/* Command Palette Button */}
          <motion.button
            onClick={onOpenCommandPalette}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center space-x-2 px-4 py-2 text-sm text-slate-600 dark:text-slate-300 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl border border-violet-200/30 dark:border-violet-800/30 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 transition-all duration-200 shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="font-medium">⌘K</span>
          </motion.button>

          {/* Settings Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="p-2.5 text-slate-500 hover:text-violet-600 dark:text-slate-400 dark:hover:text-violet-400 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl border border-violet-200/30 dark:border-violet-800/30 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 transition-all duration-200 shadow-sm">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </Menu.Button>

            <Transition
              enter="transition duration-100 ease-out"
              enterFrom="transform scale-95 opacity-0"
              enterTo="transform scale-100 opacity-100"
              leave="transition duration-75 ease-in"
              leaveFrom="transform scale-100 opacity-100"
              leaveTo="transform scale-95 opacity-0"
            >
              <Menu.Items className="absolute right-0 top-full mt-2 w-56 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-violet-200/30 dark:border-violet-800/30 z-50">
                <div className="py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onOpenSettings}
                        className={`w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1 ${
                          active
                            ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span>Application Settings</span>
                        </div>
                      </button>
                    )}
                  </Menu.Item>
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onOpenToolsManagement}
                        className={`w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1 ${
                          active
                            ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
                          </svg>
                          <span>Manage Tools</span>
                        </div>
                      </button>
                    )}
                  </Menu.Item>
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onOpenMcpManagement}
                        className={`w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1 ${
                          active
                            ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20'
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21.75 17.25v-.228a4.5 4.5 0 00-.12-1.03l-2.268-9.64a3.375 3.375 0 00-3.285-2.602H7.923a3.375 3.375 0 00-3.285 2.602l-2.268 9.64a4.5 4.5 0 00-.12 1.03v.228m19.5 0a3 3 0 01-3 3H5.25a3 3 0 01-3-3m19.5 0v1.5a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 20.25v-1.5m16.5 0h-16.5" />
                          </svg>
                          <span>Manage MCP Servers</span>
                        </div>
                      </button>
                    )}
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </motion.header>
  );
};