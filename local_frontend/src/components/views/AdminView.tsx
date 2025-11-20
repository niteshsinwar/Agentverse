/**
 * Admin View
 * Admin panel integrated with unified header/sidebar/footer
 * Features:
 * - User Management
 * - Group Management
 * - Resource Permissions
 * - Settings
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UsersIcon,
  UserGroupIcon,
  CubeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import {
  fetchGroups,
  fetchUsers,
  fetchAgents,
  fetchTools,
  fetchMCPServers,
  type Group,
  type TenantUser,
  type Agent,
  type Tool,
  type MCPServer,
} from '../../lib/cloud/api';

type AdminView = 'overview' | 'users' | 'groups' | 'resources' | 'settings';

interface AdminViewProps {
  adminTab: AdminView;
  onTabChange?: (tab: AdminView) => void;
}

export const AdminView: React.FC<AdminViewProps> = ({ adminTab, onTabChange }) => {

  // State for real data from cloud backend
  const [users, setUsers] = useState<TenantUser[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [mcpServers, setMCPServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all tenant data in parallel
        const [usersData, groupsData, agentsData, toolsData, mcpServersData] = await Promise.all([
          fetchUsers(),
          fetchGroups(),
          fetchAgents(),
          fetchTools(),
          fetchMCPServers(),
        ]);

        setUsers(usersData);
        setGroups(groupsData);
        setAgents(agentsData);
        setTools(toolsData);
        setMCPServers(mcpServersData);
      } catch (err) {
        console.error('Failed to load admin data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Combined resources list (agents + tools + mcp servers)
  const allResources = [
    ...agents.map((a) => ({ ...a, type: 'agent' as const })),
    ...tools.map((t) => ({ ...t, type: 'tool' as const })),
    ...mcpServers.map((m) => ({ ...m, type: 'mcp' as const })),
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Admin Overview</h2>
        <p className="text-slate-600 dark:text-slate-400">
          Manage your organization's users, groups, and resource permissions
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-slate-50 to-sky-100 dark:from-slate-900/30 dark:to-sky-900/20 rounded-2xl p-6 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <UsersIcon className="w-8 h-8 text-sky-600 dark:text-sky-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{users.length}</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Total Users</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-2xl p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between mb-4">
            <UserGroupIcon className="w-8 h-8 text-green-600 dark:text-green-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{groups.length}</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Active Groups</div>
        </div>

        <div className="bg-gradient-to-br from-sky-50 to-slate-100 dark:from-sky-900/20 dark:to-slate-900/25 rounded-2xl p-6 border border-sky-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <CubeIcon className="w-8 h-8 text-sky-600 dark:text-sky-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{allResources.length}</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Resources</div>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 rounded-2xl p-6 border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-between mb-4">
            <ChartBarIcon className="w-8 h-8 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">Enterprise</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Account Type</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onTabChange?.('users')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-slate-50 to-sky-100 dark:from-slate-900/30 dark:to-sky-900/20 rounded-xl hover:shadow-md transition-shadow border border-slate-200 dark:border-slate-700"
          >
            <UsersIcon className="w-6 h-6 text-sky-600 dark:text-sky-400" />
            <div className="text-left">
              <div className="font-semibold text-slate-900 dark:text-white">Add User</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Invite new member</div>
            </div>
          </button>

          <button
            onClick={() => onTabChange?.('groups')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl hover:shadow-md transition-shadow border border-green-200 dark:border-green-800"
          >
            <UserGroupIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
            <div className="text-left">
              <div className="font-semibold text-slate-900 dark:text-white">Create Group</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">New access group</div>
            </div>
          </button>

          <button
            onClick={() => onTabChange?.('resources')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-sky-50 to-slate-100 dark:from-sky-900/20 dark:to-slate-900/25 rounded-xl hover:shadow-md transition-shadow border border-sky-200 dark:border-slate-700"
          >
            <CubeIcon className="w-6 h-6 text-sky-600 dark:text-sky-400" />
            <div className="text-left">
              <div className="font-semibold text-slate-900 dark:text-white">Manage Permissions</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Resource access control</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );

  const renderUsers = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">User Management</h2>
        <button className="px-4 py-2 brand-gradient text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-all">
          + Add User
        </button>
      </div>

      {/* Users Table Placeholder */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 dark:bg-slate-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Last Active</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {users.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                  No users found for this tenant
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/50">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 brand-gradient rounded-full flex items-center justify-center text-white text-sm font-bold">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-medium text-slate-900 dark:text-white">{user.name}</div>
                        <div className="text-sm text-slate-500 dark:text-slate-400">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      user.role === 'admin'
                        ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                        : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      user.status === 'active'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                        : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                    }`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{user.last_active || 'N/A'}</td>
                  <td className="px-6 py-4">
                    <button className="text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300 text-sm font-medium">
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderGroups = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Group Management</h2>
        <button className="px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg text-sm font-semibold hover:from-green-700 hover:to-teal-700 transition-all">
          + Create Group
        </button>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <UserGroupIcon className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 mb-4">
              No groups found for this tenant
            </p>
            <button className="px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg text-sm font-semibold hover:from-green-700 hover:to-teal-700 transition-all">
              Create Your First Group
            </button>
          </div>
        ) : (
          groups.map((group, index) => {
            // Assign colors dynamically based on index
            const colors = ['indigo', 'purple', 'green', 'pink', 'amber', 'cyan'];
            const color = colors[index % colors.length];

            return (
              <div key={group.id} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${
                    color === 'indigo' ? 'from-sky-500 to-cyan-600' :
                    color === 'purple' ? 'from-cyan-400 to-sky-500' :
                    color === 'green' ? 'from-emerald-400 to-emerald-600' :
                    color === 'pink' ? 'from-pink-400 to-pink-600' :
                    color === 'amber' ? 'from-amber-400 to-amber-600' :
                    'from-cyan-400 to-cyan-600'
                  } flex items-center justify-center text-white text-xl font-bold shadow-lg`}>
                    {group.name.charAt(0)}
                  </div>
                  <button className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">{group.name}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{group.description}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">{group.member_count || 0} members</span>
                  <button className="text-sky-600 hover:text-sky-700 dark:text-sky-400 font-medium">
                    Manage →
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );

  const renderResources = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Resource Permissions</h2>
        <button className="px-4 py-2 brand-gradient text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-all">
          + Add Resource
        </button>
      </div>

      {/* Resources List */}
      <div className="space-y-4">
        {allResources.length === 0 ? (
          <div className="text-center py-12">
            <CubeIcon className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 mb-4">
              No resources found for this tenant
            </p>
            <p className="text-sm text-slate-400 dark:text-slate-500">
              Resources include agents, tools, and MCP servers
            </p>
          </div>
        ) : (
          allResources.map((resource) => (
            <div key={resource.id} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{resource.name}</h3>
                    {'is_protected' in resource && resource.is_protected && (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 text-xs font-medium rounded-full">
                        Protected
                      </span>
                    )}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full uppercase ${
                      resource.type === 'agent' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' :
                      resource.type === 'tool' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' :
                      'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                    }`}>
                      {resource.type}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{resource.description}</p>

                  {/* Resource metadata */}
                  <div className="flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
                    {resource.created_by && (
                      <span>Created by: {resource.created_by}</span>
                    )}
                    {resource.created_at && (
                      <span>Created: {new Date(resource.created_at).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
                <button className="ml-4 text-sky-600 hover:text-sky-700 dark:text-sky-400 text-sm font-medium">
                  Edit Permissions
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Admin Settings</h2>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* General Settings */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">General Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Allow User Registration</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Enable new users to sign up</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-sky-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Require Email Verification</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Users must verify their email</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-slate-200 dark:bg-slate-700">
                <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Security Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Two-Factor Authentication</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Require 2FA for admin accounts</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-sky-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Session Timeout</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Auto logout after inactivity</div>
              </div>
              <select className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-sm">
                <option>30 minutes</option>
                <option>1 hour</option>
                <option>4 hours</option>
                <option>Never</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Notification Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-slate-900 dark:text-white">Email Notifications</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Send email alerts for admin events</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-sky-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (adminTab) {
      case 'users':
        return renderUsers();
      case 'groups':
        return renderGroups();
      case 'resources':
        return renderResources();
      case 'settings':
        return renderSettings();
      default:
        return renderOverview();
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20">
          <div className="max-w-7xl mx-auto p-8 flex items-center justify-center min-h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 dark:border-sky-400 mx-auto mb-4"></div>
              <p className="text-slate-600 dark:text-slate-400">Loading tenant data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20">
          <div className="max-w-7xl mx-auto p-8 flex items-center justify-center min-h-96">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">Failed to Load Data</h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 brand-gradient text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-all"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Content Area - Tab navigation now handled by sidebar */}
      <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-50 via-violet-50/30 to-cyan-50/20 dark:from-slate-900 dark:via-violet-950/30 dark:to-cyan-950/20">
        <div className="max-w-7xl mx-auto p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={adminTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
