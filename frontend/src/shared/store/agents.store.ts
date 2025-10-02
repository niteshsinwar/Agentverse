/**
 * Agents Store
 * State management for agent data and operations
 */

import { create } from 'zustand';
import { agentsApi } from '../api/endpoints/agents.api';
import type { Agent, CreateAgentRequest, UpdateAgentRequest } from '../api/types/entities';
import type { AsyncState } from '../types/common';

export interface AgentsState {
  // Available agents
  agents: AsyncState<Agent[]>;

  // Agent creation/editing
  agentFormData: CreateAgentRequest | null;
  agentValidation: {
    isValidating: boolean;
    result: any | null;
    error: string | null;
  };
}

export interface AgentsActions {
  // Agent Actions
  loadAgents: () => Promise<void>;
  createAgent: (data: CreateAgentRequest) => Promise<Agent>;
  updateAgent: (agentKey: string, data: UpdateAgentRequest) => Promise<Agent>;
  deleteAgent: (agentKey: string) => Promise<void>;

  // Validation Actions
  validateAgent: (data: CreateAgentRequest) => Promise<any>;
  validateAgentFolder: (folderPath: string) => Promise<any>;

  // Form Actions
  setAgentFormData: (data: CreateAgentRequest | null) => void;
  updateAgentFormData: (updates: Partial<CreateAgentRequest>) => void;
  clearAgentFormData: () => void;

  // Utility Actions
  reset: () => void;
}

export type AgentsStore = AgentsState & AgentsActions;

const createAsyncState = <T>(initialData: T | null = null): AsyncState<T> => ({
  data: initialData,
  status: 'idle',
  error: null,
  lastUpdated: undefined,
});

const initialState: AgentsState = {
  agents: createAsyncState<Agent[]>([]),
  agentFormData: null,
  agentValidation: {
    isValidating: false,
    result: null,
    error: null,
  },
};

export const useAgentsStore = create<AgentsStore>((set) => ({
  ...initialState,

  // Agent Actions
  loadAgents: async () => {
    set((state) => ({
      agents: { ...state.agents, status: 'loading', error: null },
    }));

    try {
      const agents = await agentsApi.getAgents();
      set(() => ({
        agents: {
          data: Array.isArray(agents) ? agents : [],
          status: 'success',
          error: null,
          lastUpdated: Date.now(),
        },
      }));
    } catch (error) {
      console.error('Failed to load agents:', error);
      set((state) => ({
        agents: {
          ...state.agents,
          status: 'error',
          error: error instanceof Error ? error.message : 'Failed to load agents',
        },
      }));
    }
  },

  createAgent: async (data: CreateAgentRequest) => {
    try {
      const newAgent = await agentsApi.createAgent(data);

      set((state) => ({
        agents: {
          ...state.agents,
          data: state.agents.data ? [...state.agents.data, newAgent] : [newAgent],
        },
      }));

      return newAgent;
    } catch (error) {
      console.error('Failed to create agent:', error);
      throw error;
    }
  },

  updateAgent: async (agentKey: string, data: UpdateAgentRequest) => {
    try {
      const updatedAgent = await agentsApi.updateAgent(agentKey, data);

      set((state) => ({
        agents: {
          ...state.agents,
          data: state.agents.data?.map(agent =>
            agent.key === agentKey ? updatedAgent : agent
          ) || [],
        },
      }));

      return updatedAgent;
    } catch (error) {
      console.error('Failed to update agent:', error);
      throw error;
    }
  },

  deleteAgent: async (agentKey: string) => {
    try {
      await agentsApi.deleteAgent(agentKey);

      set((state) => ({
        agents: {
          ...state.agents,
          data: state.agents.data?.filter(agent => agent.key !== agentKey) || [],
        },
      }));
    } catch (error) {
      console.error('Failed to delete agent:', error);
      throw error;
    }
  },

  // Validation Actions
  validateAgent: async (data: CreateAgentRequest) => {
    set((state) => ({
      agentValidation: {
        ...state.agentValidation,
        isValidating: true,
        error: null,
      },
    }));

    try {
      const result = await agentsApi.validateAgent(data);

      set(() => ({
        agentValidation: {
          isValidating: false,
          result,
          error: null,
        },
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Validation failed';

      set(() => ({
        agentValidation: {
          isValidating: false,
          result: null,
          error: errorMessage,
        },
      }));

      throw error;
    }
  },

  validateAgentFolder: async (folderPath: string) => {
    set((state) => ({
      agentValidation: {
        ...state.agentValidation,
        isValidating: true,
        error: null,
      },
    }));

    try {
      const result = await agentsApi.validateAgentFolder(folderPath);

      set(() => ({
        agentValidation: {
          isValidating: false,
          result,
          error: null,
        },
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Folder validation failed';

      set(() => ({
        agentValidation: {
          isValidating: false,
          result: null,
          error: errorMessage,
        },
      }));

      throw error;
    }
  },

  // Form Actions
  setAgentFormData: (data: CreateAgentRequest | null) => {
    set({ agentFormData: data });
  },

  updateAgentFormData: (updates: Partial<CreateAgentRequest>) => {
    set((state) => ({
      agentFormData: state.agentFormData
        ? { ...state.agentFormData, ...updates }
        : null,
    }));
  },

  clearAgentFormData: () => {
    set({
      agentFormData: null,
      agentValidation: {
        isValidating: false,
        result: null,
        error: null,
      },
    });
  },

  // Utility Actions
  reset: () => {
    set(initialState);
  },
}));