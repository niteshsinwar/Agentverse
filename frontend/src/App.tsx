import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '@/lib/stores/app';
import { useAuthStore } from '@/lib/stores/auth';
import { useGroupsStore } from '@/lib/stores/groups';
import { useAgentsStore } from '@/lib/stores/agents';
import { Toaster, toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cog6ToothIcon,
  CodeBracketIcon,
  ServerIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

// Modern, enterprise-grade components
import { Sidebar } from './components/views/Sidebar';
import { ConversationView } from './components/views/ConversationView';
import { CommandPalette } from './components/modals/CommandPalette';
import { AgentStudio } from './components/views/AgentStudio';
import { AgentManagementPanel } from './components/modals/AgentManagementPanel';
import { SettingsPanel } from './components/modals/SettingsPanel';
import { ToolsManagementPanel } from './components/modals/ToolsManagementPanel';
import { McpManagementPanel } from './components/modals/McpManagementPanel';
import { HelpPanel } from './components/modals/HelpPanel';
import { ComprehensiveLogPanel } from './components/modals/ComprehensiveLogPanel';
import { CommunityCenterPanel } from './components/modals/CommunityCenterPanel';
import { AuthenticationPortal } from './components/modals/AuthenticationPortal';
import { AdminView } from './components/views/AdminView';
import { AnimatedSplashScreen } from './components/shared/AnimatedSplashScreen';
import { AppHeader, HeaderMenuItem } from './components/core/AppHeader';
import { AppFooter } from './components/core/AppFooter';
import { settingsApi } from '@/lib/api';

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
    communityCenterOpen,
    setCommunityCenterOpen,
    appLoading,
    setAppLoading,
    showSplash,
    setShowSplash,
    setAppReady,
    initialLoadCompleted: storeInitialLoadCompleted,
    setInitialLoadCompleted,
    theme,
    setSupportedFileFormats,
  } = useAppStore();

  // Auth Store
  const {
    currentUser,
    authPortalOpen,
    setAuthPortalOpen,
    isAdmin,
    logout,
  } = useAuthStore();

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

  // Local state for Agent Management Modal
  const [agentManagementOpen, setAgentManagementOpen] = useState(false);
  const [agentToEdit, setAgentToEdit] = useState<any>(null);

  // Admin tab state
  const [adminTab, setAdminTab] = useState<'overview' | 'users' | 'groups' | 'resources' | 'settings'>('overview');

  const initialLoadCompleted = useRef(storeInitialLoadCompleted);

  // Unified header menu items for all views
  const headerMenuItems: HeaderMenuItem[] = [
    {
      key: 'settings',
      label: 'Application Settings',
      icon: <Cog6ToothIcon className="w-4 h-4" />,
      onClick: () => setSettingsOpen(true),
    },
    {
      key: 'tools',
      label: 'Manage Tools',
      icon: <CodeBracketIcon className="w-4 h-4" />,
      onClick: () => setToolsManagementOpen(true),
    },
    {
      key: 'mcp',
      label: 'Manage MCP Servers',
      icon: <ServerIcon className="w-4 h-4" />,
      onClick: () => setMcpManagementOpen(true),
    },
    {
      key: 'logs',
      label: 'View Logs',
      icon: <DocumentTextIcon className="w-4 h-4" />,
      onClick: () => setLogsOpen(true),
    },
  ];

  // Enhanced loading with better error handling
  const loadData = async (isInitialLoad = false) => {
    try {
      setAppLoading(true);

      const settingsPromise = settingsApi.getSettings()
        .then((response) => {
          const formats = response?.settings?.supported_file_formats;
          if (Array.isArray(formats) && formats.length > 0) {
            setSupportedFileFormats(formats);
          }
        })
        .catch((error) => {
          console.error('Failed to load settings:', error);
        });

      await Promise.all([
        loadGroups(),
        loadAgents(),
        settingsPromise,
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
    
    // Clear auth seen flag on fresh page load (for demo)
    sessionStorage.removeItem('agentverse_auth_seen');
  }, []);

  // Apply theme to document element
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark');
    
    if (theme === 'system' || theme === 'auto') {
      // Use system preference
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.add(isDark ? 'dark' : 'light');
    } else {
      // Use explicit theme
      root.classList.add(theme);
    }
  }, [theme]);

  // Redirect non-admin users away from admin view
  useEffect(() => {
    if (currentView === 'admin' && !isAdmin()) {
      setCurrentView('chat');
      if (currentUser) {
        // Only show error if user is logged in but not admin
        toast.error('Access denied: Admin privileges required');
      }
    }
  }, [currentView, currentUser, isAdmin, setCurrentView]);

  // Handle splash screen completion and show auth portal
  const handleSplashComplete = () => {
    setShowSplash(false);
    
    // Show auth portal after splash if not logged in
    const hasSeenAuth = sessionStorage.getItem('agentverse_auth_seen');
    if (!hasSeenAuth && !currentUser) {
      setTimeout(() => {
        setAuthPortalOpen(true);
        sessionStorage.setItem('agentverse_auth_seen', 'true');
      }, 300);
    }
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
    <>
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
                isAdmin={isAdmin()}
                adminTab={adminTab}
                onToggleExpanded={() => setSidebarExpanded(!sidebarExpanded)}
                onSelectGroup={setSelectedGroup}
                onCreateGroup={handleGroupCreate}
                onDeleteGroup={handleGroupDelete}
                onAddAgent={handleAddAgent}
                onRemoveAgent={handleRemoveAgent}
                onViewChange={setCurrentView}
                onAdminTabChange={setAdminTab}
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
                className="relative z-10 flex flex-col h-full"
              >
                {/* Unified Header for Conversation View */}
                <AppHeader
                  title={selectedGroup ? selectedGroup.name : "AgentVerse"}
                  subtitle={selectedGroup ? `${groupAgents.data?.length || 0} agent${(groupAgents.data?.length || 0) !== 1 ? 's' : ''} active • ${messages.data?.length || 0} messages` : "No workspace selected"}
                  leading={
                    <motion.div
                      className="w-3 h-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full"
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
                  }
                  onCommandPalette={() => setCommandPaletteOpen(true)}
                  menuItems={headerMenuItems}
                  rightContent={
                    currentUser ? (
                      <div className="flex items-center space-x-3">
                        {/* Account Type Badge */}
                        <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                          currentUser.accountType === 'enterprise'
                            ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/30 dark:to-purple-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800'
                            : 'bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                        }`}>
                          {currentUser.accountType === 'enterprise' ? '🏢 Enterprise' : '👤 Individual'}
                        </div>
                        
                        {/* Admin Badge */}
                        {currentUser.role === 'admin' && (
                          <div className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                            👑 Admin
                          </div>
                        )}
                        
                        {/* User Profile with Logout */}
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-2 px-3 py-2 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-300 dark:border-gray-600 shadow-sm">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-md">
                              {currentUser.name.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-sm font-semibold text-gray-800 dark:text-gray-200 max-w-[120px] truncate">
                              {currentUser.name}
                            </span>
                          </div>
                          
                          {/* Logout Button */}
                          <button
                            onClick={() => {
                              logout();
                              toast.success('Logged out successfully');
                            }}
                            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl text-sm font-bold transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center space-x-1"
                          >
                            <span>🚪</span>
                            <span>Logout</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setAuthPortalOpen(true)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg text-sm font-semibold transition-all"
                      >
                        Login
                      </button>
                    )
                  }
                  className="z-20"
                />

                {/* Conversation Content */}
                <ConversationView
                  selectedGroup={selectedGroup}
                  agents={groupAgents.data || []}
                  messages={messages.data || []}
                  onSendMessage={handleSendMessage}
                  onStopGroupChain={stopGroupChain}
                  onUploadDocument={handleUploadDocument}
                />
              </motion.div>
            ) : currentView === 'agent-management' ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 flex flex-col h-full"
              >
                {/* Enhanced Agent Studio Header */}
                <AppHeader
                  title="Agent Studio"
                  subtitle="Design, configure, and deploy AI agents"
                  leading={
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
                  }
                  onCommandPalette={() => setCommandPaletteOpen(true)}
                  menuItems={headerMenuItems}
                  rightContent={
                    currentUser ? (
                      <div className="flex items-center space-x-3">
                        {/* Account Type Badge */}
                        <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                          currentUser.accountType === 'enterprise'
                            ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/30 dark:to-purple-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800'
                            : 'bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                        }`}>
                          {currentUser.accountType === 'enterprise' ? '🏢 Enterprise' : '👤 Individual'}
                        </div>
                        
                        {/* Admin Badge */}
                        {currentUser.role === 'admin' && (
                          <div className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                            👑 Admin
                          </div>
                        )}
                        
                        {/* User Profile with Logout */}
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-2 px-3 py-2 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-300 dark:border-gray-600 shadow-sm">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-md">
                              {currentUser.name.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-sm font-semibold text-gray-800 dark:text-gray-200 max-w-[120px] truncate">
                              {currentUser.name}
                            </span>
                          </div>
                          
                          {/* Logout Button - More Prominent */}
                          <button
                            onClick={() => {
                              logout();
                              toast.success('Logged out successfully');
                            }}
                            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl text-sm font-bold transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center space-x-1"
                          >
                            <span>🚪</span>
                            <span>Logout</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setAuthPortalOpen(true)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg text-sm font-semibold transition-all"
                      >
                        Login
                      </button>
                    )
                  }
                  className="z-20"
                />

                {/* Agent Management Workspace */}
                <div className="flex-1 overflow-hidden bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm relative z-0">
                  <AgentStudio 
                    onCreateAgent={() => {
                      setAgentToEdit(null);
                      setAgentManagementOpen(true);
                    }}
                    onEditAgent={(agent) => {
                      setAgentToEdit(agent);
                      setAgentManagementOpen(true);
                    }}
                    onAgentDeleted={() => loadData()}
                  />
                </div>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 flex flex-col h-full"
              >
                {/* Admin Dashboard Header */}
                <AppHeader
                  title="👑 Admin Dashboard"
                  subtitle="Manage users, groups, and permissions"
                  leading={
                    <motion.div
                      className="w-3 h-3 bg-gradient-to-r from-amber-500 to-orange-600 rounded-full"
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
                  }
                  onCommandPalette={() => setCommandPaletteOpen(true)}
                  menuItems={headerMenuItems}
                  rightContent={
                    currentUser ? (
                      <div className="flex items-center space-x-3">
                        {/* Account Type Badge */}
                        <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${
                          currentUser.accountType === 'enterprise'
                            ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/30 dark:to-purple-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800'
                            : 'bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/30 dark:to-pink-900/30 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800'
                        }`}>
                          {currentUser.accountType === 'enterprise' ? '🏢 Enterprise' : '👤 Individual'}
                        </div>
                        
                        {/* Admin Badge */}
                        {currentUser.role === 'admin' && (
                          <div className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                            👑 Admin
                          </div>
                        )}
                        
                        {/* User Profile with Logout */}
                        <div className="flex items-center space-x-3">
                          <div className="flex items-center space-x-2 px-3 py-2 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-300 dark:border-gray-600 shadow-sm">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-md">
                              {currentUser.name.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-sm font-semibold text-gray-800 dark:text-gray-200 max-w-[120px] truncate">
                              {currentUser.name}
                            </span>
                          </div>
                          
                          {/* Logout Button */}
                          <button
                            onClick={() => {
                              logout();
                              toast.success('Logged out successfully');
                            }}
                            className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl text-sm font-bold transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center space-x-1"
                          >
                            <span>🚪</span>
                            <span>Logout</span>
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setAuthPortalOpen(true)}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg text-sm font-semibold transition-all"
                      >
                        Login
                      </button>
                    )
                  }
                  className="z-20"
                />

                {/* Admin View Content */}
                <div className="flex-1 overflow-hidden bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm relative z-0">
                  <AdminView adminTab={adminTab} onTabChange={setAdminTab} />
                </div>
              </motion.div>
            )}
          </div>
        </div>

        <AppFooter />

      {/* Agent Management Modal */}
      <AnimatePresence>
        {agentManagementOpen && (
          <AgentManagementPanel 
            isOpen={agentManagementOpen}
            onClose={() => {
              setAgentManagementOpen(false);
              setAgentToEdit(null);
            }}
            agentToEdit={agentToEdit}
            onAgentCreated={() => loadData()}
            onAgentUpdated={() => loadData()}
          />
        )}
      </AnimatePresence>

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
          <HelpPanel 
            isOpen={helpOpen} 
            onClose={() => setHelpOpen(false)} 
          />
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

      {/* Community Center Panel */}
      <AnimatePresence>
        {communityCenterOpen && (
          <CommunityCenterPanel
            isOpen={communityCenterOpen}
            onClose={() => setCommunityCenterOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Authentication Portal */}
      <AnimatePresence>
        {authPortalOpen && (
          <AuthenticationPortal
            isOpen={authPortalOpen}
            onClose={() => setAuthPortalOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Authentication Portal */}
      <AuthenticationPortal
        isOpen={authPortalOpen}
        onClose={() => setAuthPortalOpen(false)}
      />
      </div>
      )}
    </>
  );
}

export default App;
