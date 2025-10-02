import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  FunnelIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  ExclamationTriangleIcon,

  InformationCircleIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  UserIcon,

} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiService } from "@/shared/api";

// Types for log entries following project patterns
interface LogEvent {
  timestamp: string;
  session_id: string;
  event_type: string;
  level: string;
  message: string;
  details?: any;
  agent_id?: string;
  user_id?: string;
  duration_ms?: number;
  error?: string;
}

interface LogViewerProps {
  sessionId?: string;
  className?: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({ sessionId, className = '' }) => {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [eventTypeFilter, setEventTypeFilter] = useState('ALL');
  const [agentFilter, setAgentFilter] = useState('ALL');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());

  // Event categorization for intelligent display
  const eventCategories = {
    system: ['system_event', 'group_created', 'group_renamed', 'agent_added', 'agent_removed'],
    communication: ['message_sent', 'message_received'],
    tools: ['tool_called', 'tool_result'],
    mcp: ['mcp_called', 'mcp_result'],
    documents: ['document_uploaded', 'document_processed'],
    errors: ['error_occurred']
  };

  // Performance metrics calculation
  const performanceMetrics = useMemo(() => {
    const toolCalls = logs.filter(log => log.event_type === 'tool_called' && log.duration_ms);
    const avgDuration = toolCalls.length > 0
      ? toolCalls.reduce((sum, log) => sum + (log.duration_ms || 0), 0) / toolCalls.length
      : 0;

    const errorCount = logs.filter(log => log.level === 'ERROR').length;
    const successRate = logs.length > 0 ? ((logs.length - errorCount) / logs.length) * 100 : 100;

    return {
      totalEvents: logs.length,
      toolCalls: toolCalls.length,
      avgDuration: Math.round(avgDuration * 100) / 100,
      errorCount,
      successRate: Math.round(successRate * 100) / 100
    };
  }, [logs]);

  // Load logs from API
  const fetchLogs = async () => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const data = await apiService.getSessionLogs(sessionId, {});
      const events = Array.isArray(data) ? data : (data as any).events || [];
      setLogs(events);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      toast.error('Failed to load logs');
    } finally {
      setLoading(false);
    }
  };

  // Filter logs based on current filters
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.agent_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(log.details || {}).toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (levelFilter !== 'ALL') {
      filtered = filtered.filter(log => log.level === levelFilter);
    }

    if (eventTypeFilter !== 'ALL') {
      filtered = filtered.filter(log => log.event_type === eventTypeFilter);
    }

    if (agentFilter !== 'ALL') {
      filtered = filtered.filter(log => log.agent_id === agentFilter);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, levelFilter, eventTypeFilter, agentFilter]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, sessionId]);

  // Initial load
  useEffect(() => {
    fetchLogs();
  }, [sessionId]);

  // Get unique values for filters
  const uniqueAgents = [...new Set(logs.map(log => log.agent_id).filter(Boolean))];
  const uniqueEventTypes = [...new Set(logs.map(log => log.event_type))];

  // Get appropriate icon for event type
  const getEventIcon = (eventType: string, level: string) => {
    if (level === 'ERROR') return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
    if (level === 'WARNING') return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;

    if (eventCategories.tools.includes(eventType)) return <WrenchScrewdriverIcon className="h-5 w-5 text-blue-500" />;
    if (eventCategories.mcp.includes(eventType)) return <ServerIcon className="h-5 w-5 text-purple-500" />;
    if (eventCategories.communication.includes(eventType)) return <UserIcon className="h-5 w-5 text-green-500" />;

    return <InformationCircleIcon className="h-5 w-5 text-gray-500" />;
  };

  // Get color for event level
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'bg-red-100 text-red-800 border-red-200';
      case 'WARNING': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'INFO': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'DEBUG': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Toggle entry expansion
  const toggleExpanded = (logId: string) => {
    const newExpanded = new Set(expandedEntries);
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId);
    } else {
      newExpanded.add(logId);
    }
    setExpandedEntries(newExpanded);
  };

  // Download logs
  const downloadLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs_${sessionId}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ClockIcon className="h-6 w-6 text-gray-600" />
            <h2 className="text-xl font-semibold text-gray-900">
              Log Viewer
              {sessionId && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  Session: {sessionId}
                </span>
              )}
            </h2>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:border-gray-400 transition-colors"
            >
              <FunnelIcon className="h-4 w-4 mr-1" />
              Filters
            </button>
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:border-gray-400 transition-colors disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={downloadLogs}
              className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:border-gray-400 transition-colors"
            >
              <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{performanceMetrics.totalEvents}</div>
            <div className="text-sm text-gray-500">Total Events</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{performanceMetrics.toolCalls}</div>
            <div className="text-sm text-gray-500">Tool Calls</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{performanceMetrics.avgDuration}ms</div>
            <div className="text-sm text-gray-500">Avg Duration</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${performanceMetrics.errorCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {performanceMetrics.successRate}%
            </div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-6 py-4 bg-gray-50 border-b border-gray-200"
          >
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <div className="relative">
                  <MagnifyingGlassIcon className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search logs..."
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Level</label>
                <select
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="ALL">All Levels</option>
                  <option value="ERROR">Error</option>
                  <option value="WARNING">Warning</option>
                  <option value="INFO">Info</option>
                  <option value="DEBUG">Debug</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
                <select
                  value={eventTypeFilter}
                  onChange={(e) => setEventTypeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="ALL">All Types</option>
                  {uniqueEventTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
                <select
                  value={agentFilter}
                  onChange={(e) => setAgentFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  <option value="ALL">All Agents</option>
                  {uniqueAgents.map(agent => (
                    <option key={agent} value={agent}>{agent}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4 flex items-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Auto-refresh every 5 seconds</span>
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Log Entries */}
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <ArrowPathIcon className="h-6 w-6 animate-spin text-gray-400 mr-2" />
            <span className="text-gray-500">Loading logs...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-8">
            <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-1">No logs found</h3>
            <p className="text-sm text-gray-500">
              {logs.length === 0 ? 'No logs available for this session.' : 'Try adjusting your filters.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLogs.map((log, index) => {
              const logId = `${log.timestamp}-${index}`;
              const isExpanded = expandedEntries.has(logId);

              return (
                <motion.div
                  key={logId}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getEventIcon(log.event_type, log.level)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">
                            {formatTimestamp(log.timestamp)}
                          </span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getLevelColor(log.level)}`}>
                            {log.level}
                          </span>
                          {log.agent_id && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                              {log.agent_id}
                            </span>
                          )}
                          {log.duration_ms && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">
                              {log.duration_ms.toFixed(2)}ms
                            </span>
                          )}
                        </div>

                        {(log.details || log.error) && (
                          <button
                            onClick={() => toggleExpanded(logId)}
                            className="flex items-center text-xs text-gray-500 hover:text-gray-700"
                          >
                            {isExpanded ? (
                              <ChevronUpIcon className="h-4 w-4" />
                            ) : (
                              <ChevronDownIcon className="h-4 w-4" />
                            )}
                          </button>
                        )}
                      </div>

                      <p className="mt-1 text-sm text-gray-900">{log.message}</p>

                      <AnimatePresence>
                        {isExpanded && (log.details || log.error) && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="mt-3 overflow-hidden"
                          >
                            {log.error && (
                              <div className="mb-3">
                                <h4 className="text-xs font-medium text-red-600 mb-1">Error:</h4>
                                <div className="bg-red-50 border border-red-200 rounded p-2 text-xs text-red-900 font-mono">
                                  {log.error}
                                </div>
                              </div>
                            )}

                            {log.details && (
                              <div>
                                <h4 className="text-xs font-medium text-gray-600 mb-1">Details:</h4>
                                <div className="bg-gray-50 border border-gray-200 rounded p-2 text-xs text-gray-900 font-mono overflow-x-auto">
                                  <pre className="whitespace-pre-wrap">
                                    {JSON.stringify(log.details, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer;