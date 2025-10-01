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
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';

import LogViewer from './LogViewer';
import UserActivityDashboard from './UserActivityDashboard';
import { LogSession, SessionSummary } from '../types';
import { apiService } from "@/shared/api";
import { toast } from 'react-hot-toast';
import { BrandLogo } from './BrandLogo';
import { BrandedCard, BrandedButton, BrandedBadge, BrandedStatus } from './BrandedComponents';

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
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Performance Overview</h3>
        <p className="text-slate-600 dark:text-slate-400">System metrics and performance analytics</p>
      </div>

      {sessionSummary ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <BrandedCard variant="glass" className="p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <DocumentTextIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Total Events</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                    {sessionSummary.total_events}
                  </p>
                </div>
              </div>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
                  <ChartBarIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Success Rate</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                    {sessionSummary.total_events > 0
                      ? Math.round(((sessionSummary.total_events - sessionSummary.error_count) / sessionSummary.total_events) * 100)
                      : 100}%
                  </p>
                </div>
              </div>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                  <UserIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Active Agents</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    {Object.keys(sessionSummary.agent_activity || {}).length}
                  </p>
                </div>
              </div>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl flex items-center justify-center">
                  <ExclamationTriangleIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Errors</p>
                  <p className="text-2xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
                    {sessionSummary.error_count}
                  </p>
                </div>
              </div>
            </BrandedCard>
          </div>

          {Object.keys(sessionSummary.event_counts || {}).length > 0 && (
            <BrandedCard variant="outline" className="p-6">
              <h4 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-4">Event Distribution</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(sessionSummary.event_counts).map(([eventType, count]) => (
                  <div key={eventType} className="p-4 bg-gradient-to-br from-slate-50 to-violet-50/30 dark:from-slate-800 dark:to-violet-950/30 rounded-xl border border-violet-200/20 dark:border-violet-800/20">
                    <p className="text-xs font-medium text-slate-600 dark:text-slate-400 truncate">{eventType}</p>
                    <p className="text-lg font-bold text-slate-800 dark:text-slate-200">{count}</p>
                  </div>
                ))}
              </div>
            </BrandedCard>
          )}
        </div>
      ) : (
        <BrandedCard variant="glass" className="p-8 text-center">
          <div className="flex justify-center mb-4">
            <BrandLogo variant="icon" size="md" />
          </div>
          <h4 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">No Session Selected</h4>
          <p className="text-slate-600 dark:text-slate-400">Select a session to view performance metrics</p>
        </BrandedCard>
      )}
    </div>
  );

  // Errors and issues component
  const ErrorsAndIssues = () => (
    <div className="p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Errors & Issues Analysis</h3>
        <p className="text-slate-600 dark:text-slate-400">Comprehensive error tracking and debugging information</p>
      </div>

      {selectedSession ? (
        <BrandedCard variant="glass" className="p-6">
          <LogViewer
            sessionId={selectedSession}
            className="border-0 shadow-none"
          />
        </BrandedCard>
      ) : (
        <BrandedCard variant="glass" className="p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl flex items-center justify-center">
              <ExclamationTriangleIcon className="h-8 w-8 text-white" />
            </div>
          </div>
          <h4 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">No Session Selected</h4>
          <p className="text-slate-600 dark:text-slate-400">Select a session to view errors and issues</p>
        </BrandedCard>
      )}
    </div>
  );

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-gradient-to-br from-slate-900/80 via-violet-900/50 to-cyan-900/30 backdrop-blur-sm z-[70] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
        className="relative bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-violet-200/30 dark:border-violet-800/30 w-full max-w-7xl h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="relative flex items-center justify-between p-6 border-b border-violet-200/30 dark:border-violet-800/30">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5 rounded-t-3xl" />
          <div className="relative flex items-center space-x-4">
            <BrandLogo variant="icon" size="md" />
            <div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent">
                Log Management Center
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                Comprehensive monitoring for user actions, system logs, and performance metrics
              </p>
            </div>
          </div>
          <BrandedButton
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="p-2"
          >
            <XMarkIcon className="w-6 h-6" />
          </BrandedButton>
        </div>

        {/* Session Selector */}
        <div className="relative px-6 py-4 bg-gradient-to-r from-violet-50/50 to-indigo-50/30 dark:from-violet-950/30 dark:to-indigo-950/20 border-b border-violet-200/30 dark:border-violet-800/30">
          <div className="flex items-center justify-between">
            <div className="flex-1 max-w-md">
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Session
              </label>
              <select
                value={selectedSession || ''}
                onChange={(e) => handleSessionChange(e.target.value)}
                className="w-full px-4 py-3 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm border border-violet-200/30 dark:border-violet-800/30 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 text-sm font-medium text-slate-700 dark:text-slate-300 transition-all duration-200"
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
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <BrandedBadge variant="secondary" size="sm">
                    <DocumentTextIcon className="h-3 w-3 mr-1" />
                    {sessionSummary.total_events} events
                  </BrandedBadge>
                  <BrandedBadge variant="warning" size="sm">
                    <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                    {sessionSummary.error_count} errors
                  </BrandedBadge>
                  <BrandedStatus
                    status={sessionSummary.status === 'success' ? 'active' : 'error'}
                    size="sm"
                  >
                    {sessionSummary.status.toUpperCase()}
                  </BrandedStatus>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-violet-200/30 dark:border-violet-800/30">
          <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
            <Tab.List className="flex">
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.name}
                  className={({ selected }) =>
                    `flex-1 px-6 py-4 text-sm font-semibold focus:outline-none transition-all duration-200 ${
                      selected
                        ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 bg-gradient-to-r from-indigo-50/50 to-purple-50/30 dark:from-indigo-950/30 dark:to-purple-950/20'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-violet-50/50 dark:hover:bg-violet-950/30'
                    }`
                  }
                >
                  <div className="flex items-center justify-center space-x-2">
                    <tab.icon className="h-5 w-5" />
                    <span>{tab.name}</span>
                  </div>
                </Tab>
              ))}
            </Tab.List>
          </Tab.Group>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-indigo-300 dark:scrollbar-thumb-indigo-600 scrollbar-track-transparent">
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
                <div className="flex items-center justify-center h-full p-8">
                  <BrandedCard variant="glass" className="p-8 text-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                      <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    </div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">Loading Log Data</h3>
                    <p className="text-slate-600 dark:text-slate-400">Fetching comprehensive analytics...</p>
                  </BrandedCard>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full p-8">
                  <BrandedCard variant="glass" className="p-8 text-center max-w-md">
                    <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                      <ExclamationTriangleIcon className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
                      Failed to Load Logs
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-6">{error}</p>
                    <BrandedButton
                      variant="primary"
                      onClick={() => fetchSessions()}
                    >
                      Retry Loading
                    </BrandedButton>
                  </BrandedCard>
                </div>
              ) : !selectedSession ? (
                <div className="flex items-center justify-center h-full p-8">
                  <BrandedCard variant="glass" className="p-8 text-center max-w-md">
                    <div className="flex justify-center mb-4">
                      <BrandLogo variant="icon" size="lg" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
                      No Session Selected
                    </h3>
                    <p className="text-slate-600 dark:text-slate-400">
                      Please select a session from the dropdown above to view {tabs[selectedTab].description.toLowerCase()}.
                    </p>
                  </BrandedCard>
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
                      <div className="mb-6">
                        <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Session Logs</h3>
                        <p className="text-slate-600 dark:text-slate-400">Detailed system logs and agent activity</p>
                      </div>
                      <BrandedCard variant="glass" className="p-6">
                        <LogViewer
                          sessionId={selectedSession}
                          className="border-0 shadow-none"
                        />
                      </BrandedCard>
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
    </motion.div>
  );
};

export default ComprehensiveLogPanel;