import React, { useState, useRef, useEffect } from 'react';
import { Group, Agent, Message } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PaperAirplaneIcon,
  CommandLineIcon,
  UserIcon,
  CpuChipIcon,
  ClockIcon,
  DocumentTextIcon,
  BoltIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  PaperClipIcon,
  DocumentIcon,
  CodeBracketIcon,
  ServerIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';
import { DocumentsListPanel } from './DocumentsListPanel';

interface MainWorkspaceProps {
  selectedGroup: Group | null;
  agents: Agent[];
  messages: Message[];
  onSendMessage: (agentId: string, message: string) => void;
  onOpenCommandPalette: () => void;
  onUploadDocument?: (agentId: string, file: File, message?: string) => Promise<void>;
  onOpenSettings?: () => void;
  onOpenToolsManagement?: () => void;
  onOpenMcpManagement?: () => void;
}

export const MainWorkspace: React.FC<MainWorkspaceProps> = ({
  selectedGroup,
  agents,
  messages,
  onSendMessage,
  onOpenCommandPalette,
  onUploadDocument,
  onOpenSettings,
  onOpenToolsManagement,
  onOpenMcpManagement,
}) => {
  const [message, setMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    console.log('MainWorkspace: agents changed:', agents);
    if (agents.length > 0) {
      // Check if current selectedAgent is valid for this group
      const isSelectedAgentValid = agents.some(agent => agent.key === selectedAgent);

      if (!selectedAgent || !isSelectedAgentValid) {
        console.log('MainWorkspace: setting selectedAgent to:', agents[0].key, '(was:', selectedAgent, ')');
        setSelectedAgent(agents[0].key);
      }
    } else {
      // No agents available, clear selection
      setSelectedAgent('');
    }
  }, [agents]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // If both message and file are present, upload document with message
    if (selectedFile && selectedAgent && onUploadDocument) {
      try {
        setIsUploading(true);
        setIsTyping(true);
        console.log('MainWorkspace: uploading document with message to agent:', selectedAgent);

        // Upload document with message context
        await onUploadDocument(selectedAgent, selectedFile, message.trim());

        // Clear both message and file after successful upload
        setMessage('');
        setSelectedFile(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } catch (error) {
        console.error('Document upload failed:', error);
      } finally {
        setIsUploading(false);
        setTimeout(() => setIsTyping(false), 2000);
      }
    }
    // If only message (no file), send regular message
    else if (message.trim() && selectedAgent && !selectedFile) {
      console.log('MainWorkspace: sending message to agent:', selectedAgent, 'message:', message.trim());
      setIsTyping(true);
      await onSendMessage(selectedAgent, message.trim());
      setMessage('');
      setTimeout(() => setIsTyping(false), 2000);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };


  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getAgentInfo = (agentKey: string) => {
    return agents.find(a => a.key === agentKey);
  };

  if (!selectedGroup) {
    return (
      <div className="flex flex-col h-full bg-white dark:bg-gray-900">
        {/* Header with Global Settings - Always visible */}
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-gray-400 rounded-full" />
                  <div>
                    <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                      Agentic Platform
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      No workspace selected
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={onOpenCommandPalette}
                  className="flex items-center space-x-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <CommandLineIcon className="w-4 h-4" />
                  <span>⌘K</span>
                </button>

                <Menu as="div" className="relative">
                  <Menu.Button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                    <Cog6ToothIcon className="w-5 h-5" />
                  </Menu.Button>
                  <Transition
                    enter="transition duration-100 ease-out"
                    enterFrom="transform scale-95 opacity-0"
                    enterTo="transform scale-100 opacity-100"
                    leave="transition duration-75 ease-in"
                    leaveFrom="transform scale-100 opacity-100"
                    leaveTo="transform scale-95 opacity-0"
                  >
                    <Menu.Items className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                      <div className="py-1">
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={onOpenSettings}
                              className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                                active
                                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                  : 'text-gray-700 dark:text-gray-300'
                              }`}
                            >
                              <div className="flex items-center space-x-2">
                                <Cog6ToothIcon className="w-4 h-4" />
                                <span>Application Settings</span>
                              </div>
                            </button>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={onOpenToolsManagement}
                              className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                                active
                                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                  : 'text-gray-700 dark:text-gray-300'
                              }`}
                            >
                              <div className="flex items-center space-x-2">
                                <CodeBracketIcon className="w-4 h-4" />
                                <span>Manage Tools</span>
                              </div>
                            </button>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={onOpenMcpManagement}
                              className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                                active
                                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                  : 'text-gray-700 dark:text-gray-300'
                              }`}
                            >
                              <div className="flex items-center space-x-2">
                                <ServerIcon className="w-4 h-4" />
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
          </div>
        </div>

        {/* Welcome Content */}
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-md mx-auto p-8"
          >
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <BoltIcon className="w-8 h-8 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Welcome to Agentic Platform
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Create or select a workspace to start orchestrating your AI agents and unlock the power of multi-agent collaboration.
            </p>

            <div className="grid grid-cols-2 gap-4 text-sm text-gray-500 dark:text-gray-400">
              <div className="flex items-center space-x-2">
                <CpuChipIcon className="w-4 h-4" />
                <span>Multi-Agent Teams</span>
              </div>
              <div className="flex items-center space-x-2">
                <CommandLineIcon className="w-4 h-4" />
                <span>Command Palette</span>
              </div>
              <div className="flex items-center space-x-2">
                <ChartBarIcon className="w-4 h-4" />
                <span>Real-time Analytics</span>
              </div>
              <div className="flex items-center space-x-2">
                <DocumentTextIcon className="w-4 h-4" />
                <span>Smart Context</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="px-6 py-4 pb-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <div>
                  <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {selectedGroup.name}
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {agents.length} agent{agents.length !== 1 ? 's' : ''} active • {messages.length} messages
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={onOpenCommandPalette}
                className="flex items-center space-x-2 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                <CommandLineIcon className="w-4 h-4" />
                <span>⌘K</span>
              </button>

              <Menu as="div" className="relative">
                <Menu.Button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                  <Cog6ToothIcon className="w-5 h-5" />
                </Menu.Button>
                <Transition
                  enter="transition duration-100 ease-out"
                  enterFrom="transform scale-95 opacity-0"
                  enterTo="transform scale-100 opacity-100"
                  leave="transition duration-75 ease-in"
                  leaveFrom="transform scale-100 opacity-100"
                  leaveTo="transform scale-95 opacity-0"
                >
                  <Menu.Items className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                    <div className="py-1">
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={onOpenSettings}
                            className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                              active
                                ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                : 'text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            <div className="flex items-center space-x-2">
                              <Cog6ToothIcon className="w-4 h-4" />
                              <span>Application Settings</span>
                            </div>
                          </button>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={onOpenToolsManagement}
                            className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                              active
                                ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                : 'text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            <div className="flex items-center space-x-2">
                              <CodeBracketIcon className="w-4 h-4" />
                              <span>Manage Tools</span>
                            </div>
                          </button>
                        )}
                      </Menu.Item>
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={onOpenMcpManagement}
                            className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                              active
                                ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                : 'text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            <div className="flex items-center space-x-2">
                              <ServerIcon className="w-4 h-4" />
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
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 px-6">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'chat'
                ? 'bg-gray-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <ChatBubbleLeftRightIcon className="h-4 w-4" />
            <span>Chat</span>
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === 'documents'
                ? 'bg-gray-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400 border-b-2 border-blue-600'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <DocumentTextIcon className="h-4 w-4" />
            <span>Documents</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? (
          <div className="flex flex-col h-full">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
              <div className="max-w-4xl mx-auto">
                {messages.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-center h-full py-16"
                  >
                    <div className="text-center">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                        <CpuChipIcon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        Ready to Collaborate
                      </h3>
                      <p className="text-gray-500 dark:text-gray-400 max-w-md">
                        Start a conversation with your AI agents. They're standing by to help with your tasks.
                      </p>
                    </div>
                  </motion.div>
                ) : (
                  <div className="py-6 space-y-6">
                    <AnimatePresence>
                      {messages.map((msg, index) => {
                        const isUser = msg.role === 'user';
                        const agentInfo = !isUser ? getAgentInfo(msg.sender) : null;

                        return (
                          <motion.div
                            key={msg.id || index}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -20, scale: 0.95 }}
                            transition={{ duration: 0.3 }}
                            className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-6`}
                          >
                            <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : ''} space-x-3`}>
                              {/* Avatar */}
                              <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                                  isUser
                                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                                    : 'bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800'
                                }`}>
                                  {isUser ? (
                                    <UserIcon className="w-5 h-5" />
                                  ) : (
                                    <span className="text-lg">{agentInfo?.emoji || '🤖'}</span>
                                  )}
                                </div>
                              </div>

                              {/* Message Content */}
                              <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
                                <div className={`inline-block max-w-full ${
                                  isUser
                                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-t-2xl rounded-bl-2xl rounded-br-md'
                                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700 rounded-t-2xl rounded-br-2xl rounded-bl-md shadow-sm'
                                } px-4 py-3`}>
                                  {!isUser && agentInfo && (
                                    <div className="flex items-center space-x-2 mb-2 pb-2 border-b border-gray-100 dark:border-gray-700">
                                      <span className="text-sm font-semibold text-purple-600 dark:text-purple-400">
                                        {agentInfo.name}
                                      </span>
                                      <span className="text-xs text-gray-500 dark:text-gray-400">
                                        Agent Response
                                      </span>
                                    </div>
                                  )}

                                  <div className="text-left">
                                    <p className="whitespace-pre-wrap leading-relaxed">
                                      {msg.content}
                                    </p>
                                  </div>
                                </div>

                                <div className={`flex items-center mt-2 text-xs text-gray-500 dark:text-gray-400 ${
                                  isUser ? 'justify-end' : ''
                                }`}>
                                  <ClockIcon className="w-3 h-3 mr-1" />
                                  {formatTimestamp(msg.created_at)}
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </AnimatePresence>

                    {/* Typing Indicator */}
                    <AnimatePresence>
                      {isTyping && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="flex justify-start px-6"
                        >
                          <div className="flex space-x-3 max-w-3xl">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                              <CpuChipIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                            </div>

                            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-t-2xl rounded-br-2xl rounded-bl-md px-4 py-3 shadow-sm">
                              <div className="flex items-center space-x-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">Agent is thinking...</span>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
            </div>

            {/* Input Area - only show in chat tab */}
            <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div className="max-w-4xl mx-auto p-6">
                {agents.length === 0 ? (
                  <div className="text-center py-6">
                    <CpuChipIcon className="w-8 h-8 mx-auto mb-3 text-gray-400" />
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      No agents available in this workspace
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      Add agents from the sidebar to start chatting
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Agent Selector */}
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Send to:
                      </span>
                      <div className="flex-1 max-w-md">
                        <select
                          value={selectedAgent}
                          onChange={(e) => setSelectedAgent(e.target.value)}
                          className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        >
                          {agents.map((agent) => (
                            <option key={agent.key} value={agent.key}>
                              {agent.emoji} {agent.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* File Preview Section */}
                    {selectedFile && (
                      <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                        <div className="flex items-center space-x-3">
                          <DocumentIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                          <div>
                            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                              {selectedFile.name}
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-400">
                              {(selectedFile.size / 1024).toFixed(1)} KB • Will upload when you send
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={removeFile}
                          className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                          title="Remove file"
                        >
                          ✕
                        </button>
                      </div>
                    )}

                    {/* Message Input */}
                    <div className="flex space-x-3">
                      <div className="flex-1 relative">
                        <textarea
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          placeholder={selectedFile ? "Add a message for your document (optional)..." : "Type your message to the agent..."}
                          rows={3}
                          className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-all"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                              handleSubmit(e);
                            }
                          }}
                        />
                        <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                          {selectedFile ? "⌘↵ to upload & send" : "⌘↵ to send"}
                        </div>
                      </div>

                      {/* File Upload Input (Hidden) */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileSelect}
                        accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx,.xls,.png"
                        className="hidden"
                      />

                      {/* File Upload Button */}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={!selectedAgent}
                        className="p-3 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-2xl hover:bg-gray-200 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all transform hover:scale-105 active:scale-95"
                        title="Upload document"
                      >
                        <PaperClipIcon className="w-5 h-5" />
                      </button>

                      <button
                        type="submit"
                        disabled={(!message.trim() && !selectedFile) || !selectedAgent || isTyping || isUploading}
                        className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-2xl hover:from-blue-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 min-w-[80px]"
                        title={selectedFile ? "Send message and upload document" : "Send message"}
                      >
                        {isUploading ? (
                          <div className="flex items-center space-x-2">
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-sm">Uploading...</span>
                          </div>
                        ) : isTyping ? (
                          <div className="flex items-center space-x-2">
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span className="text-sm">Sending...</span>
                          </div>
                        ) : selectedFile ? (
                          <div className="flex items-center space-x-2">
                            <DocumentIcon className="w-4 h-4" />
                            <PaperAirplaneIcon className="w-4 h-4" />
                          </div>
                        ) : (
                          <PaperAirplaneIcon className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Documents Tab */
          <DocumentsListPanel
            groupId={selectedGroup.id}
            agents={agents}
            isVisible={activeTab === 'documents'}
          />
        )}
      </div>
    </div>
  );
};