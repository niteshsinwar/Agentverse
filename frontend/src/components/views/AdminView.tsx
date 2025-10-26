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
    { id: '1', name: 'Engineering', description: 'Software development team', color: 'blue', memberCount: 3 },
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Admin Overview</h2>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your organization's users, groups, and resource permissions
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-2xl p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between mb-4">
            <UsersIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{mockUsers.length}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Users</div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-2xl p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between mb-4">
            <UserGroupIcon className="w-8 h-8 text-green-600 dark:text-green-400" />
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{mockGroups.length}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Active Groups</div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-2xl p-6 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-4">
            <CubeIcon className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">{mockResources.length}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Resources</div>
        </div>

        <div className="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20 rounded-2xl p-6 border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-between mb-4">
            <ChartBarIcon className="w-8 h-8 text-amber-600 dark:text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">Enterprise</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Account Type</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onTabChange?.('users')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl hover:shadow-md transition-shadow border border-blue-200 dark:border-blue-800"
          >
            <UsersIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <div className="text-left">
              <div className="font-semibold text-gray-900 dark:text-white">Add User</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Invite new member</div>
            </div>
          </button>

          <button
            onClick={() => onTabChange?.('groups')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl hover:shadow-md transition-shadow border border-green-200 dark:border-green-800"
          >
            <UserGroupIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
            <div className="text-left">
              <div className="font-semibold text-gray-900 dark:text-white">Create Group</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">New access group</div>
            </div>
          </button>

          <button
            onClick={() => onTabChange?.('resources')}
            className="flex items-center space-x-3 p-4 bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl hover:shadow-md transition-shadow border border-purple-200 dark:border-purple-800"
          >
            <CubeIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            <div className="text-left">
              <div className="font-semibold text-gray-900 dark:text-white">Manage Permissions</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Resource access control</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );

  const renderUsers = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h2>
        <button className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg text-sm font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all">
          + Add User
        </button>
      </div>

      {/* Users Table Placeholder */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Active</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {mockUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                      {user.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{user.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    user.role === 'admin' 
                      ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
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
                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{user.lastActive}</td>
                <td className="px-6 py-4">
                  <button className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium">
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Group Management</h2>
        <button className="px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg text-sm font-semibold hover:from-green-700 hover:to-teal-700 transition-all">
          + Create Group
        </button>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockGroups.map((group) => (
          <div key={group.id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${
                group.color === 'blue' ? 'from-blue-400 to-blue-600' :
                group.color === 'purple' ? 'from-purple-400 to-purple-600' :
                group.color === 'green' ? 'from-green-400 to-green-600' :
                'from-pink-400 to-pink-600'
              } flex items-center justify-center text-white text-xl font-bold shadow-lg`}>
                {group.name.charAt(0)}
              </div>
              <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </button>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{group.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{group.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">{group.memberCount} members</span>
              <button className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium">
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Resource Permissions</h2>
        <button className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg text-sm font-semibold hover:from-purple-700 hover:to-pink-700 transition-all">
          + Add Resource
        </button>
      </div>

      {/* Resources List */}
      <div className="space-y-4">
        {mockResources.map((resource) => (
          <div key={resource.id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{resource.name}</h3>
                  {resource.isProtected && (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 text-xs font-medium rounded-full">
                      Protected
                    </span>
                  )}
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 text-xs font-medium rounded-full uppercase">
                    {resource.type}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{resource.description}</p>
                
                {/* Permission Pills */}
                <div className="flex flex-wrap gap-2">
                  {Object.entries(resource.permissions).map(([groupId, perms]) => {
                    const permissionLabels = [];
                    if (perms.canView) permissionLabels.push('View');
                    if (perms.canEdit) permissionLabels.push('Edit');
                    if (perms.canDelete) permissionLabels.push('Delete');
                    if (perms.canExecute) permissionLabels.push('Execute');
                    
                    return (
                      <span key={groupId} className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs font-medium rounded-full">
                        Group {groupId}: {permissionLabels.join(', ')}
                      </span>
                    );
                  })}
                </div>
              </div>
              <button className="ml-4 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 text-sm font-medium">
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
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Admin Settings</h2>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* General Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">General Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Allow User Registration</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Enable new users to sign up</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-indigo-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Require Email Verification</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Users must verify their email</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 dark:bg-gray-700">
                <span className="translate-x-1 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Security Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Two-Factor Authentication</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Require 2FA for admin accounts</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-indigo-600">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white transition" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Session Timeout</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Auto logout after inactivity</div>
              </div>
              <select className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-sm">
                <option>30 minutes</option>
                <option>1 hour</option>
                <option>4 hours</option>
                <option>Never</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notification Settings</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Email Notifications</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Send email alerts for admin events</div>
              </div>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-indigo-600">
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
