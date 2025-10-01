/**
 * Log API Types
 * TypeScript interfaces for logging and analytics
 */

import type { ID, ISODateString } from '../../types/common';

// Log Event
export interface LogEvent {
  timestamp: ISODateString;
  session_id: ID;
  event_type: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  details?: any;
  agent_id?: string;
  user_id?: string;
  duration_ms?: number;
  error?: string;
}

// Log Session
export interface LogSession {
  session_id: ID;
  created_at: ISODateString;
  modified_at: ISODateString;
  has_events: boolean;
  has_readable_logs: boolean;
  events_size?: number;
  session_log_size?: number;
}

// Session Summary
export interface SessionSummary {
  session_id: ID;
  total_events: number;
  start_time: ISODateString;
  end_time: ISODateString;
  event_counts: Record<string, number>;
  agent_activity: Record<string, number>;
  error_count: number;
  status: string;
}

// Performance Metrics
export interface PerformanceMetrics {
  session_id: ID;
  overview: {
    total_events: number;
    tool_calls: number;
    mcp_calls: number;
    errors: number;
    success_rate: number;
  };
  performance: {
    tool_calls: {
      min: number;
      max: number;
      avg: number;
      total: number;
    };
    mcp_calls: {
      min: number;
      max: number;
      avg: number;
      total: number;
    };
  };
  agent_activity: Record<string, {
    total_events: number;
    tool_calls: number;
    errors: number;
    total_duration: number;
  }>;
  time_series: Record<string, number>;
}

// Log Query Options
export interface LogQueryOptions {
  format?: 'json' | 'human';
  limit?: number;
  level?: string;
  event_type?: string;
  agent_id?: string;
  from_timestamp?: ISODateString;
  to_timestamp?: ISODateString;
}

// Frontend Error Logging
export interface FrontendErrorLog {
  error_id: string;
  timestamp: ISODateString;
  message: string;
  stack?: string;
  component_stack?: string;
  user_agent: string;
  url: string;
  context?: Record<string, any>;
}

// Application Logs
export interface ApplicationLog {
  timestamp: ISODateString;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  logger: string;
  message: string;
  module?: string;
  function?: string;
  line?: number;
  context?: Record<string, any>;
}

// Startup Logs
export interface StartupLog {
  timestamp: ISODateString;
  component: string;
  status: 'starting' | 'success' | 'error';
  message: string;
  duration_ms?: number;
  error?: string;
  details?: Record<string, any>;
}

// Log Export Options
export interface LogExportOptions {
  format: 'json' | 'zip';
  session_id?: ID;
  date_range?: {
    start: ISODateString;
    end: ISODateString;
  };
  levels?: string[];
  event_types?: string[];
}