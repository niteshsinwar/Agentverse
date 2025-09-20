import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChartBarIcon,
  ClockIcon,
  UserIcon,
  CogIcon,
  ServerIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';

import LogViewer from './LogViewer';
import UserActivityDashboard from './UserActivityDashboard';
import { LogSession, SessionSummary } from '../types';
import { apiService } from '../services/api';
import { toast } from 'react-hot-toast';

interface ComprehensiveLogPanelProps {
  isOpen: boolean;
  onClose: () => void;
  currentSessionId?: string;
}

export const ComprehensiveLogPanel: React.FC<ComprehensiveLogPanelProps> = ({
  isOpen,
  onClose,
  currentSessionId
}) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [sessions, setSessions] = useState<LogSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(currentSessionId || null);
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tab configuration
  const tabs = [
    {
      name: 'User Activity',
      icon: UserIcon,
      component: UserActivityDashboard,
      description: 'Track user interactions, form submissions, and validation errors'
    },
    {
      name: 'Session Logs',
      icon: ClockIcon,
      component: LogViewer,
      description: 'Detailed system logs and agent activity'
    },
    {
      name: 'Performance',
      icon: ChartBarIcon,
      component: null,
      description: 'System performance metrics and analytics'
    },
    {
      name: 'Errors & Issues',
      icon: ExclamationTriangleIcon,
      component: null,
      description: 'Error tracking and debugging information'
    }
  ];

  // Load sessions when panel opens
  React.useEffect(() => {
    if (isOpen) {
      console.log('ComprehensiveLogPanel: Loading sessions...');
      fetchSessions();
    }
  }, [isOpen]);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getLogSessions() as { sessions: LogSession[] };
      console.log('Sessions loaded:', response.sessions?.length || 0);
      setSessions(response.sessions || []);

      // Auto-select current session or most recent
      if (!selectedSession && response.sessions?.length > 0) {
        const sessionToSelect = currentSessionId || response.sessions[0].session_id;
        setSelectedSession(sessionToSelect);
        await fetchSessionSummary(sessionToSelect);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load log sessions';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionSummary = async (sessionId: string) => {
    try {
      const summary = await apiService.getSessionSummary(sessionId) as SessionSummary;
      setSessionSummary(summary);
    } catch (error) {
      console.error('Failed to fetch session summary:', error);
      toast.error(`Failed to load summary for session ${sessionId}`);
    }
  };

  const handleSessionChange = async (sessionId: string) => {
    setSelectedSession(sessionId);
    await fetchSessionSummary(sessionId);
  };

  // Performance metrics component
  const PerformanceMetrics = () => (
    <div className="p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Overview</h3>
      {sessionSummary ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-900">Total Events</p>
                <p className="text-2xl font-bold text-blue-600">{sessionSummary.total_events}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-900">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {sessionSummary.total_events > 0
                    ? Math.round(((sessionSummary.total_events - sessionSummary.error_count) / sessionSummary.total_events) * 100)
                    : 100}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="flex items-center">
              <UserIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-purple-900">Active Agents</p>
                <p className="text-2xl font-bold text-purple-600">
                  {Object.keys(sessionSummary.agent_activity || {}).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 p-4 rounded-lg">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-900">Errors</p>
                <p className="text-2xl font-bold text-red-600">{sessionSummary.error_count}</p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-500">Select a session to view performance metrics</p>
        </div>
      )}

      {sessionSummary && Object.keys(sessionSummary.event_counts || {}).length > 0 && (
        <div className="mt-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Event Distribution</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(sessionSummary.event_counts).map(([eventType, count]) => (
              <div key={eventType} className="bg-gray-50 p-3 rounded-lg">
                <p className="text-xs text-gray-600 truncate">{eventType}</p>
                <p className="text-lg font-semibold text-gray-900">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Errors and issues component
  const ErrorsAndIssues = () => (
    <div className="p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Errors & Issues Analysis</h3>

      {selectedSession ? (
        <LogViewer
          sessionId={selectedSession}
          className="border-0 shadow-none"
        />
      ) : (
        <div className="text-center py-8">
          <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Select a session to view errors and issues</p>
        </div>
      )}
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />

      <motion.div
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="absolute right-0 top-0 h-full w-full max-w-6xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Log Management Center</h2>
            <p className="text-sm text-gray-600">
              Comprehensive monitoring for user actions, system logs, and performance metrics
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-2 hover:bg-gray-200 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Session Selector */}
        <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Session
              </label>
              <select
                value={selectedSession || ''}
                onChange={(e) => handleSessionChange(e.target.value)}
                className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
                disabled={loading}
              >
                <option value="">Select a session...</option>
                {sessions.map((session) => (
                  <option key={session.session_id} value={session.session_id}>
                    {session.session_id} - {new Date(session.created_at).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>

            {sessionSummary && (
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center">
                  <DocumentTextIcon className="h-4 w-4 mr-1" />
                  {sessionSummary.total_events} events
                </div>
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                  {sessionSummary.error_count} errors
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  sessionSummary.status === 'success'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {sessionSummary.status.toUpperCase()}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
            <Tab.List className="flex">
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.name}
                  className={({ selected }) =>
                    `flex-1 px-6 py-3 text-sm font-medium focus:outline-none transition-colors ${
                      selected
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                    }`
                  }
                >
                  <div className="flex items-center justify-center space-x-2">
                    <tab.icon className="h-4 w-4" />
                    <span>{tab.name}</span>
                  </div>
                </Tab>
              ))}
            </Tab.List>
          </Tab.Group>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={selectedTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading log data...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Failed to Load Logs
                    </h3>
                    <p className="text-gray-500 max-w-sm mb-4">{error}</p>
                    <button
                      onClick={() => fetchSessions()}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              ) : !selectedSession ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <ServerIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No Session Selected
                    </h3>
                    <p className="text-gray-500 max-w-sm">
                      Please select a session from the dropdown above to view {tabs[selectedTab].description.toLowerCase()}.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {selectedTab === 0 && (
                    <UserActivityDashboard
                      sessionId={selectedSession}
                      className="border-0 shadow-none h-full"
                    />
                  )}

                  {selectedTab === 1 && (
                    <div className="p-6">
                      <LogViewer
                        sessionId={selectedSession}
                        className="border-0 shadow-none"
                      />
                    </div>
                  )}

                  {selectedTab === 2 && (
                    <PerformanceMetrics />
                  )}

                  {selectedTab === 3 && (
                    <ErrorsAndIssues />
                  )}
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};

export default ComprehensiveLogPanel;