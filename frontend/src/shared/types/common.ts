/**
 * Common Types
 * Shared TypeScript types used across the application
 */

// Base utility types
export type ID = string;
export type Timestamp = number;
export type ISODateString = string;

// API Response wrapper
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

// Pagination
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// Status types
export type Status = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T = any> {
  data: T | null;
  status: Status;
  error: string | null;
  lastUpdated?: Timestamp;
}

// Form types
export interface FormFieldError {
  field: string;
  message: string;
  code?: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: FormFieldError[];
}

// File types
export interface FileUpload {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Log levels
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

// Event types
export interface AppEvent<T = any> {
  type: string;
  payload: T;
  timestamp: Timestamp;
  source?: string;
}

// User preference types
export interface UserPreferences {
  theme: Theme;
  sidebarExpanded: boolean;
  language: string;
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
  };
  appearance: {
    density: 'compact' | 'normal' | 'spacious';
    fontSize: 'small' | 'medium' | 'large';
  };
}

// Search and filter types
export interface SearchParams {
  query?: string;
  filters?: Record<string, any>;
  dateRange?: {
    start: ISODateString;
    end: ISODateString;
  };
}

// Component props
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  testId?: string;
}

// Modal and dialog types
export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

// Error types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: Timestamp;
  stack?: string;
}

// Navigation types
export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ComponentType;
}

// Data table types
export interface TableColumn<T = any> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T, index: number) => React.ReactNode;
  width?: string | number;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  error?: string;
  pagination?: {
    current: number;
    total: number;
    pageSize: number;
    onChange: (page: number) => void;
  };
  selection?: {
    selectedRows: T[];
    onSelectionChange: (rows: T[]) => void;
  };
}

// Form component types
export interface InputProps extends BaseComponentProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url';
}

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  icon?: React.ComponentType;
}

export interface SelectProps extends BaseComponentProps {
  label?: string;
  value?: string | number;
  onChange?: (value: string | number) => void;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  searchable?: boolean;
  multiple?: boolean;
}

// Animation types
export interface AnimationConfig {
  duration: number;
  easing: string;
  delay?: number;
}

// WebSocket types
export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  id?: string;
  timestamp: Timestamp;
}

// Context types
export interface ContextValue<T> {
  data: T;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}