# =========================================
# File: app/telemetry/user_actions.py
# Purpose: Specialized telemetry for user-driven UI actions and customizations
# =========================================
from __future__ import annotations
import time
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.telemetry.session_logger import session_logger, EventType, LogLevel


class UserActionType(str, Enum):
    """Types of user actions that can be tracked"""
    # Agent Management
    AGENT_CREATE_START = "agent_create_start"
    AGENT_CREATE_SUCCESS = "agent_create_success"
    AGENT_CREATE_FAILED = "agent_create_failed"
    AGENT_UPDATE = "agent_update"
    AGENT_DELETE = "agent_delete"
    AGENT_VALIDATE = "agent_validate"
    AGENT_TEST = "agent_test"

    # Tool Management
    TOOL_CREATE_START = "tool_create_start"
    TOOL_CREATE_SUCCESS = "tool_create_success"
    TOOL_CREATE_FAILED = "tool_create_failed"
    TOOL_UPDATE = "tool_update"
    TOOL_DELETE = "tool_delete"
    TOOL_VALIDATE = "tool_validate"
    TOOL_CODE_EDIT = "tool_code_edit"

    # MCP Management
    MCP_CREATE_START = "mcp_create_start"
    MCP_CREATE_SUCCESS = "mcp_create_success"
    MCP_CREATE_FAILED = "mcp_create_failed"
    MCP_UPDATE = "mcp_update"
    MCP_DELETE = "mcp_delete"
    MCP_TEST_CONNECTION = "mcp_test_connection"
    MCP_VALIDATE = "mcp_validate"

    # Group Management
    GROUP_CREATE = "group_create"
    GROUP_DELETE = "group_delete"
    GROUP_RENAME = "group_rename"
    GROUP_AGENT_ADD = "group_agent_add"
    GROUP_AGENT_REMOVE = "group_agent_remove"

    # Conversation Actions
    MESSAGE_SEND = "message_send"
    DOCUMENT_UPLOAD = "document_upload"
    AGENT_CONVERSATION_START = "agent_conversation_start"

    # Settings Management
    SETTINGS_UPDATE = "settings_update"
    SETTINGS_RESET = "settings_reset"
    SETTINGS_BACKUP = "settings_backup"
    SETTINGS_VALIDATE = "settings_validate"

    # UI Navigation
    PAGE_VIEW = "page_view"
    PANEL_OPEN = "panel_open"
    PANEL_CLOSE = "panel_close"

    # User Errors
    VALIDATION_ERROR = "validation_error"
    USER_INPUT_ERROR = "user_input_error"
    UI_ERROR = "ui_error"


@dataclass
class UserActionEvent:
    """Structured user action event with rich context"""
    timestamp: str
    session_id: str
    action_type: UserActionType
    user_id: Optional[str]
    success: bool
    duration_ms: Optional[float]

    # Context data
    resource_type: Optional[str]  # agent, tool, mcp, group, etc.
    resource_id: Optional[str]
    resource_name: Optional[str]

    # Action details
    action_data: Optional[Dict[str, Any]]
    validation_errors: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]

    # User context
    user_agent: Optional[str]
    ip_address: Optional[str]
    page_url: Optional[str]

    # Performance data
    complexity_score: Optional[int]  # For complex operations like agent creation
    data_size: Optional[int]  # Size of data being processed


class UserActionTracker:
    """Comprehensive tracker for user-driven actions with specialized monitoring"""

    def __init__(self):
        self.active_operations: Dict[str, float] = {}  # Track operation start times

    def _generate_operation_id(self, action_type: UserActionType, resource_id: str = None) -> str:
        """Generate unique operation ID for tracking multi-step actions"""
        base = f"{action_type.value}_{resource_id or 'unknown'}_{time.time()}"
        return hashlib.md5(base.encode()).hexdigest()[:12]

    def start_operation(self,
                       session_id: str,
                       action_type: UserActionType,
                       resource_type: str = None,
                       resource_id: str = None,
                       context: Dict[str, Any] = None) -> str:
        """Start tracking a multi-step user operation"""
        operation_id = self._generate_operation_id(action_type, resource_id)
        self.active_operations[operation_id] = time.time()

        # Log operation start
        self.track_action(
            session_id=session_id,
            action_type=action_type,
            success=True,
            resource_type=resource_type,
            resource_id=resource_id,
            action_data={
                "operation_id": operation_id,
                "operation_phase": "start",
                **(context or {})
            }
        )

        return operation_id

    def complete_operation(self,
                          session_id: str,
                          operation_id: str,
                          action_type: UserActionType,
                          success: bool,
                          resource_type: str = None,
                          resource_id: str = None,
                          result_data: Dict[str, Any] = None,
                          error_message: str = None,
                          validation_errors: List[Dict[str, Any]] = None):
        """Complete a tracked operation with results"""
        start_time = self.active_operations.pop(operation_id, time.time())
        duration_ms = (time.time() - start_time) * 1000

        # Determine the completion action type
        if success:
            if action_type.value.endswith('_start'):
                completion_type = UserActionType(action_type.value.replace('_start', '_success'))
            else:
                completion_type = action_type
        else:
            if action_type.value.endswith('_start'):
                completion_type = UserActionType(action_type.value.replace('_start', '_failed'))
            else:
                completion_type = UserActionType.USER_INPUT_ERROR

        self.track_action(
            session_id=session_id,
            action_type=completion_type,
            success=success,
            duration_ms=duration_ms,
            resource_type=resource_type,
            resource_id=resource_id,
            action_data={
                "operation_id": operation_id,
                "operation_phase": "complete",
                **(result_data or {})
            },
            error_message=error_message,
            validation_errors=validation_errors
        )

    def track_action(self,
                    session_id: str,
                    action_type: UserActionType,
                    success: bool = True,
                    duration_ms: float = None,
                    resource_type: str = None,
                    resource_id: str = None,
                    resource_name: str = None,
                    action_data: Dict[str, Any] = None,
                    validation_errors: List[Dict[str, Any]] = None,
                    error_message: str = None,
                    user_context: Dict[str, Any] = None):
        """Track a complete user action with full context"""

        event = UserActionEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            session_id=session_id,
            action_type=action_type,
            user_id=user_context.get('user_id') if user_context else None,
            success=success,
            duration_ms=duration_ms,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action_data=action_data,
            validation_errors=validation_errors,
            error_message=error_message,
            user_agent=user_context.get('user_agent') if user_context else None,
            ip_address=user_context.get('ip_address') if user_context else None,
            page_url=user_context.get('page_url') if user_context else None,
            complexity_score=self._calculate_complexity(action_type, action_data),
            data_size=self._calculate_data_size(action_data)
        )

        # Log to session logger with appropriate level
        level = LogLevel.ERROR if not success else LogLevel.INFO
        event_type = EventType.ERROR_OCCURRED if not success else EventType.SYSTEM_EVENT

        message = self._format_action_message(event)

        session_logger.log_event(
            session_id=session_id,
            event_type=event_type,
            level=level,
            message=message,
            details=asdict(event),
            duration_ms=duration_ms
        )

        # Special handling for critical user actions
        if self._is_critical_action(action_type):
            self._handle_critical_action(event)

    def track_validation_error(self,
                              session_id: str,
                              resource_type: str,
                              field_name: str,
                              field_value: Any,
                              validation_rule: str,
                              error_message: str,
                              form_data: Dict[str, Any] = None):
        """Track validation errors from user inputs"""
        self.track_action(
            session_id=session_id,
            action_type=UserActionType.VALIDATION_ERROR,
            success=False,
            resource_type=resource_type,
            action_data={
                "field_name": field_name,
                "field_value": str(field_value)[:100],  # Truncate for safety
                "validation_rule": validation_rule,
                "form_data_fields": list(form_data.keys()) if form_data else []
            },
            error_message=error_message
        )

    def track_ui_interaction(self,
                           session_id: str,
                           interaction_type: str,
                           component_name: str,
                           interaction_data: Dict[str, Any] = None):
        """Track user interactions with UI components"""
        self.track_action(
            session_id=session_id,
            action_type=UserActionType.PAGE_VIEW if interaction_type == 'page_view' else UserActionType.PANEL_OPEN,
            success=True,
            resource_type="ui_component",
            resource_id=component_name,
            action_data={
                "interaction_type": interaction_type,
                "component_name": component_name,
                **(interaction_data or {})
            }
        )

    def _calculate_complexity(self, action_type: UserActionType, action_data: Dict[str, Any] = None) -> int:
        """Calculate complexity score for the action (1-10)"""
        base_complexity = {
            UserActionType.AGENT_CREATE_START: 8,
            UserActionType.TOOL_CREATE_START: 6,
            UserActionType.MCP_CREATE_START: 7,
            UserActionType.SETTINGS_UPDATE: 5,
            UserActionType.GROUP_CREATE: 3,
            UserActionType.MESSAGE_SEND: 2,
        }

        complexity = base_complexity.get(action_type, 3)

        # Adjust based on action data
        if action_data:
            if 'code' in action_data:
                complexity += 2  # Code editing is more complex
            if 'validation_errors' in action_data:
                complexity += 1  # Validation adds complexity
            if action_data.get('is_custom_template'):
                complexity += 2  # Custom templates are more complex

        return min(complexity, 10)

    def _calculate_data_size(self, action_data: Dict[str, Any] = None) -> Optional[int]:
        """Calculate the size of data being processed"""
        if not action_data:
            return None

        try:
            return len(json.dumps(action_data, default=str))
        except:
            return None

    def _format_action_message(self, event: UserActionEvent) -> str:
        """Format human-readable message for the action"""
        action_map = {
            UserActionType.AGENT_CREATE_START: f"🤖 User started creating agent '{event.resource_name or event.resource_id}'",
            UserActionType.AGENT_CREATE_SUCCESS: f"✅ Agent '{event.resource_name}' created successfully",
            UserActionType.AGENT_CREATE_FAILED: f"❌ Agent creation failed: {event.error_message}",
            UserActionType.TOOL_CREATE_START: f"🔧 User started creating tool '{event.resource_name or event.resource_id}'",
            UserActionType.TOOL_CREATE_SUCCESS: f"✅ Tool '{event.resource_name}' created successfully",
            UserActionType.TOOL_CREATE_FAILED: f"❌ Tool creation failed: {event.error_message}",
            UserActionType.MCP_CREATE_START: f"🌐 User started creating MCP server '{event.resource_name or event.resource_id}'",
            UserActionType.MCP_CREATE_SUCCESS: f"✅ MCP server '{event.resource_name}' created successfully",
            UserActionType.MCP_CREATE_FAILED: f"❌ MCP server creation failed: {event.error_message}",
            UserActionType.VALIDATION_ERROR: f"⚠️ Validation error in {event.resource_type}: {event.error_message}",
            UserActionType.SETTINGS_UPDATE: f"⚙️ User updated settings",
            UserActionType.GROUP_CREATE: f"👥 User created group '{event.resource_name}'",
            UserActionType.MESSAGE_SEND: f"💬 User sent message to {event.resource_id}",
        }

        return action_map.get(event.action_type, f"📝 User action: {event.action_type.value}")

    def _is_critical_action(self, action_type: UserActionType) -> bool:
        """Determine if an action is critical and needs special handling"""
        critical_actions = {
            UserActionType.AGENT_CREATE_FAILED,
            UserActionType.TOOL_CREATE_FAILED,
            UserActionType.MCP_CREATE_FAILED,
            UserActionType.SETTINGS_RESET,
        }
        return action_type in critical_actions

    def _handle_critical_action(self, event: UserActionEvent):
        """Handle critical actions that might need immediate attention"""
        print(f"🚨 CRITICAL USER ACTION: {event.action_type.value}")
        print(f"   Session: {event.session_id}")
        print(f"   Resource: {event.resource_type}/{event.resource_id}")
        if event.error_message:
            print(f"   Error: {event.error_message}")

    def get_user_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of user actions for a session"""
        # This would typically query the session logs
        # For now, return a placeholder structure
        return {
            "session_id": session_id,
            "total_actions": 0,
            "actions_by_type": {},
            "error_rate": 0.0,
            "complexity_score": 0,
            "most_used_features": [],
            "problem_areas": []
        }


# Global instance for tracking user actions
user_action_tracker = UserActionTracker()


# Convenience functions for common user actions
def track_agent_creation(session_id: str, agent_data: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
    """Track agent creation workflow"""
    return user_action_tracker.start_operation(
        session_id=session_id,
        action_type=UserActionType.AGENT_CREATE_START,
        resource_type="agent",
        resource_id=agent_data.get('key'),
        context={
            "agent_type": agent_data.get('type'),
            "has_custom_tools": bool(agent_data.get('tools')),
            "has_mcp_servers": bool(agent_data.get('mcp_servers')),
            "complexity": len(agent_data.get('description', '')) > 100
        }
    )

def track_tool_creation(session_id: str, tool_data: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
    """Track tool creation workflow"""
    return user_action_tracker.start_operation(
        session_id=session_id,
        action_type=UserActionType.TOOL_CREATE_START,
        resource_type="tool",
        resource_id=tool_data.get('name'),
        context={
            "tool_type": tool_data.get('type'),
            "has_custom_code": bool(tool_data.get('code')),
            "function_count": len(tool_data.get('functions', [])),
            "code_length": len(tool_data.get('code', ''))
        }
    )

def track_mcp_creation(session_id: str, mcp_data: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
    """Track MCP server creation workflow"""
    return user_action_tracker.start_operation(
        session_id=session_id,
        action_type=UserActionType.MCP_CREATE_START,
        resource_type="mcp_server",
        resource_id=mcp_data.get('name'),
        context={
            "server_type": mcp_data.get('type'),
            "connection_type": mcp_data.get('connection', {}).get('type'),
            "has_custom_config": bool(mcp_data.get('config')),
            "tool_count": len(mcp_data.get('tools', []))
        }
    )

def track_user_input_validation(session_id: str, resource_type: str, field_name: str,
                               field_value: Any, validation_error: str):
    """Track validation errors from user inputs"""
    user_action_tracker.track_validation_error(
        session_id=session_id,
        resource_type=resource_type,
        field_name=field_name,
        field_value=field_value,
        validation_rule="user_input_validation",
        error_message=validation_error
    )
