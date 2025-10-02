/**
 * Groups Store
 * State management for groups, messages, and documents
 */

import { create } from 'zustand';
import { groupsApi } from '../api/endpoints/groups.api';
import { notificationService } from '../../services/notificationService';
import type { Group, Agent, Message, Document } from '../api/types/entities';
import type { AsyncState } from '../types/common';

export interface GroupsState {
  // Groups
  groups: AsyncState<Group[]>;
  selectedGroup: Group | null;

  // Group Agents
  groupAgents: AsyncState<Agent[]>;

  // Messages
  messages: AsyncState<Message[]>;

  // Documents
  documents: AsyncState<Document[]>;

  // SSE Connection
  eventSource: EventSource | null;
}

export interface GroupsActions {
  // Group Actions
  loadGroups: () => Promise<void>;
  createGroup: (name: string) => Promise<Group>;
  deleteGroup: (groupId: string) => Promise<void>;
  setSelectedGroup: (group: Group | null) => Promise<void>;

  // Group Agent Actions
  loadGroupAgents: (groupId: string) => Promise<void>;
  addAgentToGroup: (groupId: string, agentKey: string) => Promise<void>;
  removeAgentFromGroup: (groupId: string, agentKey: string) => Promise<void>;

  // Message Actions
  loadMessages: (groupId: string) => Promise<void>;
  sendMessage: (groupId: string, agentId: string, message: string) => Promise<void>;
  addMessage: (message: Message) => void;
  stopGroupChain: (groupId: string) => Promise<void>;

  // Document Actions
  loadDocuments: (groupId: string) => Promise<void>;
  uploadDocument: (
    groupId: string,
    file: File,
    agentId: string,
    message?: string,
    onProgress?: (progress: number) => void
  ) => Promise<Document>;

  // SSE Actions
  connectEventStream: (groupId: string) => void;
  disconnectEventStream: () => void;

  // Utility Actions
  clearGroupData: () => void;
  reset: () => void;
}

export type GroupsStore = GroupsState & GroupsActions;

const createAsyncState = <T>(initialData: T | null = null): AsyncState<T> => ({
  data: initialData,
  status: 'idle',
  error: null,
  lastUpdated: undefined,
});

const initialState: GroupsState = {
  groups: createAsyncState<Group[]>([]),
  selectedGroup: null,
  groupAgents: createAsyncState<Agent[]>([]),
  messages: createAsyncState<Message[]>([]),
  documents: createAsyncState<Document[]>([]),
  eventSource: null,
};

export const useGroupsStore = create<GroupsStore>((set, get) => ({
  ...initialState,

  // Group Actions
  loadGroups: async () => {
    set((state) => ({
      groups: { ...state.groups, status: 'loading', error: null },
    }));

    try {
      const groups = await groupsApi.getGroups();
      set(() => ({
        groups: {
          data: Array.isArray(groups) ? groups : [],
          status: 'success',
          error: null,
          lastUpdated: Date.now(),
        },
      }));
    } catch (error) {
      console.error('Failed to load groups:', error);
      set((state) => ({
        groups: {
          ...state.groups,
          status: 'error',
          error: error instanceof Error ? error.message : 'Failed to load groups',
        },
      }));
    }
  },

  createGroup: async (name: string) => {
    try {
      const newGroup = await groupsApi.createGroup({ name });

      set((state) => ({
        groups: {
          ...state.groups,
          data: state.groups.data ? [...state.groups.data, newGroup] : [newGroup],
        },
      }));

      return newGroup;
    } catch (error) {
      console.error('Failed to create group:', error);
      throw error;
    }
  },

  deleteGroup: async (groupId: string) => {
    try {
      await groupsApi.deleteGroup(groupId);

      const { selectedGroup } = get();

      set((state) => ({
        groups: {
          ...state.groups,
          data: state.groups.data?.filter(group => group.id !== groupId) || [],
        },
        selectedGroup: selectedGroup?.id === groupId ? null : selectedGroup,
      }));
    } catch (error) {
      console.error('Failed to delete group:', error);
      throw error;
    }
  },

  setSelectedGroup: async (group: Group | null) => {
    const { disconnectEventStream, connectEventStream, clearGroupData } = get();

    // Disconnect from previous group's event stream
    disconnectEventStream();

    // Clear previous group's data
    clearGroupData();

    set({ selectedGroup: group });

    if (group) {
      // Load group data
      await Promise.all([
        get().loadGroupAgents(group.id),
        get().loadMessages(group.id),
        get().loadDocuments(group.id),
      ]);

      // Connect to event stream
      connectEventStream(group.id);
    }
  },

  // Group Agent Actions
  loadGroupAgents: async (groupId: string) => {
    set((state) => ({
      groupAgents: { ...state.groupAgents, status: 'loading', error: null },
    }));

    try {
      const agents = await groupsApi.getGroupAgents(groupId);
      set(() => ({
        groupAgents: {
          data: Array.isArray(agents) ? agents : [],
          status: 'success',
          error: null,
          lastUpdated: Date.now(),
        },
      }));
    } catch (error) {
      console.error('Failed to load group agents:', error);
      set((state) => ({
        groupAgents: {
          ...state.groupAgents,
          status: 'error',
          error: error instanceof Error ? error.message : 'Failed to load agents',
        },
      }));
    }
  },

  addAgentToGroup: async (groupId: string, agentKey: string) => {
    try {
      await groupsApi.addAgentToGroup(groupId, agentKey);
      // Reload group agents
      await get().loadGroupAgents(groupId);
    } catch (error) {
      console.error('Failed to add agent to group:', error);
      throw error;
    }
  },

  removeAgentFromGroup: async (groupId: string, agentKey: string) => {
    try {
      await groupsApi.removeAgentFromGroup(groupId, agentKey);
      // Reload group agents
      await get().loadGroupAgents(groupId);
    } catch (error) {
      console.error('Failed to remove agent from group:', error);
      throw error;
    }
  },

  // Message Actions
  loadMessages: async (groupId: string) => {
    set((state) => ({
      messages: { ...state.messages, status: 'loading', error: null },
    }));

    try {
      const messages = await groupsApi.getGroupMessages(groupId);
      set(() => ({
        messages: {
          data: Array.isArray(messages) ? messages.filter(msg => msg && msg.role) : [],
          status: 'success',
          error: null,
          lastUpdated: Date.now(),
        },
      }));
    } catch (error) {
      console.error('Failed to load messages:', error);
      set((state) => ({
        messages: {
          ...state.messages,
          status: 'error',
          error: error instanceof Error ? error.message : 'Failed to load messages',
        },
      }));
    }
  },

  sendMessage: async (groupId: string, agentId: string, message: string) => {
    try {
      const response = await groupsApi.sendMessage(groupId, { agent_id: agentId, message });

      console.log('Send message API response:', response);

      // The API returns a success message, not the actual message object
      // Messages will be updated via SSE events, so we don't need to add them here
      // This is the expected behavior based on the backend response format
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  },

  addMessage: (message: Message) => {
    if (!message || !message.role) {
      console.warn('Attempted to add invalid message:', message);
      return;
    }

    // Trigger notifications ONLY for agent messages that mention @user
    if (message.role === 'agent' && message.sender && message.content) {
      if (message.content.includes('@user')) {
        const { selectedGroup } = get();
        notificationService.notifyAgentMention(
          message.sender,
          message.content,
          selectedGroup?.name
        );
      }
    }

    set((state) => ({
      messages: {
        ...state.messages,
        data: state.messages.data ? [...state.messages.data, message] : [message],
      },
    }));

    // Dispatch custom event for UI updates
    if (message.role === 'agent') {
      window.dispatchEvent(new CustomEvent('agentChainResponse', {
        detail: { message, agent: message.sender }
      }));
    }
  },

  stopGroupChain: async (groupId: string) => {
    try {
      await groupsApi.stopGroupChain(groupId);
      console.log('✅ Group chain stopped for group:', groupId);
    } catch (error) {
      console.error('❌ Failed to stop group chain:', error);
      throw error;
    }
  },

  // Document Actions
  loadDocuments: async (groupId: string) => {
    set((state) => ({
      documents: { ...state.documents, status: 'loading', error: null },
    }));

    try {
      const documents = await groupsApi.getGroupDocuments(groupId);
      set(() => ({
        documents: {
          data: Array.isArray(documents) ? documents : [],
          status: 'success',
          error: null,
          lastUpdated: Date.now(),
        },
      }));
    } catch (error) {
      console.error('Failed to load documents:', error);
      set((state) => ({
        documents: {
          ...state.documents,
          status: 'error',
          error: error instanceof Error ? error.message : 'Failed to load documents',
        },
      }));
    }
  },

  uploadDocument: async (
    groupId: string,
    file: File,
    agentId: string,
    message?: string,
    onProgress?: (progress: number) => void
  ) => {
    try {
      const document = await groupsApi.uploadDocument(
        groupId,
        { file, agent_id: agentId, message },
        onProgress
      );

      set((state) => ({
        documents: {
          ...state.documents,
          data: state.documents.data ? [...state.documents.data, document] : [document],
        },
      }));

      return document;
    } catch (error) {
      console.error('Failed to upload document:', error);
      throw error;
    }
  },

  // SSE Actions
  connectEventStream: (groupId: string) => {
    const { eventSource } = get();

    if (eventSource) {
      eventSource.close();
    }

    try {
      const newEventSource = groupsApi.createEventStream(groupId);

      newEventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('SSE event received:', data);

          // Handle different event types
          switch (data.type) {
            case 'message':
              console.log('Processing message event:', data.payload);
              // Backend sends message data in 'payload', not 'data'
              if (data.payload && data.payload.role) {
                // Convert backend payload to frontend message format
                const message = {
                  id: Date.now(), // Generate temporary ID
                  group_id: data.group_id,
                  sender: data.payload.sender,
                  role: data.payload.role,
                  content: data.payload.content,
                  created_at: data.timestamp,
                  updated_at: data.timestamp,
                  metadata: {}
                };
                get().addMessage(message);
              } else {
                console.warn('Received invalid message data via SSE:', data);
              }
              break;
            case 'agent_added':
              get().loadGroupAgents(groupId);
              break;
            case 'agent_removed':
              get().loadGroupAgents(groupId);
              break;
            case 'document_uploaded':
              get().loadDocuments(groupId);
              break;
            case 'tool_call':
              console.log('Processing tool_call event:', data.payload);
              // Add tool call as a special message to show real-time tool execution
              const toolCallMessage = {
                id: Date.now(),
                group_id: data.group_id,
                sender: data.agent_key || 'system',
                role: 'tool_call' as const,
                content: `🔧 Tool call: ${data.payload.tool}\nStatus: ${data.payload.status}`,
                created_at: data.timestamp,
                updated_at: data.timestamp,
                metadata: { tool: data.payload.tool, status: data.payload.status }
              };
              get().addMessage(toolCallMessage);
              break;
            case 'tool_result':
              console.log('Processing tool_result event:', data.payload);
              // Add tool result as a special message
              const toolResultMessage = {
                id: Date.now(),
                group_id: data.group_id,
                sender: data.agent_key || 'system',
                role: 'tool_result' as const,
                content: `✅ Tool result: ${data.payload.tool}\n${data.payload.excerpt}`,
                created_at: data.timestamp,
                updated_at: data.timestamp,
                metadata: { tool: data.payload.tool, excerpt: data.payload.excerpt }
              };
              get().addMessage(toolResultMessage);
              break;
            case 'mcp_call':
              console.log('Processing mcp_call event:', data.payload);
              // Add MCP call as a special message
              const mcpCallMessage = {
                id: Date.now(),
                group_id: data.group_id,
                sender: data.agent_key || 'system',
                role: 'mcp_call' as const,
                content: `🔧 MCP call: ${data.payload.server}/${data.payload.tool}\nStatus: ${data.payload.status}`,
                created_at: data.timestamp,
                updated_at: data.timestamp,
                metadata: { server: data.payload.server, tool: data.payload.tool, status: data.payload.status }
              };
              get().addMessage(mcpCallMessage);
              break;
            case 'error':
              console.log('Processing error event:', data.payload);
              // Add error as a special message
              const errorMessage = {
                id: Date.now(),
                group_id: data.group_id,
                sender: 'system',
                role: 'error' as const,
                content: `❌ Error in ${data.payload.where}: ${data.payload.message}`,
                created_at: data.timestamp,
                updated_at: data.timestamp,
                metadata: { where: data.payload.where, message: data.payload.message }
              };
              get().addMessage(errorMessage);
              break;
            case 'connected':
              console.log('SSE connection established for group:', groupId);
              break;
            default:
              console.log('Unknown event type:', data.type);
          }
        } catch (error) {
          console.error('Failed to parse SSE event:', error);
        }
      };

      newEventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
      };

      set({ eventSource: newEventSource });
    } catch (error) {
      console.error('Failed to connect to event stream:', error);
    }
  },

  disconnectEventStream: () => {
    const { eventSource } = get();

    if (eventSource) {
      eventSource.close();
      set({ eventSource: null });
    }
  },

  // Utility Actions
  clearGroupData: () => {
    set({
      groupAgents: createAsyncState<Agent[]>([]),
      messages: createAsyncState<Message[]>([]),
      documents: createAsyncState<Document[]>([]),
    });
  },

  reset: () => {
    const { disconnectEventStream } = get();
    disconnectEventStream();
    set(initialState);
  },
}));