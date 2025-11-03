/**
 * Admin View
 * Admin panel integrated with unified header/sidebar/footer
 * Features:
 * - User Management
 * - Group Management
 * - Resource Permissions
 * - Settings
 * NON-FUNCTIONAL: UI demonstration only
 */

import { motion, AnimatePresence } from 'framer-motion';
import {
  UsersIcon,
  UserGroupIcon,
  CubeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

type AdminView = 'overview' | 'users' | 'groups' | 'resources' | 'settings';

interface AdminViewProps {
  adminTab: AdminView;
  onTabChange?: (tab: AdminView) => void;
}

export const AdminView: React.FC<AdminViewProps> = ({ adminTab, onTabChange }) => {

  // Mock data
  const mockUsers = [
    { id: '1', name: 'John Doe', email: 'john@company.com', role: 'admin', status: 'active', groups: ['1', '2'], lastActive: '2 min ago' },
    { id: '2', name: 'Jane Smith', email: 'jane@company.com', role: 'user', status: 'active', groups: ['1'], lastActive: '1 hour ago' },
    { id: '3', name: 'Bob Wilson', email: 'bob@company.com', role: 'user', status: 'inactive', groups: ['2', '3'], lastActive: '2 days ago' },
    { id: '4', name: 'Alice Johnson', email: 'alice@company.com', role: 'user', status: 'active', groups: ['3'], lastActive: '5 min ago' },
    { id: '5', name: 'Charlie Brown', email: 'charlie@company.com', role: 'user', status: 'active', groups: ['1', '3'], lastActive: '30 min ago' },
  ];

  const mockGroups = [
    { id: '1', name: 'Engineering', description: 'Software development team', color: 'indigo', memberCount: 3 },
    { id: '2', name: 'Data Science', description: 'ML and AI research', color: 'purple', memberCount: 2 },
    { id: '3', name: 'Product', description: 'Product management', color: 'green', memberCount: 3 },
    { id: '4', name: 'Design', description: 'UX/UI design team', color: 'pink', memberCount: 0 },
  ];

  const mockResources = [
    {
      id: '1',
      name: 'GitHub MCP',
      description: 'Access GitHub repositories and issues',
      type: 'mcp' as const,
      isProtected: true,
      permissions: {
        '1': { canView: true, canEdit: true, canDelete: true, canExecute: true },
        '2': { canView: true, canEdit: false, canDelete: false, canExecute: true },
      },
      allowedUsers: ['1', '2'],
      createdBy: 'System',
      createdAt: '2024-01-15',
    },
    {
      id: '2',
      name: 'Filesystem MCP',
      description: 'Read and write local files',
      type: 'mcp' as const,
      isProtected: false,
      permissions: {
        '1': { canView: true, canEdit: true, canDelete: true, canExecute: true },
        '3': { canView: true, canEdit: true, canDelete: false, canExecute: true },
      },
      allowedUsers: ['1', '3'],
      createdBy: 'Admin',
      createdAt: '2024-02-01',
    },
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
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{mockUsers.length}</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Total Users</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-2xl p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between mb-4">
            <UserGroupIcon className="w-8 h-8 text-green-600 dark:text-green-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{mockGroups.length}</div>
          <div className="text-sm text-slate-600 dark:text-slate-400">Active Groups</div>
        </div>

        <div className="bg-gradient-to-br from-sky-50 to-slate-100 dark:from-sky-900/20 dark:to-slate-900/25 rounded-2xl p-6 border border-sky-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <CubeIcon className="w-8 h-8 text-sky-600 dark:text-sky-400" />
          </div>
          <div className="text-3xl font-bold text-slate-900 dark:text-white mb-1">{mockResources.length}</div>
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
            {mockUsers.map((user) => (
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
                <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">{user.lastActive}</td>
                <td className="px-6 py-4">
                  <button className="text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300 text-sm font-medium">
                    Edit
                  </button>
                </td>
              </tr>
            ))}
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
        {mockGroups.map((group) => (
          <div key={group.id} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${
                group.color === 'indigo' ? 'from-sky-500 to-cyan-600' :
                group.color === 'purple' ? 'from-cyan-400 to-sky-500' :
                group.color === 'green' ? 'from-emerald-400 to-emerald-600' :
                'from-amber-400 to-amber-600'
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
              <span className="text-slate-500 dark:text-slate-400">{group.memberCount} members</span>
              <button className="text-sky-600 hover:text-sky-700 dark:text-sky-400 font-medium">
                Manage →
              </button>
            </div>
          </div>
        ))}
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
        {mockResources.map((resource) => (
          <div key={resource.id} className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{resource.name}</h3>
                  {resource.isProtected && (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 text-xs font-medium rounded-full">
                      Protected
                    </span>
                  )}
                  <span className="px-2 py-1 bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300 text-xs font-medium rounded-full uppercase">
                    {resource.type}
                  </span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{resource.description}</p>
                
                {/* Permission Pills */}
                <div className="flex flex-wrap gap-2">
                  {Object.entries(resource.permissions).map(([groupId, perms]) => {
                    const permissionLabels = [];
                    if (perms.canView) permissionLabels.push('View');
                    if (perms.canEdit) permissionLabels.push('Edit');
                    if (perms.canDelete) permissionLabels.push('Delete');
                    if (perms.canExecute) permissionLabels.push('Execute');
                    
                    return (
                      <span key={groupId} className="px-3 py-1 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium rounded-full">
                        Group {groupId}: {permissionLabels.join(', ')}
                      </span>
                    );
                  })}
                </div>
              </div>
              <button className="ml-4 text-sky-600 hover:text-sky-700 dark:text-sky-400 text-sm font-medium">
                Edit Permissions
              </button>
            </div>
          </div>
        ))}
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
