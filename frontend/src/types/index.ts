// API Types matching the Python backend
export interface Group {
  id: string;
  name: string;
  created_at: number;
  updated_at: number;
}

export interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
  llm?: {
    provider: string;
    model: string;
  };
}

export interface Message {
  id: number;
  group_id: string;
  sender: string;
  role: 'user' | 'agent' | 'system' | 'tool_call' | 'tool_result' | 'mcp_call' | 'error' | 'agent_thought';
  content: string;
  metadata?: Record<string, any>;
  created_at: number;
}

export interface Document {
  document_id: string;
  filename: string;
  size: number;
  created_at: number;
  target_agent: string;
  sender: string;
  size_str: string;
  date_str: string;
  file_extension: string;
  content_summary?: string;
}

export interface EventMessage {
  type: string;
  data: Record<string, any>;
  timestamp: number;
}

// Log related types
export interface LogEvent {
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

export interface LogSession {
  session_id: string;
  created_at: string;
  modified_at: string;
  has_events: boolean;
  has_readable_logs: boolean;
  events_size?: number;
  session_log_size?: number;
}

export interface SessionSummary {
  session_id: string;
  total_events: number;
  start_time: string;
  end_time: string;
  event_counts: Record<string, number>;
  agent_activity: Record<string, number>;
  error_count: number;
  status: string;
}

export interface PerformanceMetrics {
  session_id: string;
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
