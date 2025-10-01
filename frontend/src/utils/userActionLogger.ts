/**
 * Frontend User Action Logger
 * Tracks user interactions and form validation errors
 */

import { apiService } from "@/shared/api";

export interface UserActionContext {
  sessionId: string;
  userAgent?: string;
  pageUrl?: string;
  userId?: string;
}

export interface ValidationError {
  field: string;
  value: any;
  rule: string;
  message: string;
}

export interface UserAction {
  actionType: string;
  resourceType: string;
  resourceId?: string;
  resourceName?: string;
  success: boolean;
  startTime?: number;
  endTime?: number;
  data?: Record<string, any>;
  validationErrors?: ValidationError[];
  errorMessage?: string;
}

class UserActionLogger {
  private sessionId: string;
  private activeOperations: Map<string, number> = new Map();

  constructor() {
    this.sessionId = this.generateSessionId();
    this.setupGlobalHandlers();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalHandlers() {
    // Track form submission errors
    document.addEventListener('submit', this.handleFormSubmit.bind(this));

    // Track navigation
    window.addEventListener('beforeunload', this.handlePageUnload.bind(this));

    // Track validation errors from invalid form inputs
    document.addEventListener('invalid', this.handleInputInvalid.bind(this), true);
  }

  private handleFormSubmit(event: Event) {
    const form = event.target as HTMLFormElement;
    const formData = new FormData(form);
    const formAction = form.action || window.location.href;

    // Determine action type from form attributes
    let actionType = 'form_submit';
    let resourceType = 'form';

    if (form.dataset.actionType) {
      actionType = form.dataset.actionType;
    } else if (formAction.includes('agents')) {
      actionType = 'agent_form_submit';
      resourceType = 'agent';
    } else if (formAction.includes('tools')) {
      actionType = 'tool_form_submit';
      resourceType = 'tool';
    } else if (formAction.includes('mcp')) {
      actionType = 'mcp_form_submit';
      resourceType = 'mcp';
    }

    this.startOperation(actionType, {
      resourceType,
      resourceId: form.dataset.resourceId,
      data: {
        formFields: Array.from(formData.keys()),
        formAction: formAction,
        formMethod: form.method
      }
    });
  }

  private handlePageUnload() {
    // Log any incomplete operations
    this.activeOperations.forEach((startTime, operationId) => {
      this.completeOperation(operationId, {
        success: false,
        errorMessage: 'Operation interrupted by page unload'
      });
    });
  }

  private handleInputInvalid(event: Event) {
    const input = event.target as HTMLInputElement;

    this.trackValidationError({
      field: input.name || input.id || 'unknown',
      value: input.value,
      rule: this.getValidationRule(input),
      message: input.validationMessage
    }, {
      resourceType: this.getResourceTypeFromInput(input),
      resourceId: input.form?.dataset.resourceId
    });
  }

  private getValidationRule(input: HTMLInputElement): string {
    if (input.validity.valueMissing) return 'required';
    if (input.validity.typeMismatch) return 'type_mismatch';
    if (input.validity.patternMismatch) return 'pattern_mismatch';
    if (input.validity.tooLong) return 'max_length';
    if (input.validity.tooShort) return 'min_length';
    if (input.validity.rangeOverflow) return 'max_value';
    if (input.validity.rangeUnderflow) return 'min_value';
    return 'validation_error';
  }

  private getResourceTypeFromInput(input: HTMLInputElement): string {
    const form = input.form;
    if (!form) return 'form';

    if (form.dataset.resourceType) return form.dataset.resourceType;

    // Infer from form class names or IDs
    const className = form.className.toLowerCase();
    const formId = form.id.toLowerCase();

    if (className.includes('agent') || formId.includes('agent')) return 'agent';
    if (className.includes('tool') || formId.includes('tool')) return 'tool';
    if (className.includes('mcp') || formId.includes('mcp')) return 'mcp';
    if (className.includes('group') || formId.includes('group')) return 'group';
    if (className.includes('setting') || formId.includes('setting')) return 'settings';

    return 'form';
  }

  startOperation(actionType: string, context: {
    resourceType: string;
    resourceId?: string;
    resourceName?: string;
    data?: Record<string, any>;
  }): string {
    const operationId = `${actionType}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    this.activeOperations.set(operationId, Date.now());

    this.trackAction({
      actionType: `${actionType}_start`,
      resourceType: context.resourceType,
      resourceId: context.resourceId,
      resourceName: context.resourceName,
      success: true,
      data: {
        operationId,
        phase: 'start',
        ...context.data
      }
    });

    return operationId;
  }

  completeOperation(operationId: string, result: {
    success: boolean;
    resourceName?: string;
    data?: Record<string, any>;
    validationErrors?: ValidationError[];
    errorMessage?: string;
  }) {
    const startTime = this.activeOperations.get(operationId);
    if (!startTime) return;

    this.activeOperations.delete(operationId);
    const duration = Date.now() - startTime;

    // Extract action type from operation ID
    const actionType = operationId.split('_')[0];

    this.trackAction({
      actionType: result.success ? `${actionType}_success` : `${actionType}_failed`,
      resourceType: 'operation',
      resourceId: operationId,
      resourceName: result.resourceName,
      success: result.success,
      startTime,
      endTime: Date.now(),
      data: {
        operationId,
        phase: 'complete',
        duration_ms: duration,
        ...result.data
      },
      validationErrors: result.validationErrors,
      errorMessage: result.errorMessage
    });
  }

  trackAction(action: UserAction) {
    const context: UserActionContext = {
      sessionId: this.sessionId,
      userAgent: navigator.userAgent,
      pageUrl: window.location.href
    };

    // Calculate complexity score
    const complexityScore = this.calculateComplexity(action);

    // Log locally for immediate feedback
    if (process.env.NODE_ENV === 'development') {
      console.group(`🎯 User Action: ${action.actionType}`);
      console.log('Resource:', `${action.resourceType}/${action.resourceId}`);
      console.log('Success:', action.success);
      console.log('Duration:', action.endTime && action.startTime ? `${action.endTime - action.startTime}ms` : 'N/A');
      if (action.validationErrors?.length) {
        console.log('Validation Errors:', action.validationErrors);
      }
      if (action.errorMessage) {
        console.log('Error:', action.errorMessage);
      }
      console.groupEnd();
    }

    // Send to backend (fire and forget)
    this.sendToBackend(action, context).catch(error => {
      console.warn('Failed to send user action to backend:', error);
    });
  }

  trackValidationError(error: ValidationError, context: {
    resourceType: string;
    resourceId?: string;
  }) {
    this.trackAction({
      actionType: 'validation_error',
      resourceType: context.resourceType,
      resourceId: context.resourceId,
      success: false,
      validationErrors: [error],
      errorMessage: error.message,
      data: {
        field: error.field,
        rule: error.rule
      }
    });
  }

  trackUIInteraction(interactionType: string, componentName: string, data?: Record<string, any>) {
    this.trackAction({
      actionType: interactionType,
      resourceType: 'ui_component',
      resourceId: componentName,
      success: true,
      data: {
        component: componentName,
        interaction: interactionType,
        ...data
      }
    });
  }

  trackPageView(pageName: string, data?: Record<string, any>) {
    this.trackAction({
      actionType: 'page_view',
      resourceType: 'page',
      resourceId: pageName,
      success: true,
      data: {
        page: pageName,
        url: window.location.href,
        referrer: document.referrer,
        ...data
      }
    });
  }

  private calculateComplexity(action: UserAction): number {
    let complexity = 1;

    // Base complexity by action type
    if (action.actionType.includes('create')) complexity += 3;
    if (action.actionType.includes('update')) complexity += 2;
    if (action.actionType.includes('delete')) complexity += 2;
    if (action.actionType.includes('validation')) complexity += 1;

    // Resource type complexity
    if (action.resourceType === 'agent') complexity += 3;
    if (action.resourceType === 'tool') complexity += 2;
    if (action.resourceType === 'mcp') complexity += 2;

    // Data complexity
    if (action.data) {
      if (action.data.formFields && action.data.formFields.length > 5) complexity += 1;
      if (action.data.code) complexity += 2;
      if (action.data.config) complexity += 1;
    }

    // Error complexity
    if (action.validationErrors && action.validationErrors.length > 1) complexity += 1;

    return Math.min(complexity, 10);
  }

  private async sendToBackend(action: UserAction, context: UserActionContext) {
    try {
      await apiService.logFrontendError({
        error_id: `user_action_${Date.now()}`,
        timestamp: new Date().toISOString(),
        message: `User Action: ${action.actionType}`,
        user_agent: context.userAgent || '',
        url: context.pageUrl || '',
        context: {
          action,
          session_id: context.sessionId,
          complexity_score: this.calculateComplexity(action)
        }
      });
    } catch (error) {
      // Silently fail - don't disrupt user experience
      console.debug('Failed to log user action:', error);
    }
  }

  getSessionId(): string {
    return this.sessionId;
  }

  getActiveOperations(): string[] {
    return Array.from(this.activeOperations.keys());
  }
}

// Global instance
export const userActionLogger = new UserActionLogger();

// Convenience functions
export const trackAgentCreation = (agentData: Record<string, any>) => {
  return userActionLogger.startOperation('agent_create', {
    resourceType: 'agent',
    resourceId: agentData.key || agentData.name,
    resourceName: agentData.name,
    data: {
      hasTools: !!agentData.tools_code,
      hasMcpConfig: !!agentData.mcp_config,
      selectedToolsCount: agentData.selected_tools?.length || 0,
      selectedMcpsCount: agentData.selected_mcps?.length || 0
    }
  });
};

export const trackToolCreation = (toolData: Record<string, any>) => {
  return userActionLogger.startOperation('tool_create', {
    resourceType: 'tool',
    resourceId: toolData.name,
    resourceName: toolData.name,
    data: {
      hasCode: !!toolData.code,
      codeLength: toolData.code?.length || 0,
      functionCount: toolData.functions?.length || 0
    }
  });
};

export const trackMcpCreation = (mcpData: Record<string, any>) => {
  return userActionLogger.startOperation('mcp_create', {
    resourceType: 'mcp',
    resourceId: mcpData.name,
    resourceName: mcpData.name,
    data: {
      serverType: mcpData.type,
      hasConfig: !!mcpData.config,
      toolCount: mcpData.tools?.length || 0
    }
  });
};

export const trackFormValidationError = (field: string, value: any, rule: string, message: string, resourceType: string) => {
  userActionLogger.trackValidationError({
    field,
    value,
    rule,
    message
  }, {
    resourceType
  });
};

export default userActionLogger;