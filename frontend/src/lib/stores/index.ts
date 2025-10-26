/**
 * Store Index
 * Centralized exports for all stores
 */

export { useAppStore } from './app';
export type { AppStore, AppState, AppActions } from './app';

export { useGroupsStore } from './groups';
export type { GroupsStore, GroupsState, GroupsActions } from './groups';

export { useAgentsStore } from './agents';
export type { AgentsStore, AgentsState, AgentsActions } from './agents';

export { useAuthStore } from './auth';

// Store utilities
export const resetAllStores = () => {
  const { useAppStore } = require('./app');
  const { useGroupsStore } = require('./groups');
  const { useAgentsStore } = require('./agents');

  const { reset: resetApp } = useAppStore.getState();
  const { reset: resetGroups } = useGroupsStore.getState();
  const { reset: resetAgents } = useAgentsStore.getState();

  resetApp();
  resetGroups();
  resetAgents();
};