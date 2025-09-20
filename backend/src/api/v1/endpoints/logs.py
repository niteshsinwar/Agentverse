"""
Logs API Endpoints
RESTful endpoints for accessing and analyzing log data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from src.core.config.settings import get_settings
from src.core.telemetry.session_logger import session_logger

router = APIRouter()
settings = get_settings()


def parse_jsonl_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Parse JSONL log file and return structured events"""
    events = []
    if not file_path.exists():
        return events

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError as e:
                    # Log malformed line but continue processing
                    print(f"Warning: Malformed JSON in {file_path}:{line_num}: {e}")
                    continue
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")

    return events


def parse_human_readable_logs(file_path: Path) -> List[str]:
    """Parse human-readable log file and return lines"""
    lines = []
    if not file_path.exists():
        return lines

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"Error reading log file {file_path}: {e}")

    return lines


@router.get("/sessions")
async def list_log_sessions():
    """List all available log sessions"""
    base_log_dir = Path(settings.logging.session_logs_dir)

    if not base_log_dir.exists():
        return {"sessions": []}

    sessions = []
    for session_dir in base_log_dir.iterdir():
        if session_dir.is_dir() and session_dir.name not in ['startup']:
            session_info = {
                "session_id": session_dir.name,
                "created_at": datetime.fromtimestamp(session_dir.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(session_dir.stat().st_mtime).isoformat(),
                "has_events": (session_dir / "events.jsonl").exists(),
                "has_readable_logs": (session_dir / "session.log").exists()
            }

            # Get log file sizes
            events_file = session_dir / "events.jsonl"
            session_file = session_dir / "session.log"

            if events_file.exists():
                session_info["events_size"] = events_file.stat().st_size
            if session_file.exists():
                session_info["session_log_size"] = session_file.stat().st_size

            sessions.append(session_info)

    # Sort by modification time (newest first)
    sessions.sort(key=lambda x: x["modified_at"], reverse=True)

    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session_logs(
    session_id: str,
    format: str = Query("json", description="Format: 'json' for structured data, 'human' for readable format"),
    limit: Optional[int] = Query(None, description="Limit number of entries returned"),
    level: Optional[str] = Query(None, description="Filter by log level (ERROR, WARNING, INFO, DEBUG)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    from_timestamp: Optional[str] = Query(None, description="ISO timestamp to filter from"),
    to_timestamp: Optional[str] = Query(None, description="ISO timestamp to filter to")
):
    """Get logs for a specific session with filtering and formatting options"""
    base_log_dir = Path(settings.logging.session_logs_dir)
    session_dir = base_log_dir / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if format == "json":
        # Return structured JSON events
        events_file = session_dir / "events.jsonl"
        events = parse_jsonl_logs(events_file)

        # Apply filters
        if level:
            events = [e for e in events if e.get("level") == level.upper()]

        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]

        if agent_id:
            events = [e for e in events if e.get("agent_id") == agent_id]

        # Time filtering
        if from_timestamp:
            try:
                from_dt = datetime.fromisoformat(from_timestamp.replace('Z', '+00:00'))
                events = [e for e in events if datetime.fromisoformat(e.get("timestamp", "").replace('Z', '+00:00')) >= from_dt]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_timestamp format")

        if to_timestamp:
            try:
                to_dt = datetime.fromisoformat(to_timestamp.replace('Z', '+00:00'))
                events = [e for e in events if datetime.fromisoformat(e.get("timestamp", "").replace('Z', '+00:00')) <= to_dt]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_timestamp format")

        # Apply limit
        if limit:
            events = events[-limit:]  # Get most recent entries

        return {
            "session_id": session_id,
            "format": "json",
            "total_events": len(events),
            "events": events
        }

    elif format == "human":
        # Return human-readable logs
        session_file = session_dir / "session.log"
        lines = parse_human_readable_logs(session_file)

        # Apply limit
        if limit:
            lines = lines[-limit:]

        return {
            "session_id": session_id,
            "format": "human",
            "total_lines": len(lines),
            "lines": lines
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'human'")


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get session analytics and summary"""
    try:
        summary = session_logger.get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate session summary: {e}")


@router.get("/sessions/{session_id}/performance")
async def get_session_performance(session_id: str):
    """Get performance metrics for a session"""
    base_log_dir = Path(settings.logging.session_logs_dir)
    session_dir = base_log_dir / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    events_file = session_dir / "events.jsonl"
    events = parse_jsonl_logs(events_file)

    # Calculate performance metrics
    tool_calls = [e for e in events if e.get("event_type") == "tool_called" and e.get("duration_ms")]
    mcp_calls = [e for e in events if e.get("event_type") == "mcp_called" and e.get("duration_ms")]
    errors = [e for e in events if e.get("level") == "ERROR"]

    # Duration statistics
    tool_durations = [e["duration_ms"] for e in tool_calls]
    mcp_durations = [e["duration_ms"] for e in mcp_calls]

    def calc_stats(durations):
        if not durations:
            return {"min": 0, "max": 0, "avg": 0, "total": 0}
        return {
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "total": sum(durations)
        }

    # Agent activity
    agent_activity = {}
    for event in events:
        if event.get("agent_id"):
            agent_id = event["agent_id"]
            if agent_id not in agent_activity:
                agent_activity[agent_id] = {
                    "total_events": 0,
                    "tool_calls": 0,
                    "errors": 0,
                    "total_duration": 0
                }

            agent_activity[agent_id]["total_events"] += 1

            if event.get("event_type") == "tool_called":
                agent_activity[agent_id]["tool_calls"] += 1
                if event.get("duration_ms"):
                    agent_activity[agent_id]["total_duration"] += event["duration_ms"]

            if event.get("level") == "ERROR":
                agent_activity[agent_id]["errors"] += 1

    # Time series data (events per minute)
    if events:
        time_series = {}
        for event in events:
            timestamp = event.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    minute_key = dt.strftime("%Y-%m-%d %H:%M")
                    time_series[minute_key] = time_series.get(minute_key, 0) + 1
                except ValueError:
                    continue
    else:
        time_series = {}

    return {
        "session_id": session_id,
        "overview": {
            "total_events": len(events),
            "tool_calls": len(tool_calls),
            "mcp_calls": len(mcp_calls),
            "errors": len(errors),
            "success_rate": ((len(events) - len(errors)) / len(events) * 100) if events else 100
        },
        "performance": {
            "tool_calls": calc_stats(tool_durations),
            "mcp_calls": calc_stats(mcp_durations)
        },
        "agent_activity": agent_activity,
        "time_series": time_series
    }


@router.get("/application")
async def get_application_logs(
    limit: Optional[int] = Query(100, description="Limit number of lines returned"),
    level: Optional[str] = Query(None, description="Filter by log level")
):
    """Get application-wide logs"""
    base_log_dir = Path(settings.logging.session_logs_dir)
    app_log_file = base_log_dir / "application.log"

    if not app_log_file.exists():
        return {"lines": [], "total_lines": 0}

    lines = parse_human_readable_logs(app_log_file)

    # Apply level filter if specified
    if level:
        lines = [line for line in lines if level.upper() in line]

    # Apply limit
    if limit:
        lines = lines[-limit:]

    return {
        "total_lines": len(lines),
        "lines": lines
    }


@router.get("/startup")
async def get_startup_logs():
    """Get server startup logs"""
    base_log_dir = Path(settings.logging.session_logs_dir)
    startup_dir = base_log_dir / "startup"

    if not startup_dir.exists():
        return {"events": [], "lines": []}

    events_file = startup_dir / "events.jsonl"
    session_file = startup_dir / "session.log"

    events = parse_jsonl_logs(events_file)
    lines = parse_human_readable_logs(session_file)

    return {
        "events": events,
        "lines": lines
    }


@router.delete("/sessions/{session_id}")
async def delete_session_logs(session_id: str):
    """Delete logs for a specific session"""
    base_log_dir = Path(settings.logging.session_logs_dir)
    session_dir = base_log_dir / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        import shutil
        shutil.rmtree(session_dir)
        return {"message": f"Session {session_id} logs deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session logs: {e}")


@router.get("/export/{session_id}")
async def export_session_logs(session_id: str, format: str = Query("json")):
    """Export session logs in various formats"""
    from fastapi.responses import FileResponse
    import tempfile
    import zipfile

    base_log_dir = Path(settings.logging.session_logs_dir)
    session_dir = base_log_dir / session_id

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if format == "zip":
        # Create a zip file with all session logs
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                for log_file in session_dir.glob("*"):
                    if log_file.is_file():
                        zip_file.write(log_file, log_file.name)

            return FileResponse(
                tmp_file.name,
                media_type="application/zip",
                filename=f"session_{session_id}_logs.zip"
            )

    else:
        # Return JSON export
        events_file = session_dir / "events.jsonl"
        events = parse_jsonl_logs(events_file)

        lines_file = session_dir / "session.log"
        lines = parse_human_readable_logs(lines_file)

        export_data = {
            "session_id": session_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "structured_events": events,
            "human_readable_logs": lines
        }

        return export_data