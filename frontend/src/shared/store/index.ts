/**
 * Store Index
 * Centralized exports for all stores
 */

export { useAppStore } from './app.store';
export type { AppStore, AppState, AppActions } from './app.store';

export { useGroupsStore } from './groups.store';
export type { GroupsStore, GroupsState, GroupsActions } from './groups.store';

export { useAgentsStore } from './agents.store';
export type { AgentsStore, AgentsState, AgentsActions } from './agents.store';

// Store utilities
export const resetAllStores = () => {
  const { useAppStore } = require('./app.store');
  const { useGroupsStore } = require('./groups.store');
  const { useAgentsStore } = require('./agents.store');

  const { reset: resetApp } = useAppStore.getState();
  const { reset: resetGroups } = useGroupsStore.getState();
  const { reset: resetAgents } = useAgentsStore.getState();

  resetApp();
  resetGroups();
  resetAgents();
};