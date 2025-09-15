import React, { useState, useRef, useEffect } from 'react';
import { Group, Agent, Message } from '../types';
import { Send, Bot, User } from 'lucide-react';
import { ChatBubbleLeftRightIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { DocumentsListPanel } from './DocumentsListPanel';

interface ChatInterfaceProps {
  group: Group;
  agents: Agent[];
  messages: Message[];
  onSendMessage: (agentId: string, message: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  group,
  agents,
  messages,
  onSendMessage,
}) => {
  const [message, setMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (agents.length > 0 && !selectedAgent) {
      setSelectedAgent(agents[0].key);
    }
  }, [agents, selectedAgent]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && selectedAgent) {
      onSendMessage(selectedAgent, message.trim());
      setMessage('');
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getAgentInfo = (agentKey: string) => {
    return agents.find(a => a.key === agentKey);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="p-4 pb-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {group.name}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Multi-agent conversation workspace
          </p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 px-4">
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
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <h3 className="font-medium mb-2">No messages yet</h3>
                  <p className="text-sm">Start a conversation with your agents below</p>
                </div>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  const agentInfo = !isUser ? getAgentInfo(msg.sender) : null;

                  return (
                    <div
                      key={msg.id}
                      className="flex gap-3"
                    >
                      {!isUser && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                          <span className="text-sm">{agentInfo?.emoji || '🤖'}</span>
                        </div>
                      )}

                      <div className="flex-1">
                        <div className={`max-w-[70%] ${isUser ? 'ml-auto' : ''}`}>
                          <div className={`p-3 rounded-lg ${
                            isUser
                              ? 'bg-blue-600 text-white'
                              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                          }`}>
                            {!isUser && agentInfo && (
                              <div className="text-xs font-medium mb-1 opacity-75">
                                {agentInfo.name}
                              </div>
                            )}
                            <div className="whitespace-pre-wrap text-left">{msg.content}</div>
                          </div>

                          <div className={`text-xs text-gray-500 dark:text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
                            {formatTimestamp(msg.created_at)}
                          </div>
                        </div>
                      </div>

                      {isUser && (
                        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-blue-600 text-white">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form - only show in chat tab */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              {agents.length === 0 ? (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                  <p className="text-sm">No agents available in this group</p>
                  <p className="text-xs">Add agents to start chatting</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-3">
                  {/* Agent Selector */}
                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Send to:
                    </label>
                    <select
                      value={selectedAgent}
                      onChange={(e) => setSelectedAgent(e.target.value)}
                      className="flex-1 px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {agents.map((agent) => (
                        <option key={agent.key} value={agent.key}>
                          {agent.emoji} {agent.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Message Input */}
                  <div className="flex gap-2">
                    <textarea
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Type your message to the agent..."
                      rows={3}
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                          handleSubmit(e);
                        }
                      }}
                    />
                    <button
                      type="submit"
                      disabled={!message.trim() || !selectedAgent}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Press Cmd/Ctrl + Enter to send
                  </div>
                </form>
              )}
            </div>
          </div>
        ) : (
          /* Documents Tab */
          <DocumentsListPanel
            groupId={group.id}
            agents={agents}
            isVisible={activeTab === 'documents'}
          />
        )}
      </div>
    </div>
  );
};