# =========================================
# File: app/telemetry/events.py
# Purpose: Structured, transparent event bus for UI activity feed
# =========================================
from __future__ import annotations
import asyncio
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Callable, Coroutine, Optional
import time


@dataclass
class TelemetryEvent:
    ts: float
    group_id: str
    kind: str  # 'message' | 'tool_call' | 'tool_result' | 'mcp_call' | 'agent_call' | 'agent_thought' | 'error' | 'rag_retrieval' | 'summarization' | 'document_processing' | 'group_operation' | 'settings_change' | 'agent_management'
    agent_key: Optional[str]
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventBus:
    """In‑process async pub/sub for telemetry. Thread-safe via queue."""

    def __init__(self) -> None:
        self._queue: "asyncio.Queue[TelemetryEvent]" = asyncio.Queue()
        self._subscribers: List[Callable[[TelemetryEvent], Coroutine[Any, Any, None]]] = []

    async def publish(self, evt: TelemetryEvent) -> None:
        # 1. Persist to database for historical queries (Comprehensive Log Panel)
        try:
            from src.core.memory import session_store
            session_store.append_telemetry_event(
                timestamp=evt.ts,
                group_id=evt.group_id,
                event_type=evt.kind,
                agent_key=evt.agent_key,
                payload=evt.payload
            )
        except Exception as e:
            print(f"Warning: Failed to persist telemetry event: {e}")

        # 2. Add to queue for polling consumers
        await self._queue.put(evt)

        # 3. Fire-and-forget to all SSE subscribers (real-time UI updates)
        for sub in list(self._subscribers):
            asyncio.create_task(sub(evt))

    def subscribe(self, handler: Callable[[TelemetryEvent], Coroutine[Any, Any, None]]) -> None:
        self._subscribers.append(handler)

    async def drain(self, limit: int = 200) -> List[TelemetryEvent]:
        """Non-blocking drain of the queue for consumers that poll periodically."""
        out: List[TelemetryEvent] = []
        try:
            while len(out) < limit:
                evt = self._queue.get_nowait()
                out.append(evt)
        except asyncio.QueueEmpty:
            pass
        return out


# Global singleton used across the app
EVENT_BUS = EventBus()


# Convenience factories ------------------------------------------------------

def now_ts() -> float:
    return time.time()

async def emit_message(
    group_id: str,
    sender: str,
    role: str,
    content: str,
    agent_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="message",
        agent_key=agent_key,
        payload={
            "sender": sender,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
    ))

async def emit_tool_call(group_id: str, agent_key: str, tool_name: str, status: str, meta: Optional[Dict[str, Any]] = None) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="tool_call",
        agent_key=agent_key,
        payload={"tool": tool_name, "status": status, **(meta or {})}
    ))

async def emit_tool_result(group_id: str, agent_key: str, tool_name: str, excerpt: str, meta: Optional[Dict[str, Any]] = None) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="tool_result",
        agent_key=agent_key,
        payload={"tool": tool_name, "excerpt": excerpt, **(meta or {})}
    ))

async def emit_mcp_call(group_id: str, agent_key: str, server: str, tool_name: str, status: str, meta: Optional[Dict[str, Any]] = None) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="mcp_call",
        agent_key=agent_key,
        payload={"server": server, "tool": tool_name, "status": status, **(meta or {})}
    ))

async def emit_agent_call(group_id: str, caller: str, callee: str, status: str, meta: Optional[Dict[str, Any]] = None) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="agent_call",
        agent_key=caller,
        payload={"caller": caller, "callee": callee, "status": status, **(meta or {})}
    ))

async def emit_error(group_id: str, where: str, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="error",
        agent_key=None,
        payload={"where": where, "message": message, **(meta or {})}
    ))

async def emit_agent_thought(
    group_id: str,
    agent_key: str,
    thought: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="agent_thought",
        agent_key=agent_key,
        payload={
            "thought": thought,
            **(meta or {})
        }
    ))

async def emit_rag_retrieval(
    group_id: str,
    agent_key: str,
    query: str,
    chunks_found: int,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit RAG context retrieval event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="rag_retrieval",
        agent_key=agent_key,
        payload={
            "query": query[:100],  # Truncate query for logs
            "chunks_found": chunks_found,
            **(meta or {})
        }
    ))

async def emit_summarization(
    group_id: str,
    status: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit conversation summarization event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="summarization",
        agent_key=None,
        payload={
            "status": status,  # "start", "complete", "error"
            **(meta or {})
        }
    ))

async def emit_document_processing(
    group_id: str,
    agent_key: str,
    filename: str,
    status: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit document processing pipeline event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="document_processing",
        agent_key=agent_key,
        payload={
            "filename": filename,
            "status": status,  # "start", "extracting", "chunking", "embedding", "storing", "complete", "error"
            **(meta or {})
        }
    ))

async def emit_group_operation(
    group_id: str,
    operation: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit group management operation event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id=group_id,
        kind="group_operation",
        agent_key=None,
        payload={
            "operation": operation,  # "created", "deleted", "agent_added", "agent_removed", "renamed"
            **(meta or {})
        }
    ))

async def emit_settings_change(
    setting_key: str,
    operation: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit settings change event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id="system",
        kind="settings_change",
        agent_key=None,
        payload={
            "setting_key": setting_key,
            "operation": operation,  # "updated", "deleted", "validated", "backup"
            **(meta or {})
        }
    ))

async def emit_agent_management(
    agent_key: str,
    operation: str,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """Emit agent management operation event"""
    await EVENT_BUS.publish(TelemetryEvent(
        ts=now_ts(),
        group_id="system",
        kind="agent_management",
        agent_key=agent_key,
        payload={
            "operation": operation,  # "created", "updated", "deleted", "registered"
            **(meta or {})
        }
    ))
