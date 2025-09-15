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
}

export interface Message {
  id: number;
  group_id: string;
  sender: string;
  role: 'user' | 'agent' | 'system';
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