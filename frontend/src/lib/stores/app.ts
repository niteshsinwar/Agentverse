/**
 * App Store
 * Global application state management
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Theme } from '../types';
import { DEFAULT_SUPPORTED_FILE_FORMATS } from '../config';

export interface AppState {
  // UI State
  sidebarExpanded: boolean;
  currentView: 'chat' | 'agent-management' | 'admin';

  // Modal states
  commandPaletteOpen: boolean;
  settingsOpen: boolean;
  toolsManagementOpen: boolean;
  mcpManagementOpen: boolean;
  helpOpen: boolean;
  logsOpen: boolean;
  communityCenterOpen: boolean;

  // Theme
  theme: Theme;

  // Loading states
  appLoading: boolean;
  showSplash: boolean;
  appReady: boolean;

  // Initialization
  initialLoadCompleted: boolean;

  // Backend-configured document formats
  supportedFileFormats: string[];
}

export interface AppActions {
  // UI Actions
  setSidebarExpanded: (expanded: boolean) => void;
  setCurrentView: (view: AppState['currentView']) => void;

  // Modal Actions
  setCommandPaletteOpen: (open: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
  setToolsManagementOpen: (open: boolean) => void;
  setMcpManagementOpen: (open: boolean) => void;
  setHelpOpen: (open: boolean) => void;
  setLogsOpen: (open: boolean) => void;
  setCommunityCenterOpen: (open: boolean) => void;
  closeAllModals: () => void;

  // Theme Actions
  setTheme: (theme: Theme) => void;

  // Loading Actions
  setAppLoading: (loading: boolean) => void;
  setShowSplash: (show: boolean) => void;
  setAppReady: (ready: boolean) => void;

  // Initialization Actions
  setInitialLoadCompleted: (completed: boolean) => void;

  // Reset
  reset: () => void;

  // Settings sync
  setSupportedFileFormats: (formats: string[]) => void;
}

export type AppStore = AppState & AppActions;

const initialState: AppState = {
  // UI State
  sidebarExpanded: true,
  currentView: 'chat',

  // Modal states
  commandPaletteOpen: false,
  settingsOpen: false,
  toolsManagementOpen: false,
  mcpManagementOpen: false,
  helpOpen: false,
  logsOpen: false,
  communityCenterOpen: false,

  // Theme
  theme: 'system',

  // Loading states
  appLoading: true,
  showSplash: true,
  appReady: false,

  // Initialization
  initialLoadCompleted: false,

  // Backend-configured document formats
  supportedFileFormats: Array.from(DEFAULT_SUPPORTED_FILE_FORMATS),
};

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      ...initialState,

      // UI Actions
      setSidebarExpanded: (expanded) => set({ sidebarExpanded: expanded }),
      setCurrentView: (view) => set({ currentView: view }),

      // Modal Actions
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      setSettingsOpen: (open) => set({ settingsOpen: open }),
      setToolsManagementOpen: (open) => set({ toolsManagementOpen: open }),
      setMcpManagementOpen: (open) => set({ mcpManagementOpen: open }),
      setHelpOpen: (open) => set({ helpOpen: open }),
      setLogsOpen: (open) => set({ logsOpen: open }),
      setCommunityCenterOpen: (open) => set({ communityCenterOpen: open }),
      closeAllModals: () => set({
        commandPaletteOpen: false,
        settingsOpen: false,
        toolsManagementOpen: false,
        mcpManagementOpen: false,
        helpOpen: false,
        logsOpen: false,
        communityCenterOpen: false,
      }),

      // Theme Actions
      setTheme: (theme) => set({ theme }),

      // Loading Actions
      setAppLoading: (loading) => set({ appLoading: loading }),
      setShowSplash: (show) => set({ showSplash: show }),
      setAppReady: (ready) => set({ appReady: ready }),

      // Initialization Actions
      setInitialLoadCompleted: (completed) => set({ initialLoadCompleted: completed }),

      setSupportedFileFormats: (formats) => set({
        supportedFileFormats: Array.from(
          new Set(
            (formats || [])
              .map((ext) => ext?.toString().trim().toLowerCase())
              .filter((ext): ext is string => Boolean(ext))
          )
        ),
      }),

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: 'agentverse-app-store',
      partialize: (state) => ({
        // Only persist UI preferences, not loading states
        sidebarExpanded: state.sidebarExpanded,
        theme: state.theme,
        currentView: state.currentView,
      }),
    }
  )
);
