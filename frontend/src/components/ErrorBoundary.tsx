import React, { Component, ReactNode } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo, errorId: string) => void;
}

// Enhanced error logging service for frontend
class FrontendErrorLogger {
  private static instance: FrontendErrorLogger;
  private errors: Array<{
    id: string;
    timestamp: string;
    error: Error;
    errorInfo?: React.ErrorInfo;
    userAgent: string;
    url: string;
    userId?: string;
    context?: Record<string, any>;
  }> = [];

  static getInstance(): FrontendErrorLogger {
    if (!FrontendErrorLogger.instance) {
      FrontendErrorLogger.instance = new FrontendErrorLogger();
    }
    return FrontendErrorLogger.instance;
  }

  private constructor() {
    // Set up global error handlers
    this.setupGlobalErrorHandlers();
  }

  private setupGlobalErrorHandlers() {
    // Handle unhandled JavaScript errors
    window.addEventListener('error', (event) => {
      this.logError(event.error || new Error(event.message), {
        type: 'javascript_error',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError(
        event.reason instanceof Error ? event.reason : new Error(String(event.reason)),
        { type: 'unhandled_promise_rejection' }
      );
    });

    // Handle console errors
    const originalConsoleError = console.error;
    console.error = (...args) => {
      this.logError(new Error(args.join(' ')), { type: 'console_error' });
      originalConsoleError.apply(console, args);
    };
  }

  logError(error: Error, context?: Record<string, any>, errorInfo?: React.ErrorInfo): string {
    const errorId = this.generateErrorId();
    const errorEntry = {
      id: errorId,
      timestamp: new Date().toISOString(),
      error,
      errorInfo,
      userAgent: navigator.userAgent,
      url: window.location.href,
      context
    };

    this.errors.unshift(errorEntry);

    // Keep only last 100 errors
    if (this.errors.length > 100) {
      this.errors = this.errors.slice(0, 100);
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.group(`🚨 Frontend Error [${errorId}]`);
      console.error('Error:', error);
      if (errorInfo) {
        console.error('Component Stack:', errorInfo.componentStack);
      }
      if (context) {
        console.error('Context:', context);
      }
      console.groupEnd();
    }

    // Send to backend logging service
    this.sendToBackend(errorEntry).catch(console.error);

    // Show user notification for critical errors
    if (this.isCriticalError(error)) {
      toast.error('Something went wrong. Our team has been notified.', {
        duration: 5000,
        id: errorId
      });
    }

    return errorId;
  }

  private async sendToBackend(errorEntry: any) {
    try {
      // Use centralized API service instead of direct fetch
      const { apiService } = await import('@/shared/api');
      await apiService.logFrontendError({
          error_id: errorEntry.id,
          timestamp: errorEntry.timestamp,
          message: errorEntry.error.message,
          stack: errorEntry.error.stack,
          component_stack: errorEntry.errorInfo?.componentStack,
          user_agent: errorEntry.userAgent,
          url: errorEntry.url,
          context: errorEntry.context
        });
    } catch (sendError) {
      console.error('Failed to send error to backend:', sendError);
    }
  }

  private isCriticalError(error: Error): boolean {
    const criticalPatterns = [
      /ChunkLoadError/,
      /Loading chunk \d+ failed/,
      /Cannot read prop/,
      /undefined is not a function/,
      /Network Error/
    ];

    return criticalPatterns.some(pattern => pattern.test(error.message));
  }

  private generateErrorId(): string {
    return `fe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getErrors() {
    return [...this.errors];
  }

  clearErrors() {
    this.errors = [];
  }
}

// Initialize the logger
const errorLogger = FrontendErrorLogger.getInstance();

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const errorId = errorLogger.logError(error, { type: 'react_error_boundary' }, errorInfo);

    this.setState({
      errorInfo,
      errorId
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo, errorId);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
              <div className="text-center">
                <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500" />
                <h2 className="mt-4 text-lg font-medium text-gray-900">
                  Something went wrong
                </h2>
                <p className="mt-2 text-sm text-gray-600">
                  We're sorry, but something unexpected happened. Our team has been notified and is working on a fix.
                </p>

                {import.meta.env.DEV && this.state.error && (
                  <div className="mt-4 p-3 bg-red-50 rounded-md">
                    <h3 className="text-sm font-medium text-red-800 mb-2">
                      Error Details (Development Mode)
                    </h3>
                    <div className="text-xs text-red-700 font-mono text-left overflow-auto max-h-32">
                      <div className="mb-2">
                        <strong>Error ID:</strong> {this.state.errorId}
                      </div>
                      <div className="mb-2">
                        <strong>Message:</strong> {this.state.error.message}
                      </div>
                      {this.state.error.stack && (
                        <div>
                          <strong>Stack:</strong>
                          <pre className="mt-1 whitespace-pre-wrap">
                            {this.state.error.stack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="mt-6 space-y-3">
                  <button
                    onClick={this.handleRetry}
                    className="w-full flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                  >
                    <ArrowPathIcon className="h-4 w-4 mr-2" />
                    Try Again
                  </button>

                  <button
                    onClick={this.handleReload}
                    className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                  >
                    Reload Page
                  </button>
                </div>

                <p className="mt-4 text-xs text-gray-500">
                  Error ID: {this.state.errorId}
                </p>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Export both the component and the logger for external use
export { ErrorBoundary, errorLogger };
export default ErrorBoundary;