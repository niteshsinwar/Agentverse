/**
 * Authentication Store
 * Manages user authentication state, account type, and role
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { cloudAuth } from '../cloud/auth';

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
  tenant_id: string;
  tenant_name?: string;
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
  login: (tenant_id: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
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
      login: async (tenant_id, email, password) => {
        try {
          // Call cloud auth service
          const response = await cloudAuth.login({ tenant_id, email, password });

          // Fetch user profile
          const userProfile = await cloudAuth.me();

          // Map to local User interface
          const user: User = {
            id: userProfile.id,
            name: userProfile.name,
            email: userProfile.email,
            accountType: 'enterprise', // Default to enterprise for cloud users
            role: userProfile.role,
            tenant_id: tenant_id,
            tenant_name: userProfile.tenant_name,
            joinedAt: new Date().toISOString(),
          };

          set({
            isAuthenticated: true,
            currentUser: user,
            authPortalOpen: false,
          });
        } catch (error) {
          console.error('Login failed:', error);
          throw error;
        }
      },

      logout: async () => {
        try {
          await cloudAuth.logout();
        } catch (error) {
          console.error('Logout failed:', error);
        }

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
