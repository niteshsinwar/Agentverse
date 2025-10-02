# =========================================
# File: app/telemetry/session_logger.py
# Purpose: Comprehensive session-wise logging with human-readable format
# =========================================
from __future__ import annotations
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler
from src.core.config.settings import get_settings; settings = get_settings()
from dataclasses import dataclass, asdict
from enum import Enum
import re

class LogLevel(str, Enum):
    """Log levels for different types of events"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    CRITICAL = "CRITICAL"

class EventType(str, Enum):
    """Types of events that can be logged"""
    GROUP_CREATED = "group_created"
    GROUP_RENAMED = "group_renamed"
    AGENT_ADDED = "agent_added"
    AGENT_REMOVED = "agent_removed"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    MCP_CALLED = "mcp_called"
    MCP_RESULT = "mcp_result"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_EVENT = "system_event"

@dataclass
class LogEvent:
    """Structured log event"""
    timestamp: str
    session_id: str
    event_type: EventType
    level: LogLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None

class SessionLogger:
    """Production-grade session-wise logger with human-readable formatting"""

    def __init__(self):
        self.base_log_dir = Path(settings.logging.session_logs_dir)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers: Dict[str, logging.Logger] = {}
        self.is_windows = sys.platform == 'win32'
        self._setup_root_logger()

    @staticmethod
    def _strip_emojis(text: str) -> str:
        """Remove emojis from text for Windows console compatibility"""
        # Remove emojis using regex
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # chinese char
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # dingbats
            u"\u3030"
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)
    
    def _setup_root_logger(self):
        """Setup root logger for the application"""
        root_logger = logging.getLogger("agentic_framework")
        root_logger.setLevel(getattr(logging, settings.logging.level.upper()))
        
        if not root_logger.handlers:
            # Console handler with Windows emoji stripping
            if settings.logging.enable_console_logging:
                console_handler = logging.StreamHandler()
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(console_formatter)

                # On Windows, filter emojis to prevent encoding errors
                if self.is_windows:
                    class EmojiFilter(logging.Filter):
                        def filter(self, record):
                            record.msg = SessionLogger._strip_emojis(str(record.msg))
                            return True
                    console_handler.addFilter(EmojiFilter())

                root_logger.addHandler(console_handler)
            
            # File handler for general logs with UTF-8 encoding
            if settings.logging.enable_file_logging:
                general_log_file = self.base_log_dir / "application.log"
                file_handler = RotatingFileHandler(
                    general_log_file,
                    maxBytes=settings.logging.max_file_size,
                    backupCount=settings.logging.backup_count,
                    encoding='utf-8'
                )
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
    
    def get_session_logger(self, session_id: str) -> logging.Logger:
        """Get or create a session-specific logger"""
        if session_id not in self._loggers:
            logger_name = f"session.{session_id}"
            session_logger = logging.getLogger(logger_name)
            session_logger.setLevel(getattr(logging, settings.logging.level.upper()))
            
            # Create session log directory
            session_log_dir = self.base_log_dir / session_id
            session_log_dir.mkdir(exist_ok=True)
            
            # Human-readable log file with UTF-8 encoding for cross-platform compatibility
            readable_log_file = session_log_dir / "session.log"
            readable_handler = RotatingFileHandler(
                readable_log_file,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            readable_formatter = logging.Formatter(
                '%(asctime)s | %(message)s'
            )
            readable_handler.setFormatter(readable_formatter)
            session_logger.addHandler(readable_handler)
            
            # JSON log file for structured data with UTF-8 encoding
            json_log_file = session_log_dir / "events.jsonl"
            json_handler = RotatingFileHandler(
                json_log_file,
                maxBytes=settings.logging.max_file_size,
                backupCount=settings.logging.backup_count,
                encoding='utf-8'
            )
            json_formatter = logging.Formatter('%(message)s')
            json_handler.setFormatter(json_formatter)
            json_handler.setLevel(logging.DEBUG)
            
            # Create a custom handler for JSON logs
            json_logger = logging.getLogger(f"session.{session_id}.json")
            json_logger.addHandler(json_handler)
            json_logger.setLevel(logging.DEBUG)
            json_logger.propagate = False
            
            self._loggers[session_id] = session_logger
            
            # Log session start
            self.log_event(
                session_id=session_id,
                event_type=EventType.SYSTEM_EVENT,
                level=LogLevel.INFO,
                message=f"📝 Session {session_id} logging started"
            )
        
        return self._loggers[session_id]
    
    def log_event(self, session_id: str, event_type: EventType, level: LogLevel, 
                  message: str, **kwargs):
        """Log an event with both human-readable and structured formats"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Create structured event
        event = LogEvent(
            timestamp=timestamp,
            session_id=session_id,
            event_type=event_type,
            level=level,
            message=message,
            **kwargs
        )
        
        # Get loggers
        session_logger = self.get_session_logger(session_id)
        json_logger = logging.getLogger(f"session.{session_id}.json")

        # Log human-readable format
        human_message = self._format_human_readable(event)
        log_level = getattr(logging, level.value.upper())

        # Strip emojis for console on Windows, keep for file
        console_message = self._strip_emojis(human_message) if self.is_windows else human_message
        session_logger.log(log_level, console_message)

        # Log JSON format
        json_logger.debug(json.dumps(asdict(event), default=str))
    
    def _format_human_readable(self, event: LogEvent) -> str:
        """Format event as human-readable message"""
        emoji_map = {
            EventType.GROUP_CREATED: "🆕",
            EventType.GROUP_RENAMED: "✏️",
            EventType.AGENT_ADDED: "➕",
            EventType.AGENT_REMOVED: "➖",
            EventType.MESSAGE_SENT: "💬",
            EventType.MESSAGE_RECEIVED: "📨",
            EventType.TOOL_CALLED: "🔧",
            EventType.TOOL_RESULT: "📤",
            EventType.MCP_CALLED: "🌐",
            EventType.MCP_RESULT: "📥",
            EventType.DOCUMENT_UPLOADED: "📄",
            EventType.DOCUMENT_PROCESSED: "🔄",
            EventType.ERROR_OCCURRED: "❌",
            EventType.SYSTEM_EVENT: "ℹ️"
        }
        
        emoji = emoji_map.get(event.event_type, "📝")
        base_message = f"{emoji} {event.message}"
        
        # Add agent info if present
        if event.agent_id:
            base_message += f" [Agent: {event.agent_id}]"
        
        # Add duration if present
        if event.duration_ms is not None:
            base_message += f" [Duration: {event.duration_ms:.2f}ms]"
        
        # Add error info if present
        if event.error:
            base_message += f" [Error: {event.error}]"
        
        # Add details if present and not too verbose
        if event.details:
            detail_str = self._format_details(event.details)
            if detail_str:
                base_message += f" [Details: {detail_str}]"
        
        return base_message
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary for human reading"""
        if not details:
            return ""
        
        # Keep it concise - only show key information
        important_keys = ["status", "result", "type", "count", "size", "name"]
        formatted_parts = []
        
        for key in important_keys:
            if key in details:
                value = details[key]
                if isinstance(value, (str, int, float, bool)):
                    formatted_parts.append(f"{key}={value}")
                elif isinstance(value, list):
                    formatted_parts.append(f"{key}={len(value)} items")
                elif isinstance(value, dict):
                    formatted_parts.append(f"{key}={len(value)} props")
        
        return ", ".join(formatted_parts[:3])  # Limit to 3 details
    
    def log_group_created(self, session_id: str, group_name: str, creator: str = "system"):
        """Log group creation"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.GROUP_CREATED,
            level=LogLevel.INFO,
            message=f"Group '{group_name}' created by {creator}",
            details={"group_name": group_name, "creator": creator}
        )
    
    def log_group_renamed(self, session_id: str, old_name: str, new_name: str, user: str = "system"):
        """Log group rename"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.GROUP_RENAMED,
            level=LogLevel.INFO,
            message=f"Group renamed from '{old_name}' to '{new_name}' by {user}",
            details={"old_name": old_name, "new_name": new_name, "user": user}
        )
    
    def log_agent_added(self, session_id: str, agent_id: str, group_name: str, user: str = "system"):
        """Log agent addition to group"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.AGENT_ADDED,
            level=LogLevel.INFO,
            message=f"Agent '{agent_id}' added to group '{group_name}' by {user}",
            agent_id=agent_id,
            details={"group_name": group_name, "user": user}
        )
    
    def log_agent_removed(self, session_id: str, agent_id: str, group_name: str, user: str = "system"):
        """Log agent removal from group"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.AGENT_REMOVED,
            level=LogLevel.INFO,
            message=f"Agent '{agent_id}' removed from group '{group_name}' by {user}",
            agent_id=agent_id,
            details={"group_name": group_name, "user": user}
        )
    
    def log_message(self, session_id: str, sender: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Log message exchange"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.MESSAGE_SENT if role == "user" else EventType.MESSAGE_RECEIVED,
            level=LogLevel.INFO,
            message=f"{sender} ({role}): {content[:100]}{'...' if len(content) > 100 else ''}",
            agent_id=sender if role != "user" else None,
            details={"role": role, "content_length": len(content), "metadata": metadata}
        )
    
    def log_tool_call(self, session_id: str, agent_id: str, tool_name: str, params: Dict[str, Any], 
                     duration_ms: Optional[float] = None, result: Any = None, error: Optional[str] = None):
        """Log tool call and result"""
        if error:
            self.log_event(
                session_id=session_id,
                event_type=EventType.ERROR_OCCURRED,
                level=LogLevel.ERROR,
                message=f"Tool call failed: {tool_name}",
                agent_id=agent_id,
                duration_ms=duration_ms,
                error=error,
                details={"tool_name": tool_name, "params": params}
            )
        else:
            self.log_event(
                session_id=session_id,
                event_type=EventType.TOOL_CALLED,
                level=LogLevel.INFO,
                message=f"Tool called: {tool_name}",
                agent_id=agent_id,
                duration_ms=duration_ms,
                details={"tool_name": tool_name, "params": params, "result": str(result)[:200] if result else None}
            )
    
    def log_mcp_call(self, session_id: str, agent_id: str, server_name: str, tool_name: str, 
                    params: Dict[str, Any], duration_ms: Optional[float] = None, 
                    result: Any = None, error: Optional[str] = None):
        """Log MCP call and result"""
        if error:
            self.log_event(
                session_id=session_id,
                event_type=EventType.ERROR_OCCURRED,
                level=LogLevel.ERROR,
                message=f"MCP call failed: {server_name}/{tool_name}",
                agent_id=agent_id,
                duration_ms=duration_ms,
                error=error,
                details={"server_name": server_name, "tool_name": tool_name, "params": params}
            )
        else:
            self.log_event(
                session_id=session_id,
                event_type=EventType.MCP_CALLED,
                level=LogLevel.INFO,
                message=f"MCP called: {server_name}/{tool_name}",
                agent_id=agent_id,
                duration_ms=duration_ms,
                details={
                    "server_name": server_name, 
                    "tool_name": tool_name, 
                    "params": params, 
                    "result": str(result)[:200] if result else None
                }
            )
    
    def log_error(self, session_id: str, error: Exception, context: str = "", 
                 agent_id: Optional[str] = None):
        """Log error with full context"""
        self.log_event(
            session_id=session_id,
            event_type=EventType.ERROR_OCCURRED,
            level=LogLevel.ERROR,
            message=f"Error in {context}: {str(error)}",
            agent_id=agent_id,
            error=str(error),
            details={
                "error_type": type(error).__name__,
                "context": context,
                "traceback": str(error)
            }
        )
    
    def log_document_upload(self, session_id: str, filename: str, size_bytes: int, 
                           agent_id: Optional[str] = None, user: str = "system"):
        """Log document upload"""
        size_mb = size_bytes / (1024 * 1024)
        self.log_event(
            session_id=session_id,
            event_type=EventType.DOCUMENT_UPLOADED,
            level=LogLevel.INFO,
            message=f"Document uploaded: {filename} ({size_mb:.2f}MB)",
            agent_id=agent_id,
            details={"filename": filename, "size_bytes": size_bytes, "size_mb": size_mb, "user": user}
        )
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of session activity"""
        json_log_file = self.base_log_dir / session_id / "events.jsonl"
        if not json_log_file.exists():
            return {"error": "No logs found for session"}
        
        events = []
        try:
            with open(json_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            return {"error": f"Failed to read logs: {e}"}
        
        if not events:
            return {"total_events": 0}
        
        # Calculate statistics
        event_counts = {}
        agent_activity = {}
        error_count = 0
        start_time = events[0]['timestamp'] if events else None
        end_time = events[-1]['timestamp'] if events else None
        
        for event in events:
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            if event.get('agent_id'):
                agent_id = event['agent_id']
                agent_activity[agent_id] = agent_activity.get(agent_id, 0) + 1
            
            if event.get('level') == 'ERROR':
                error_count += 1
        
        return {
            "session_id": session_id,
            "total_events": len(events),
            "start_time": start_time,
            "end_time": end_time,
            "event_counts": event_counts,
            "agent_activity": agent_activity,
            "error_count": error_count,
            "status": "error" if error_count > 0 else "success"
        }

# Global session logger instance
session_logger = SessionLogger()
