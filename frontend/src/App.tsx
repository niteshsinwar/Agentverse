import { useState, useEffect } from 'react';
import { Group, Agent, Message } from './types';
import { apiService } from './services/api';
import { Toaster, toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './contexts/ThemeContext';

// Modern, enterprise-grade components
import { Sidebar } from './components/Sidebar';
import { MainWorkspace } from './components/MainWorkspace';
import { LoadingOverlay } from './components/LoadingOverlay';
import { CommandPalette } from './components/CommandPalette';
import { EnhancedAgentCreationPanel } from './components/EnhancedAgentCreationPanel';
import { SettingsPanel } from './components/SettingsPanel';
import { ToolsManagementPanel } from './components/ToolsManagementPanel';
import { McpManagementPanel } from './components/McpManagementPanel';

import './App.css';

function App() {
  // State management
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [groupAgents, setGroupAgents] = useState<Agent[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [toolsManagementOpen, setToolsManagementOpen] = useState(false);
  const [mcpManagementOpen, setMcpManagementOpen] = useState(false);
  const [currentView, setCurrentView] = useState<'chat' | 'agent-management'>('chat');

  // Enhanced loading with better error handling
  const loadData = async () => {
    try {
      setLoading(true);

      const [groupsData, agentsData] = await Promise.all([
        apiService.getGroups().catch(() => []),
        apiService.getAvailableAgents().catch(() => []),
      ]);

      setGroups(Array.isArray(groupsData) ? groupsData : []);
      setAgents(Array.isArray(agentsData) ? agentsData : []);

      // Auto-select first group or create a demo group
      if (Array.isArray(groupsData) && groupsData.length > 0) {
        setSelectedGroup(groupsData[0]);
      }

      toast.success('Platform initialized successfully');
    } catch (error) {
      console.error('Failed to load initial data:', error);
      toast.error('Failed to initialize platform');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Load group-specific data with retry logic
  useEffect(() => {
    if (!selectedGroup) return;

    const loadGroupData = async () => {
      try {
        const [groupAgentsData, messagesData] = await Promise.all([
          apiService.getGroupAgents(selectedGroup.id).catch(() => []),
          apiService.getGroupMessages(selectedGroup.id).catch(() => []),
        ]);
        
        console.log('App: API returned groupAgents for group', selectedGroup.id, ':', groupAgentsData);
        setGroupAgents(Array.isArray(groupAgentsData) ? groupAgentsData : []);
        setMessages(Array.isArray(messagesData) ? messagesData : []);
      } catch (error) {
        console.error('Failed to load group data:', error);
        toast.error(`Failed to load data for ${selectedGroup.name}`);
      }
    };

    loadGroupData();
  }, [selectedGroup]);

  // Set up SSE stream to refresh messages on every agent response
  useEffect(() => {
    if (!selectedGroup) return;

    const eventSource = apiService.createEventStream(selectedGroup.id);

    eventSource.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);

        // Refresh messages on agent responses (message events with agent role)
        if (data.type === 'message' && data.payload?.role === 'agent') {
          console.log('SSE: Agent response received, refreshing messages...');
          const newMessages = await apiService.getGroupMessages(selectedGroup.id);
          setMessages(Array.isArray(newMessages) ? newMessages : []);

          // Clear any existing loading state when agent responds
          window.dispatchEvent(new CustomEvent('agentChainResponse', {
            detail: { groupId: selectedGroup.id }
          }));

          // If the agent response contains @mentions for another agent (not @user), show loading
          const agentMentionMatch = data.payload?.content?.match(/@([A-Za-z0-9_\-]+)/);
          const hasAgentMention = agentMentionMatch && agentMentionMatch[1].toLowerCase() !== 'user';

          if (hasAgentMention) {
            // Small delay to show the response before loading next agent
            setTimeout(() => {
              window.dispatchEvent(new CustomEvent('agentChainLoading', {
                detail: { groupId: selectedGroup.id }
              }));
            }, 500);
          }
        }
      } catch (error) {
        console.error('Error processing SSE event:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
    };

    // Cleanup function to close SSE connection
    return () => {
      eventSource.close();
    };
  }, [selectedGroup]);

  // Enhanced group management
  const handleGroupCreate = async (name: string) => {
    try {
      const newGroup = await apiService.createGroup(name) as Group;
      setGroups([newGroup, ...groups]);
      setSelectedGroup(newGroup);
      toast.success(`Created group: ${name}`);
    } catch (error) {
      console.error('Failed to create group:', error);
      toast.error('Failed to create group');
    }
  };

  const handleGroupDelete = async (groupId: string) => {
    try {
      await apiService.deleteGroup(groupId);
      const newGroups = groups.filter(g => g.id !== groupId);
      setGroups(newGroups);
      
      if (selectedGroup?.id === groupId) {
        setSelectedGroup(newGroups[0] || null);
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
      await apiService.addAgentToGroup(selectedGroup.id, agentKey);
      const agent = agents.find(a => a.key === agentKey);
      if (agent) {
        setGroupAgents([...groupAgents, agent]);
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
      await apiService.removeAgentFromGroup(selectedGroup.id, agentKey);
      const agent = groupAgents.find(a => a.key === agentKey);
      setGroupAgents(groupAgents.filter(a => a.key !== agentKey));
      
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
      // Add user message optimistically
      const userMessage: Message = {
        id: Date.now(),
        group_id: selectedGroup.id,
        sender: 'user',
        role: 'user',
        content: message,
        created_at: Date.now() / 1000
      };
      
      setMessages(prev => [...prev, userMessage]);
      
      await apiService.sendMessage(selectedGroup.id, agentId, message);

      // SSE stream will automatically refresh messages when agent responds
      
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleUploadDocument = async (agentId: string, file: File, message: string = '') => {
    if (!selectedGroup) return;
    
    try {
      await apiService.uploadDocument(selectedGroup.id, agentId, file, message);
      toast.success(`Document "${file.name}" uploaded successfully`);
      
      // Refresh messages to show the upload and any processing results
      setTimeout(async () => {
        try {
          const updatedMessages = await apiService.getGroupMessages(selectedGroup.id);
          setMessages(Array.isArray(updatedMessages) ? updatedMessages : []);
        } catch (error) {
          console.error('Failed to refresh messages after upload:', error);
        }
      }, 2000); // Longer timeout to allow document processing
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

  if (loading) {
    return (
      <ThemeProvider>
        <LoadingOverlay />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#374151',
            border: '1px solid #e5e7eb',
            borderRadius: '12px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          },
        }}
      />
      
      {/* Enhanced Sidebar */}
      <motion.div
        initial={{ width: sidebarExpanded ? 320 : 80 }}
        animate={{ width: sidebarExpanded ? 320 : 80 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col shadow-xl"
      >
        <Sidebar
          groups={groups}
          selectedGroup={selectedGroup}
          agents={agents}
          groupAgents={groupAgents}
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
      </motion.div>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        {currentView === 'chat' ? (
          <MainWorkspace
            selectedGroup={selectedGroup}
            agents={groupAgents}
            messages={messages}
            onSendMessage={handleSendMessage}
            onUploadDocument={handleUploadDocument}
            onOpenCommandPalette={() => setCommandPaletteOpen(true)}
            onOpenSettings={() => setSettingsOpen(true)}
            onOpenToolsManagement={() => setToolsManagementOpen(true)}
            onOpenMcpManagement={() => setMcpManagementOpen(true)}
          />
        ) : (
          <div className="flex flex-col h-full">
            {/* Global Header for Agent Creation */}
            <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      <div>
                        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                          Agent Management
                        </h1>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          Create and configure AI agents
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => setCommandPaletteOpen(true)}
                      className="flex items-center space-x-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3" />
                      </svg>
                      <span>⌘K</span>
                    </button>

                    <div className="relative group">
                      <button
                        onClick={() => setSettingsOpen(true)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        title="Settings"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Agent Creation Content */}
            <div className="flex-1 overflow-hidden">
              <EnhancedAgentCreationPanel onAgentCreated={() => loadData()} />
            </div>
          </div>
        )}
      </div>

      {/* Command Palette */}
      <AnimatePresence>
        {commandPaletteOpen && (
          <CommandPalette
            isOpen={commandPaletteOpen}
            onClose={() => setCommandPaletteOpen(false)}
            groups={groups}
            agents={agents}
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
      </div>
    </ThemeProvider>
  );
}

export default App;