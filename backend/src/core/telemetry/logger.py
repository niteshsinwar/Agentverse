# =========================================
# File: app/telemetry/logger.py
# Purpose: Enhanced JSON logger with comprehensive error tracking and context
# =========================================
import logging, json, sys, time, traceback, threading, psutil, os
from typing import Dict, Any, Optional
from src.core.telemetry.context import get_context

class EnhancedJsonFormatter(logging.Formatter):
    """Enhanced JSON formatter with comprehensive error tracking and system context"""

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_context()

        # Basic payload
        payload = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "thread_id": threading.get_ident(),
            "process_id": os.getpid(),
            **ctx,
        }

        # Add system performance metrics for errors and warnings
        if record.levelno >= logging.WARNING:
            try:
                payload["system"] = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent if os.path.exists('/') else None
                }
            except Exception:
                pass  # Don't fail logging due to system metrics

        # Enhanced exception handling
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

            # Add stack trace analysis
            tb_lines = traceback.format_exception(*record.exc_info)
            payload["stack_trace"] = tb_lines
            payload["error_location"] = self._extract_error_location(tb_lines)

        # Add custom attributes from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                          'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage']:
                payload[f"custom_{key}"] = str(value) if not isinstance(value, (dict, list, int, float, bool)) else value

        return json.dumps(payload, ensure_ascii=False, default=str)

    def _extract_error_location(self, tb_lines: list) -> Optional[Dict[str, Any]]:
        """Extract precise error location from traceback"""
        if not tb_lines:
            return None

        try:
            # Find the last traceback line that contains our code (not library code)
            for line in reversed(tb_lines):
                if 'File "' in line and ('src/' in line or 'backend/' in line):
                    # Parse file, line number, and function
                    parts = line.strip().split(', ')
                    if len(parts) >= 3:
                        file_part = parts[0].replace('File "', '').replace('"', '')
                        line_part = parts[1].replace('line ', '')
                        func_part = parts[2].replace('in ', '') if len(parts) > 2 else 'unknown'

                        return {
                            "file": file_part,
                            "line": int(line_part) if line_part.isdigit() else None,
                            "function": func_part
                        }
        except Exception:
            pass

        return None


def init_enhanced_json_logger(level: int = logging.INFO):
    """Initialize enhanced JSON logger with comprehensive error tracking"""
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(EnhancedJsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)

def init_json_logger(level: int = logging.INFO):
    """Backward compatibility wrapper"""
    init_enhanced_json_logger(level)

# Enhanced logging utility functions
class ErrorCapture:
    """Utility class for capturing and logging minute-level errors"""

    @staticmethod
    def log_api_error(logger: logging.Logger, endpoint: str, method: str,
                     status_code: int, error_details: Any, request_data: Any = None):
        """Log API-specific errors with full context"""
        logger.error(
            f"API Error: {method} {endpoint}",
            extra={
                "error_type": "api_error",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "error_details": error_details,
                "request_data": request_data
            }
        )

    @staticmethod
    def log_agent_error(logger: logging.Logger, agent_id: str, operation: str,
                       error: Exception, context: Dict[str, Any] = None):
        """Log agent-specific errors with context"""
        logger.error(
            f"Agent Error: {agent_id} - {operation}",
            extra={
                "error_type": "agent_error",
                "agent_id": agent_id,
                "operation": operation,
                "context": context or {}
            },
            exc_info=True
        )

    @staticmethod
    def log_llm_error(logger: logging.Logger, provider: str, model: str,
                     prompt_length: int, error: Exception):
        """Log LLM-specific errors"""
        logger.error(
            f"LLM Error: {provider}/{model}",
            extra={
                "error_type": "llm_error",
                "provider": provider,
                "model": model,
                "prompt_length": prompt_length
            },
            exc_info=True
        )

    @staticmethod
    def log_mcp_error(logger: logging.Logger, server_name: str, tool_name: str,
                     error: Exception, params: Dict[str, Any] = None):
        """Log MCP-specific errors"""
        logger.error(
            f"MCP Error: {server_name}/{tool_name}",
            extra={
                "error_type": "mcp_error",
                "server_name": server_name,
                "tool_name": tool_name,
                "params": params or {}
            },
            exc_info=True
        )

    @staticmethod
    def log_database_error(logger: logging.Logger, operation: str, table: str,
                          error: Exception, query_info: Dict[str, Any] = None):
        """Log database-specific errors"""
        logger.error(
            f"Database Error: {operation} on {table}",
            extra={
                "error_type": "database_error",
                "operation": operation,
                "table": table,
                "query_info": query_info or {}
            },
            exc_info=True
        )

    @staticmethod
    def log_validation_error(logger: logging.Logger, field: str, value: Any,
                           validation_rule: str, error_msg: str):
        """Log validation errors with detailed context"""
        logger.warning(
            f"Validation Error: {field}",
            extra={
                "error_type": "validation_error",
                "field": field,
                "value": str(value)[:100],  # Truncate for safety
                "validation_rule": validation_rule,
                "error_message": error_msg
            }
        )

    @staticmethod
    def log_performance_warning(logger: logging.Logger, operation: str,
                              duration_ms: float, threshold_ms: float,
                              context: Dict[str, Any] = None):
        """Log performance warnings when operations exceed thresholds"""
        logger.warning(
            f"Performance Warning: {operation} took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)",
            extra={
                "error_type": "performance_warning",
                "operation": operation,
                "duration_ms": duration_ms,
                "threshold_ms": threshold_ms,
                "context": context or {}
            }
        )