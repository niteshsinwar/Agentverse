/**
 * Debug Logger
 * Enhanced logging system for development and debugging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  component: string;
  message: string;
  data?: any;
}

class DebugLogger {
  private static instance: DebugLogger;
  private isDebugMode: boolean = false;
  private logs: LogEntry[] = [];
  private maxLogs: number = 1000;

  private constructor() {
    this.loadDebugMode();
  }

  static getInstance(): DebugLogger {
    if (!DebugLogger.instance) {
      DebugLogger.instance = new DebugLogger();
    }
    return DebugLogger.instance;
  }

  private loadDebugMode() {
    try {
      const backendSettings = localStorage.getItem('app_settings');
      if (backendSettings) {
        const settings = JSON.parse(backendSettings);
        this.isDebugMode = settings.debug ?? false;
      }
    } catch (error) {
      console.error('Failed to load debug settings:', error);
    }
  }

  setDebugMode(enabled: boolean) {
    this.isDebugMode = enabled;
    if (enabled) {
      this.info('Debug Logger', 'Debug mode enabled - verbose logging active');
    }
  }

  isDebugEnabled(): boolean {
    return this.isDebugMode;
  }

  private log(level: LogLevel, component: string, message: string, data?: any) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      component,
      message,
      data
    };

    // Add to internal log history
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Console output with enhanced formatting
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[${timestamp}] [${component}]`;

    switch (level) {
      case 'debug':
        if (this.isDebugMode) {
          console.log(`🔍 ${prefix}`, message, data || '');
        }
        break;
      case 'info':
        console.info(`ℹ️ ${prefix}`, message, data || '');
        break;
      case 'warn':
        console.warn(`⚠️ ${prefix}`, message, data || '');
        break;
      case 'error':
        console.error(`❌ ${prefix}`, message, data || '');
        break;
    }
  }

  debug(component: string, message: string, data?: any) {
    this.log('debug', component, message, data);
  }

  info(component: string, message: string, data?: any) {
    this.log('info', component, message, data);
  }

  warn(component: string, message: string, data?: any) {
    this.log('warn', component, message, data);
  }

  error(component: string, message: string, data?: any) {
    this.log('error', component, message, data);
  }

  // Get recent logs for debug panel
  getRecentLogs(count: number = 100): LogEntry[] {
    return this.logs.slice(-count);
  }

  // Clear logs
  clearLogs() {
    this.logs = [];
    this.info('Debug Logger', 'Log history cleared');
  }

  // Export logs for debugging
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

// Export singleton instance
export const debugLogger = DebugLogger.getInstance();
export default debugLogger;