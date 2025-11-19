/**
 * Authentication Store
 * Manages user authentication state, account type, and role
 * NON-FUNCTIONAL: UI demonstration only
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AccountType = 'individual' | 'enterprise';
export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  accountType: AccountType;
  role: UserRole;
  company?: string;
  joinedAt: string;
}

export interface AuthState {
  // Authentication
  isAuthenticated: boolean;
  currentUser: User | null;
  
  // UI State
  authPortalOpen: boolean;
  userManagementOpen: boolean;
  adminDashboardOpen: boolean;
}

export interface AuthActions {
  // Authentication
  login: (email: string, password: string, accountType: AccountType, isAdmin?: boolean) => void;
  logout: () => void;
  setCurrentUser: (user: User | null) => void;
  
  // UI Actions
  setAuthPortalOpen: (open: boolean) => void;
  setUserManagementOpen: (open: boolean) => void;
  setAdminDashboardOpen: (open: boolean) => void;
  
  // Role checks
  isEnterpriseUser: () => boolean;
  isAdmin: () => boolean;
  canManageUsers: () => boolean;
  
  // Reset
  reset: () => void;
}

export type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  isAuthenticated: false,
  currentUser: null,
  authPortalOpen: false,
  userManagementOpen: false,
  adminDashboardOpen: false,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Authentication Actions
      login: (email, _password, accountType, isAdmin = false) => {
        // Mock login - create user object
        const user: User = {
          id: `user_${Date.now()}`,
          name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
          email,
          accountType,
          role: isAdmin ? 'admin' : 'user',
          company: accountType === 'enterprise' ? email.split('@')[1] : undefined,
          joinedAt: new Date().toISOString(),
        };

        set({
          isAuthenticated: true,
          currentUser: user,
          authPortalOpen: false,
        });
      },

      logout: () => {
        set({
          isAuthenticated: false,
          currentUser: null,
          authPortalOpen: true, // Open auth portal on logout
        });
      },

      setCurrentUser: (user) => set({ currentUser: user }),

      // UI Actions
      setAuthPortalOpen: (open) => set({ authPortalOpen: open }),
      setUserManagementOpen: (open) => set({ userManagementOpen: open }),
      setAdminDashboardOpen: (open) => set({ adminDashboardOpen: open }),

      // Role Checks
      isEnterpriseUser: () => {
        const { currentUser } = get();
        return currentUser?.accountType === 'enterprise';
      },

      isAdmin: () => {
        const { currentUser } = get();
        return currentUser?.role === 'admin';
      },

      canManageUsers: () => {
        const { currentUser } = get();
        return currentUser?.accountType === 'enterprise' && currentUser?.role === 'admin';
      },

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: 'agentverse-auth-store',
      partialize: () => ({
        // Don't persist auth state for demo - always start logged out
        isAuthenticated: false,
        currentUser: null,
      }),
    }
  )
);
