import { useEffect, useRef } from 'react';
import { useAppStore } from '@/shared/store/app.store';
import { useGroupsStore } from '@/shared/store/groups.store';
import { useAgentsStore } from '@/shared/store/agents.store';
import { Toaster, toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, Transition } from '@headlessui/react';
import { ThemeProvider } from './contexts/ThemeContext';

// Modern, enterprise-grade components
import { Sidebar } from './components/Sidebar';
import { MainWorkspace } from './components/MainWorkspace';
import { CommandPalette } from './components/CommandPalette';
import { EnhancedAgentCreationPanel } from './components/EnhancedAgentCreationPanel';
import { SettingsPanel } from './components/SettingsPanel';
import { ToolsManagementPanel } from './components/ToolsManagementPanel';
import { McpManagementPanel } from './components/McpManagementPanel';
import { HelpPanel } from './components/HelpPanel';
import { ComprehensiveLogPanel } from './components/ComprehensiveLogPanel';
import { AnimatedSplashScreen } from './components/AnimatedSplashScreen';

import './App.css';

function App() {
  // App Store
  const {
    sidebarExpanded,
    setSidebarExpanded,
    currentView,
    setCurrentView,
    commandPaletteOpen,
    setCommandPaletteOpen,
    settingsOpen,
    setSettingsOpen,
    toolsManagementOpen,
    setToolsManagementOpen,
    mcpManagementOpen,
    setMcpManagementOpen,
    helpOpen,
    setHelpOpen,
    logsOpen,
    setLogsOpen,
    appLoading,
    setAppLoading,
    showSplash,
    setShowSplash,
    setAppReady,
    initialLoadCompleted: storeInitialLoadCompleted,
    setInitialLoadCompleted,
  } = useAppStore();

  // Groups Store
  const {
    groups,
    selectedGroup,
    groupAgents,
    messages,
    loadGroups,
    setSelectedGroup,
    createGroup,
    deleteGroup,
    addAgentToGroup,
    removeAgentFromGroup,
    sendMessage,
    uploadDocument,
    stopGroupChain,
  } = useGroupsStore();

  // Agents Store
  const {
    agents,
    loadAgents,
  } = useAgentsStore();

  const initialLoadCompleted = useRef(storeInitialLoadCompleted);

  // Enhanced loading with better error handling
  const loadData = async (isInitialLoad = false) => {
    try {
      setAppLoading(true);

      await Promise.all([
        loadGroups(),
        loadAgents(),
      ]);

      // Auto-select first group if available
      if (groups.data && groups.data.length > 0 && !selectedGroup) {
        await setSelectedGroup(groups.data[0]);
      }

      // Only show initialization toast on first load and if not already shown
      if (isInitialLoad && !initialLoadCompleted.current) {
        toast.success('Platform initialized successfully');
        initialLoadCompleted.current = true;
        setInitialLoadCompleted(true);
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
      if (isInitialLoad && !initialLoadCompleted.current) {
        toast.error('Failed to initialize platform');
        initialLoadCompleted.current = true;
        setInitialLoadCompleted(true);
      }
    } finally {
      setAppLoading(false);
      setAppReady(true);
    }
  };

  useEffect(() => {
    loadData(true);
  }, []);

  // Handle splash screen completion
  const handleSplashComplete = () => {
    setShowSplash(false);
  };

  // Group data is now handled automatically by the store when selectedGroup changes

  // SSE connection is now handled automatically by the Groups store
  // The store will automatically update messages when events are received

  // Enhanced group management
  const handleGroupCreate = async (name: string) => {
    try {
      const newGroup = await createGroup(name);
      await setSelectedGroup(newGroup);
      toast.success(`Created group: ${name}`);
    } catch (error) {
      console.error('Failed to create group:', error);
      toast.error('Failed to create group');
    }
  };

  const handleGroupDelete = async (groupId: string) => {
    try {
      await deleteGroup(groupId);

      // If we deleted the selected group, select the first available group
      if (selectedGroup?.id === groupId && groups.data && groups.data.length > 0) {
        const remainingGroups = groups.data.filter(g => g.id !== groupId);
        await setSelectedGroup(remainingGroups[0] || null);
      }

      toast.success('Group deleted');
    } catch (error) {
      console.error('Failed to delete group:', error);
      toast.error('Failed to delete group');
    }
  };

  const handleAddAgent = async (agentKey: string) => {
    if (!selectedGroup) return;

    try {
      await addAgentToGroup(selectedGroup.id, agentKey);
      const agent = agents.data?.find(a => a.key === agentKey);
      if (agent) {
        toast.success(`Added ${agent.name} to ${selectedGroup.name}`);
      }
    } catch (error) {
      console.error('Failed to add agent:', error);
      toast.error('Failed to add agent');
    }
  };

  const handleRemoveAgent = async (agentKey: string) => {
    if (!selectedGroup) return;

    try {
      const agent = groupAgents.data?.find(a => a.key === agentKey);
      await removeAgentFromGroup(selectedGroup.id, agentKey);

      if (agent) {
        toast.success(`Removed ${agent.name} from ${selectedGroup.name}`);
      }
    } catch (error) {
      console.error('Failed to remove agent:', error);
      toast.error('Failed to remove agent');
    }
  };

  const handleSendMessage = async (agentId: string, message: string) => {
    if (!selectedGroup) return;

    try {
      await sendMessage(selectedGroup.id, agentId, message);
      // Store will handle optimistic updates and SSE events automatically
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleUploadDocument = async (agentId: string, file: File, message: string = '') => {
    if (!selectedGroup) return;

    try {
      await uploadDocument(selectedGroup.id, file, agentId, message);
      toast.success(`Document "${file.name}" uploaded successfully`);
      // Store will handle automatic refresh via SSE events
    } catch (error) {
      console.error('Failed to upload document:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to upload document';
      toast.error(errorMessage);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (e.key === 'Escape') {
        setCommandPaletteOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <ThemeProvider>
      {/* Animated Splash Screen */}
      <AnimatedSplashScreen
        isLoading={showSplash || appLoading}
        onComplete={handleSplashComplete}
      />

      {/* Main App Content */}
      {!showSplash && !appLoading && (
      <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20 overflow-hidden">

        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(249,250,251,0.95) 100%)',
              color: '#1e293b',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '16px',
              boxShadow: '0 25px 50px -12px rgba(139, 92, 246, 0.25), 0 0 20px rgba(139, 92, 246, 0.1)',
              backdropFilter: 'blur(20px)',
              fontWeight: '500',
              fontSize: '14px',
              maxWidth: '400px',
              padding: '16px',
            },
            success: {
              style: {
                background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(255,255,255,0.95) 100%)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#059669',
              },
              iconTheme: {
                primary: '#10b981',
                secondary: '#ffffff',
              },
            },
            error: {
              style: {
                background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(255,255,255,0.95) 100%)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#dc2626',
              },
              iconTheme: {
                primary: '#ef4444',
                secondary: '#ffffff',
              },
            },
            loading: {
              style: {
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(255,255,255,0.95) 100%)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                color: '#7c3aed',
              },
              iconTheme: {
                primary: '#8b5cf6',
                secondary: '#ffffff',
              },
            },
          }}
        />

        {/* Main Content Area */}
        <div className="flex flex-1 overflow-hidden">
          {/* Premium Sidebar */}
          <motion.div
            initial={{ width: sidebarExpanded ? 320 : 80 }}
            animate={{ width: sidebarExpanded ? 320 : 80 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
            className="relative bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl border-r border-violet-200/30 dark:border-violet-800/30 flex flex-col shadow-2xl shadow-violet-500/10"
          >
            <div className="absolute inset-0 bg-gradient-to-b from-violet-50/50 to-cyan-50/20 dark:from-violet-950/50 dark:to-cyan-950/20" />
            <div className="relative z-10">
              <Sidebar
                groups={groups.data || []}
                selectedGroup={selectedGroup}
                agents={agents.data || []}
                groupAgents={groupAgents.data || []}
                expanded={sidebarExpanded}
                currentView={currentView}
                onToggleExpanded={() => setSidebarExpanded(!sidebarExpanded)}
                onSelectGroup={setSelectedGroup}
                onCreateGroup={handleGroupCreate}
                onDeleteGroup={handleGroupDelete}
                onAddAgent={handleAddAgent}
                onRemoveAgent={handleRemoveAgent}
                onViewChange={setCurrentView}
              />
            </div>
          </motion.div>

          {/* Immersive Main Workspace */}
<div className="flex-1 flex flex-col min-w-0 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-violet-50/40 to-cyan-50/30 dark:from-slate-900/60 dark:via-violet-950/40 dark:to-cyan-950/30" />

            {currentView === 'chat' ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 flex-1 min-h-0"
              >
                <MainWorkspace
                  selectedGroup={selectedGroup}
                  agents={groupAgents.data || []}
                  messages={messages.data || []}
                  onSendMessage={handleSendMessage}
                  onStopGroupChain={stopGroupChain}
                  onUploadDocument={handleUploadDocument}
                  onOpenCommandPalette={() => setCommandPaletteOpen(true)}
                  onOpenSettings={() => setSettingsOpen(true)}
                  onOpenToolsManagement={() => setToolsManagementOpen(true)}
                  onOpenMcpManagement={() => setMcpManagementOpen(true)}
                  onOpenHelp={() => setHelpOpen(true)}
                  onOpenLogs={() => setLogsOpen(true)}
                />
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 flex flex-col h-full"
              >
                {/* Enhanced Agent Studio Header */}
                <div className="relative bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-violet-200/30 dark:border-violet-800/30 z-20">
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
                  <div className="relative px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-3">
                          <motion.div
                            className="w-3 h-3 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                            animate={{
                              scale: [1, 1.2, 1],
                              opacity: [0.8, 1, 0.8]
                            }}
                            transition={{
                              duration: 2,
                              repeat: Infinity,
                              ease: "easeInOut"
                            }}
                          />
                          <div>
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                              Agent Studio
                            </h1>
                            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                              Design, configure, and deploy AI agents
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        <motion.button
                          onClick={() => setCommandPaletteOpen(true)}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          className="flex items-center space-x-2 px-4 py-2 text-sm text-slate-600 dark:text-slate-300 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl border border-violet-200/30 dark:border-violet-800/30 hover:bg-violet-50/80 dark:hover:bg-violet-900/20 transition-all duration-200 shadow-sm"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                          <span className="font-medium">⌘K</span>
                        </motion.button>

                        <Menu as="div" className="relative z-[10000]">
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
                            <Menu.Items className="absolute right-0 top-full mt-2 w-56 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-violet-200/30 dark:border-violet-800/30 z-[9999]">
                              <div className="py-1">
                                <Menu.Item>
                                  {({ active }) => (
                                    <button
                                      onClick={() => setSettingsOpen(true)}
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
                                      onClick={() => setToolsManagementOpen(true)}
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
                                      onClick={() => setMcpManagementOpen(true)}
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
                                <Menu.Item>
                                  {({ active }) => (
                                    <button
                                      onClick={() => setLogsOpen(true)}
                                      className={`w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1 ${
                                        active
                                          ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                                          : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20'
                                      }`}
                                    >
                                      <div className="flex items-center space-x-2">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0-1.125-.504-1.125-1.125V11.25a9 9 0 00-9-9z" />
                                        </svg>
                                        <span>View Logs</span>
                                      </div>
                                    </button>
                                  )}
                                </Menu.Item>
                                <Menu.Item>
                                  {({ active }) => (
                                    <button
                                      onClick={() => setHelpOpen(true)}
                                      className={`w-full text-left px-4 py-3 text-sm transition-all duration-200 rounded-xl mx-2 my-1 ${
                                        active
                                          ? 'bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-900/30 dark:to-indigo-900/30 text-violet-700 dark:text-violet-300 shadow-sm'
                                          : 'text-slate-700 dark:text-slate-300 hover:bg-violet-50/50 dark:hover:bg-violet-900/20'
                                      }`}
                                    >
                                      <div className="flex items-center space-x-2">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span>Help & Documentation</span>
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
                  </div>
                </div>

                {/* Enhanced Agent Creation Content */}
                <div className="flex-1 overflow-hidden bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm relative z-0">
                  <EnhancedAgentCreationPanel onAgentCreated={() => loadData()} />
                </div>
              </motion.div>
            )}
          </div>
        </div>

      {/* Command Palette */}
      <AnimatePresence>
        {commandPaletteOpen && (
          <CommandPalette
            isOpen={commandPaletteOpen}
            onClose={() => setCommandPaletteOpen(false)}
            groups={groups.data || []}
            agents={agents.data || []}
            onSelectGroup={setSelectedGroup}
            onCreateGroup={handleGroupCreate}
          />
        )}
      </AnimatePresence>

      {/* Settings Panel */}
      <AnimatePresence>
        {settingsOpen && (
          <SettingsPanel
            isOpen={settingsOpen}
            onClose={() => setSettingsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Tools Management Panel */}
      <AnimatePresence>
        {toolsManagementOpen && (
          <ToolsManagementPanel
            isOpen={toolsManagementOpen}
            onClose={() => setToolsManagementOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* MCP Management Panel */}
      <AnimatePresence>
        {mcpManagementOpen && (
          <McpManagementPanel
            isOpen={mcpManagementOpen}
            onClose={() => setMcpManagementOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Help Panel */}
      <AnimatePresence>
        {helpOpen && (
          <div className="fixed inset-0 z-[70] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
              onClick={() => setHelpOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-[90vw] h-[85vh] max-w-7xl overflow-hidden"
            >
              <div className="absolute top-4 right-4 z-10">
                <button
                  onClick={() => setHelpOpen(false)}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-lg border border-gray-200 dark:border-gray-600 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <HelpPanel isVisible={helpOpen} />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Logs Panel */}
      <AnimatePresence>
        {logsOpen && (
          <ComprehensiveLogPanel
            isOpen={logsOpen}
            onClose={() => setLogsOpen(false)}
          />
        )}
      </AnimatePresence>
      </div>
      )}
    </ThemeProvider>
  );
}

export default App;