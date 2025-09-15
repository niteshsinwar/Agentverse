import React, { useState } from 'react';
import { Group } from '../types';
import { Plus, Trash2, Users } from 'lucide-react';

interface GroupManagerProps {
  groups: Group[];
  selectedGroup: Group | null;
  onSelectGroup: (group: Group) => void;
  onCreateGroup: (name: string) => void;
  onDeleteGroup: (groupId: string) => void;
}

export const GroupManager: React.FC<GroupManagerProps> = ({
  groups,
  selectedGroup,
  onSelectGroup,
  onCreateGroup,
  onDeleteGroup,
}) => {
  const [newGroupName, setNewGroupName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (newGroupName.trim()) {
      onCreateGroup(newGroupName.trim());
      setNewGroupName('');
      setShowCreateForm(false);
    }
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <Users className="w-4 h-4" />
          Groups
        </h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreate} className="mb-4">
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="Enter group name..."
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
          <div className="flex gap-2 mt-2">
            <button
              type="submit"
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(false);
                setNewGroupName('');
              }}
              className="px-3 py-1 text-sm bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {groups.map((group) => (
          <div
            key={group.id}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
              selectedGroup?.id === group.id
                ? 'bg-blue-100 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            <div
              onClick={() => onSelectGroup(group)}
              className="flex-1 text-left"
            >
              <div className="font-medium text-gray-900 dark:text-white text-sm">
                {group.name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(group.created_at * 1000).toLocaleDateString()}
              </div>
            </div>
            
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Delete group "${group.name}"?`)) {
                  onDeleteGroup(group.id);
                }
              }}
              className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        
        {groups.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No groups yet</p>
            <p className="text-xs">Create your first group to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};