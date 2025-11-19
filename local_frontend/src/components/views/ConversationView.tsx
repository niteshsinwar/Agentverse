import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Group, Agent, Message } from '@/lib/types';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PaperAirplaneIcon,
  CommandLineIcon,
  UserIcon,
  CpuChipIcon,
  ClockIcon,
  DocumentTextIcon,
  ChartBarIcon,
  PaperClipIcon,
  DocumentIcon,
  ChatBubbleLeftRightIcon,
  StopIcon,
} from '@heroicons/react/24/outline';
import { DocumentsListPanel } from '../shared/DocumentsListPanel';
import { BrandLogo } from '../shared/BrandLogo';
import { BrandedCard, BrandedBadge, BrandedStatus } from '../shared/BrandedComponents';
import { useAppStore } from '@/lib/stores/app';
import { DEFAULT_SUPPORTED_FILE_FORMATS } from '@/lib/config';

interface ConversationViewProps {
  selectedGroup: Group | null;
  agents: Agent[];
  messages: Message[];
  onSendMessage: (agentId: string, message: string) => void;
  onStopGroupChain?: (groupId: string) => void;
  onUploadDocument?: (agentId: string, file: File, message?: string) => Promise<void>;
}

export const ConversationView: React.FC<ConversationViewProps> = ({
  selectedGroup,
  agents,
  messages,
  onSendMessage,
  onStopGroupChain,
  onUploadDocument,
}) => {
  const supportedFileFormats = useAppStore((state) => state.supportedFileFormats);
  const [message, setMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const acceptedFileTypes = useMemo(() => {
    const formats = supportedFileFormats && supportedFileFormats.length > 0
      ? supportedFileFormats
      : Array.from(DEFAULT_SUPPORTED_FILE_FORMATS);

    return formats
      .map((ext) => {
        const normalized = ext.startsWith('.') ? ext : `.${ext}`;
        return normalized.toLowerCase();
      })
      .join(',');
  }, [supportedFileFormats]);

  // Listen for agent chain loading events from SSE
  useEffect(() => {
    const handleAgentChainLoading = () => {
      console.log('ConversationView: Agent chain loading triggered');
      setIsTyping(true);
      // Auto-clear loading after 30 seconds to prevent stuck state
      setTimeout(() => setIsTyping(false), 30000);
    };

    const handleAgentChainResponse = () => {
      console.log('ConversationView: Agent response received, clearing loading state');
      setIsTyping(false);
    };

    window.addEventListener('agentChainLoading', handleAgentChainLoading as EventListener);
    window.addEventListener('agentChainResponse', handleAgentChainResponse as EventListener);

    return () => {
      window.removeEventListener('agentChainLoading', handleAgentChainLoading as EventListener);
      window.removeEventListener('agentChainResponse', handleAgentChainResponse as EventListener);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    console.log('ConversationView: agents changed:', agents);
    if (agents.length > 0) {
      // Check if current selectedAgent is valid for this group
      const isSelectedAgentValid = agents.some(agent => agent.key === selectedAgent);

      if (!selectedAgent || !isSelectedAgentValid) {
        console.log('ConversationView: setting selectedAgent to:', agents[0].key, '(was:', selectedAgent, ')');
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
    if (selectedFile && message.trim() && selectedAgent && onUploadDocument) {
      try {
        setIsUploading(true);
        setIsTyping(true);
        console.log('ConversationView: uploading document with message to agent:', selectedAgent);

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
      console.log('ConversationView: sending message to agent:', selectedAgent, 'message:', message.trim());
      setIsTyping(true);
      await onSendMessage(selectedAgent, message.trim());
      setMessage('');
      setTimeout(() => setIsTyping(false), 2000);
    }
  };

  const handleStop = async () => {
    if (!selectedGroup || !onStopGroupChain) return;

    try {
      await onStopGroupChain(selectedGroup.id);
    } catch (error) {
      console.error('Failed to stop group chain:', error);
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
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-slate-50 via-sky-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-sky-950/30 dark:to-cyan-950/20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md mx-auto p-8"
        >
          <div className="flex justify-center mb-6">
            <BrandLogo variant="icon" size="lg" />
          </div>

          <h2 className="text-2xl font-bold brand-gradient bg-clip-text text-transparent mb-4">
            Welcome to AgentVerse
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            Create or select a workspace to start orchestrating your AI agents and unlock the power of multi-agent collaboration.
          </p>

          <div className="grid grid-cols-2 gap-4 text-sm text-slate-500 dark:text-slate-400">
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
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Tab Navigation */}
      <div className="flex space-x-1 border-b border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 px-6">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === 'chat'
              ? 'bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 border-t-2 border-x border-sky-500 dark:border-sky-400 -mb-px'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <ChatBubbleLeftRightIcon className="h-4 w-4" />
          <span>Chat</span>
        </button>
        <button
          onClick={() => {
            console.log('Documents tab clicked');
            setActiveTab('documents');
          }}
          className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === 'documents'
              ? 'bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 border-t-2 border-x border-sky-500 dark:border-sky-400 -mb-px'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <DocumentTextIcon className="h-4 w-4" />
          <span>Documents</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? (
          <div className="flex flex-col h-full">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 via-sky-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-sky-950/30 dark:to-cyan-950/20 min-h-0">
              <div className="max-w-4xl mx-auto">
                {messages.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-center h-full py-16"
                  >
                    <BrandedCard variant="glass" hover={true} className="text-center max-w-md mx-4">
                      <div className="flex justify-center mb-6">
                        <BrandLogo variant="icon" size="lg" />
                      </div>
                      <h3 className="text-xl font-bold brand-gradient bg-clip-text text-transparent mb-3">
                        Ready to Collaborate
                      </h3>
                      <p className="text-slate-500 dark:text-slate-400 font-medium">
                        Start a conversation with your AI agents in the AgentVerse. They're standing by to help with your tasks.
                      </p>
                    </BrandedCard>
                  </motion.div>
                ) : (
                  <div className="py-6 space-y-6">
                    <AnimatePresence>
                      {messages.filter(msg => {
                        // Filter out document analysis but keep upload notifications visible
                        if (msg.role === 'system' && (
                          msg.metadata?.message_type === 'document_analysis' ||
                          msg.metadata?.hidden_from_ui === true
                        )) {
                          return false;
                        }
                        return msg && msg.role;
                      }).map((msg, index) => {
                        const isUser = msg.role === 'user';
                        const isAgentThought = msg.role === 'agent_thought';
                        const agentInfo = !isUser ? getAgentInfo(msg.sender) : null;
                        const isProcessingSummary = msg.metadata?.message_type === 'document_processing_summary';
                        const processingSummary = msg.metadata?.processing_metadata;
                        const processingHighlight = processingSummary
                          ? (() => {
                              if (processingSummary.truncated && processingSummary.sampled_rows && processingSummary.row_count) {
                                return `Processed first ${processingSummary.sampled_rows} of approximately ${processingSummary.row_count} rows for embeddings.`;
                              }
                              if (!processingSummary.truncated && processingSummary.row_count) {
                                return `Processed ${processingSummary.row_count} rows for embeddings.`;
                              }
                              if (processingSummary.page_count) {
                                return `Detected ${processingSummary.page_count} pages.`;
                              }
                              return null;
                            })()
                          : null;

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
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                                  isUser
                                    ? 'brand-gradient text-white'
                                    : 'bg-gradient-to-br from-sky-50 to-slate-100 dark:from-sky-900/40 dark:to-slate-900/40 border border-sky-200/50 dark:border-sky-800/40'
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
                                    ? 'brand-gradient text-white rounded-t-2xl rounded-bl-2xl rounded-br-md shadow-lg'
                                    : isAgentThought
                                      ? 'bg-gradient-to-br from-slate-50/90 to-sky-50/90 dark:from-slate-900/35 dark:to-sky-900/35 text-slate-700 dark:text-slate-300 border border-slate-200/40 dark:border-sky-800/30 rounded-2xl shadow-lg shadow-sky-500/5'
                                      : 'bg-white/80 dark:bg-slate-800/85 backdrop-blur-xl text-slate-900 dark:text-slate-100 border border-slate-200/40 dark:border-sky-800/35 rounded-t-2xl rounded-br-2xl rounded-bl-md shadow-lg shadow-sky-500/10'
                                } px-4 py-3`}>
                                  {!isUser && agentInfo && (
                                    <div className={`flex items-center space-x-2 mb-2 pb-2 border-b ${
                                      isAgentThought
                                        ? 'border-slate-200/25 dark:border-sky-800/35'
                                        : 'border-slate-200/35 dark:border-sky-800/40'
                                    }`}>
                                      <BrandedBadge variant={isAgentThought ? 'secondary' : 'primary'} size="sm">
                                        {agentInfo.name}
                                      </BrandedBadge>
                                      <span className={`text-xs font-medium ${
                                        isAgentThought ? 'text-slate-500 dark:text-slate-400 italic' : 'text-slate-500 dark:text-slate-400'
                                      }`}>
                                        {isAgentThought ? 'Internal Reflection' : 'Agent Response'}
                                      </span>
                                    </div>
                                  )}

                                  {isProcessingSummary && (
                                    <div className="mb-3 rounded-lg bg-amber-50 dark:bg-amber-900/30 border border-amber-200/60 dark:border-amber-800/40 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                                      <div className="font-semibold mb-1 flex items-center space-x-2">
                                        <DocumentTextIcon className="w-4 h-4" />
                                        <span>Document processing summary</span>
                                      </div>
                                      {processingHighlight && (
                                        <p className="leading-snug">{processingHighlight}</p>
                                      )}
                                      {!processingHighlight && processingSummary?.notes && (
                                        <p className="leading-snug">{processingSummary.notes}</p>
                                      )}
                                    </div>
                                  )}

                                  <div className="text-left">
                                    <p
                                      className={`whitespace-pre-wrap leading-relaxed ${
                                        isAgentThought ? 'italic text-slate-600 dark:text-slate-300' : ''
                                      }`}
                                    >
                                      {msg.content}
                                    </p>
                                  </div>
                                </div>

                                <div className={`flex items-center mt-2 text-xs text-slate-500 dark:text-slate-400 ${
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
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-50 to-slate-100 dark:from-sky-900/40 dark:to-slate-900/40 border border-sky-200/50 dark:border-sky-800/40 flex items-center justify-center shadow-lg">
                              <BrandedStatus status="thinking" size="sm" />
                            </div>

                            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl border border-slate-200/35 dark:border-sky-800/35 rounded-t-2xl rounded-br-2xl rounded-bl-md px-4 py-3 shadow-lg shadow-sky-500/10">
                              <div className="flex items-center space-x-1">
                                <div className="w-2 h-2 bg-gradient-to-r from-sky-500 to-cyan-500 rounded-full animate-bounce" />
                                <div className="w-2 h-2 bg-gradient-to-r from-sky-500 to-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                <div className="w-2 h-2 bg-gradient-to-r from-sky-500 to-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                <span className="ml-2 text-sm text-slate-600 dark:text-slate-400 font-medium">Agent is thinking...</span>
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
            <div className="relative border-t border-slate-200/35 dark:border-sky-900/35 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl shadow-lg shadow-sky-500/5">
              <div className="absolute inset-0 brand-gradient-soft opacity-70" />
              <div className="relative max-w-4xl mx-auto p-6">
                {agents.length === 0 ? (
                  <BrandedCard variant="glass" className="text-center py-6">
                    <div className="flex justify-center mb-4">
                      <BrandLogo variant="icon" size="md" />
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mb-2">
                      No agents available in this workspace
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-500">
                      Add agents from the sidebar to start chatting
                    </p>
                  </BrandedCard>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Agent Selector */}
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                        Send to:
                      </span>
                      <div className="flex-1 max-w-md">
                        <select
                          value={selectedAgent}
                          onChange={(e) => setSelectedAgent(e.target.value)}
                          className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
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
                      <div className="flex items-center justify-between p-3 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800 rounded-xl">
                        <div className="flex items-center space-x-3">
                          <DocumentIcon className="w-5 h-5 text-sky-600 dark:text-sky-400" />
                          <div>
                            <p className="text-sm font-medium text-sky-900 dark:text-sky-100">
                              {selectedFile.name}
                            </p>
                            <p className="text-xs text-sky-600 dark:text-sky-400">
                              {(selectedFile.size / 1024).toFixed(1)} KB • Will upload when you send
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={removeFile}
                          className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
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
                          placeholder={selectedFile ? "Type a message about your document..." : "Type your message to the agent..."}
                          rows={3}
                          className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none transition-all"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                              handleSubmit(e);
                            }
                          }}
                        />
                        <div className="absolute bottom-3 right-3 text-xs text-slate-400">
                          {selectedFile ? "⌘↵ to upload & send" : "⌘↵ to send"}
                        </div>
                      </div>

                      {/* File Upload Input (Hidden) */}
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileSelect}
                        accept={acceptedFileTypes}
                        className="hidden"
                      />

                      {/* File Upload Button */}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={!selectedAgent}
                        className="p-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-2xl hover:bg-slate-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all transform hover:scale-105 active:scale-95"
                        title="Upload document"
                      >
                        <PaperClipIcon className="w-5 h-5" />
                      </button>

                      <button
                        type="submit"
                        disabled={!message.trim() || !selectedAgent || isTyping || isUploading}
                        className="px-6 py-3 brand-gradient text-white rounded-2xl hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 min-w-[80px]"
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

                      {/* Stop Button */}
                      <button
                        type="button"
                        onClick={handleStop}
                        disabled={!selectedGroup || !onStopGroupChain}
                        className="p-3 bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 rounded-2xl hover:bg-red-200 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all transform hover:scale-105 active:scale-95"
                        title="Stop agent chain"
                      >
                        <StopIcon className="w-5 h-5" />
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
