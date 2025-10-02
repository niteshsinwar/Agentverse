import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  UserIcon,
  CogIcon,
  ExclamationTriangleIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  FolderPlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiService } from "@/shared/api";
import { LogEvent } from '../types';

interface UserAction {
  timestamp: string;
  action_type: string;
  resource_type: string;
  resource_id: string;
  resource_name?: string;
  success: boolean;
  duration_ms?: number;
  error_message?: string;
  complexity_score?: number;
  session_id: string;
}

interface ActivityMetrics {
  totalActions: number;
  successRate: number;
  avgDuration: number;
  errorCount: number;
  mostUsedFeatures: Array<{feature: string; count: number}>;
  complexityDistribution: Record<string, number>;
  hourlyActivity: Record<string, number>;
}

interface UserActivityDashboardProps {
  sessionId?: string;
  className?: string;
}

export const UserActivityDashboard: React.FC<UserActivityDashboardProps> = ({
  sessionId,
  className = ''
}) => {
  const [userActions, setUserActions] = useState<UserAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const [actionTypeFilter, setActionTypeFilter] = useState('ALL');
  const [showSuccessOnly, setShowSuccessOnly] = useState(false);

  // Calculate metrics from user actions
  const metrics: ActivityMetrics = useMemo(() => {
    const filteredActions = userActions.filter(action => {
      if (actionTypeFilter !== 'ALL' && !action.action_type.includes(actionTypeFilter.toLowerCase())) {
        return false;
      }
      if (showSuccessOnly && !action.success) {
        return false;
      }
      return true;
    });

    const totalActions = filteredActions.length;
    const successfulActions = filteredActions.filter(a => a.success).length;
    const successRate = totalActions > 0 ? (successfulActions / totalActions) * 100 : 100;
    const errorCount = filteredActions.filter(a => !a.success).length;

    const durationsWithValues = filteredActions.filter(a => a.duration_ms);
    const avgDuration = durationsWithValues.length > 0
      ? durationsWithValues.reduce((sum, a) => sum + (a.duration_ms || 0), 0) / durationsWithValues.length
      : 0;

    // Feature usage analysis
    const featureUsage: Record<string, number> = {};
    filteredActions.forEach(action => {
      const feature = action.resource_type || 'unknown';
      featureUsage[feature] = (featureUsage[feature] || 0) + 1;
    });

    const mostUsedFeatures = Object.entries(featureUsage)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([feature, count]) => ({ feature, count }));

    // Complexity distribution
    const complexityDistribution: Record<string, number> = {};
    filteredActions.forEach(action => {
      const complexity = action.complexity_score || 1;
      const bucket = complexity <= 3 ? 'Simple' : complexity <= 6 ? 'Medium' : 'Complex';
      complexityDistribution[bucket] = (complexityDistribution[bucket] || 0) + 1;
    });

    // Hourly activity
    const hourlyActivity: Record<string, number> = {};
    filteredActions.forEach(action => {
      const hour = new Date(action.timestamp).getHours();
      const hourKey = `${hour}:00`;
      hourlyActivity[hourKey] = (hourlyActivity[hourKey] || 0) + 1;
    });

    return {
      totalActions,
      successRate: Math.round(successRate * 100) / 100,
      avgDuration: Math.round(avgDuration * 100) / 100,
      errorCount,
      mostUsedFeatures,
      complexityDistribution,
      hourlyActivity
    };
  }, [userActions, actionTypeFilter, showSuccessOnly]);

  // Load user actions from session logs
  const fetchUserActions = async () => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await apiService.getSessionLogs(sessionId, {
        format: 'json',
        limit: 1000
      });
      const events = Array.isArray(response) ? response : (response as any).events || [];

      // Filter for user action events
      const userActionEvents = events.filter((event: LogEvent) =>
        event.details?.action_type ||
        event.event_type.includes('create') ||
        event.event_type.includes('update') ||
        event.event_type.includes('delete')
      ) || [];

      // Transform to user actions format
      const actions: UserAction[] = userActionEvents.map((event: LogEvent) => ({
        timestamp: event.timestamp,
        action_type: event.details?.action_type || event.event_type,
        resource_type: event.details?.resource_type || 'unknown',
        resource_id: event.details?.resource_id || event.agent_id || 'unknown',
        resource_name: event.details?.resource_name,
        success: event.level !== 'ERROR',
        duration_ms: event.duration_ms,
        error_message: event.error,
        complexity_score: event.details?.complexity_score,
        session_id: event.session_id
      }));

      setUserActions(actions);
    } catch (error) {
      console.error('Failed to fetch user actions:', error);
      toast.error('Failed to load user activity data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserActions();
  }, [sessionId, timeRange]);

  // Get icon for action type
  const getActionIcon = (actionType: string, success: boolean) => {
    if (!success) return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;

    if (actionType.includes('create')) return <FolderPlusIcon className="h-5 w-5 text-green-500" />;
    if (actionType.includes('update')) return <PencilIcon className="h-5 w-5 text-blue-500" />;
    if (actionType.includes('delete')) return <TrashIcon className="h-5 w-5 text-red-500" />;
    if (actionType.includes('view')) return <EyeIcon className="h-5 w-5 text-gray-500" />;
    if (actionType.includes('tool')) return <WrenchScrewdriverIcon className="h-5 w-5 text-purple-500" />;
    if (actionType.includes('mcp')) return <ServerIcon className="h-5 w-5 text-indigo-500" />;
    if (actionType.includes('agent')) return <UserIcon className="h-5 w-5 text-blue-500" />;

    return <CogIcon className="h-5 w-5 text-gray-500" />;
  };

  // Get action type color
  const getActionTypeColor = (actionType: string) => {
    if (actionType.includes('create')) return 'bg-green-100 text-green-800 border-green-200';
    if (actionType.includes('update')) return 'bg-blue-100 text-blue-800 border-blue-200';
    if (actionType.includes('delete')) return 'bg-red-100 text-red-800 border-red-200';
    if (actionType.includes('error')) return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  // Format action description
  const formatActionDescription = (action: UserAction) => {
    const resourceName = action.resource_name || action.resource_id;

    if (action.action_type.includes('create_start')) {
      return `Started creating ${action.resource_type}: ${resourceName}`;
    }
    if (action.action_type.includes('create_success')) {
      return `Successfully created ${action.resource_type}: ${resourceName}`;
    }
    if (action.action_type.includes('create_failed')) {
      return `Failed to create ${action.resource_type}: ${resourceName}`;
    }
    if (action.action_type.includes('update')) {
      return `Updated ${action.resource_type}: ${resourceName}`;
    }
    if (action.action_type.includes('delete')) {
      return `Deleted ${action.resource_type}: ${resourceName}`;
    }
    if (action.action_type.includes('validation_error')) {
      return `Validation error in ${action.resource_type}`;
    }

    return `${action.action_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ChartBarIcon className="h-6 w-6 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              User Activity Dashboard
              {sessionId && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  Session: {sessionId}
                </span>
              )}
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{metrics.totalActions}</div>
            <div className="text-sm text-gray-500">Total Actions</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${metrics.successRate >= 90 ? 'text-green-600' : metrics.successRate >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
              {metrics.successRate}%
            </div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{metrics.avgDuration}ms</div>
            <div className="text-sm text-gray-500">Avg Duration</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${metrics.errorCount === 0 ? 'text-green-600' : 'text-red-600'}`}>
              {metrics.errorCount}
            </div>
            <div className="text-sm text-gray-500">Errors</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <FunnelIcon className="h-4 w-4 text-gray-400 mr-2" />
            <select
              value={actionTypeFilter}
              onChange={(e) => setActionTypeFilter(e.target.value)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ALL">All Actions</option>
              <option value="create">Create Actions</option>
              <option value="update">Update Actions</option>
              <option value="delete">Delete Actions</option>
              <option value="validation">Validation Actions</option>
            </select>
          </div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={showSuccessOnly}
              onChange={(e) => setShowSuccessOnly(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Success only</span>
          </label>
        </div>
      </div>

      {/* Feature Usage & Complexity Analysis */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Most Used Features</h3>
            <div className="space-y-2">
              {metrics.mostUsedFeatures.map((feature, _index) => (
                <div key={feature.feature} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{feature.feature}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(feature.count / metrics.totalActions) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{feature.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Task Complexity</h3>
            <div className="space-y-2">
              {Object.entries(metrics.complexityDistribution).map(([complexity, count]) => (
                <div key={complexity} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{complexity}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          complexity === 'Simple' ? 'bg-green-500' :
                          complexity === 'Medium' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${(count / metrics.totalActions) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="px-6 py-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>

        {loading ? (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-gray-500">Loading activity...</span>
          </div>
        ) : userActions.length === 0 ? (
          <div className="text-center py-8">
            <UserIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-1">No activity found</h3>
            <p className="text-sm text-gray-500">User actions will appear here once they start using the system.</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {userActions.slice(0, 20).map((action, index) => (
              <motion.div
                key={`${action.timestamp}-${index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex-shrink-0">
                  {getActionIcon(action.action_type, action.success)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-900 truncate">
                      {formatActionDescription(action)}
                    </p>
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getActionTypeColor(action.action_type)}`}>
                        {action.action_type.replace(/_/g, ' ')}
                      </span>
                      {action.duration_ms && (
                        <span className="text-xs text-gray-500">
                          {action.duration_ms.toFixed(0)}ms
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-1">
                    <p className="text-xs text-gray-500">
                      {new Date(action.timestamp).toLocaleString()}
                    </p>
                    {action.error_message && (
                      <p className="text-xs text-red-600 truncate max-w-xs">
                        {action.error_message}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserActivityDashboard;