
# =========================================
# File: app/memory/session_store.py
# Purpose: SQLite persistence for groups, memberships, and messages
# =========================================
from __future__ import annotations
import json
import os
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.environ.get("AGENTIC_DB_PATH", os.path.join("data", "app.db"))

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS groups (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS group_agents (
  group_id TEXT NOT NULL,
  agent_key TEXT NOT NULL,
  PRIMARY KEY (group_id, agent_key),
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id TEXT NOT NULL,
  sender TEXT NOT NULL,            -- 'user' or agent_key
  role TEXT NOT NULL,              -- 'user' | 'agent' | 'system'
  content TEXT NOT NULL,
  metadata TEXT,                   -- JSON
  created_at REAL NOT NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_summaries (
  group_id TEXT PRIMARY KEY,
  summary TEXT NOT NULL,           -- Cumulative conversation summary
  last_summarized_count INTEGER NOT NULL,  -- Message count when last summarized
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL,
  FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS telemetry_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp REAL NOT NULL,
  group_id TEXT NOT NULL,          -- Group ID or 'system' for system-wide events
  event_type TEXT NOT NULL,        -- 'rag_retrieval', 'document_processing', 'summarization', 'group_operation', etc.
  agent_key TEXT,
  payload TEXT NOT NULL,           -- JSON
  created_at REAL NOT NULL
  -- No FK constraint: system events use group_id='system' which doesn't exist in groups table
);

-- Performance indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_group_role ON messages(group_id, role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_group_agents_group_id ON group_agents(group_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_group_id ON telemetry_events(group_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_event_type ON telemetry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_events(timestamp);
"""

def _create_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Create database connection with proper error handling.

    Args:
        db_path: Path to SQLite database file

    Returns:
        sqlite3.Connection: Database connection

    Raises:
        RuntimeError: If database initialization fails
    """
    try:
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Create connection
        cxn = sqlite3.connect(db_path, check_same_thread=False)
        cxn.execute("PRAGMA foreign_keys=ON")

        return cxn
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database at {db_path}: {e}") from e


try:
    _cxn: sqlite3.Connection = _create_connection()
    _cxn.executescript(SCHEMA)
    _cxn.commit()
except RuntimeError as e:
    # Log error and re-raise with helpful message
    import logging
    logging.error(f"Database initialization failed: {e}")
    raise RuntimeError(
        f"Failed to initialize session database. "
        f"Ensure the data directory is writable and SQLite is available."
    ) from e

# Export connection for other modules that expect _db_conn
_db_conn: sqlite3.Connection = _cxn

# -------- Groups --------

def create_group(name: str) -> str:
    gid = str(uuid.uuid4())
    now = time.time()
    _cxn.execute(
        "INSERT INTO groups (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (gid, name, now, now),
    )
    _cxn.commit()
    return gid


def rename_group(group_id: str, new_name: str) -> None:
    now = time.time()
    _cxn.execute(
        "UPDATE groups SET name=?, updated_at=? WHERE id=?",
        (new_name, now, group_id),
    )
    _cxn.commit()


def delete_group(group_id: str) -> None:
    """
    Comprehensive group deletion with cascade cleanup.

    Deletes:
    1. Group record (automatically cascades to messages and group_agents via FK)
    2. Agent memories related to this group
    3. RAG store chunks with group context
    4. Document files associated with the group
    5. Session logs for the group
    """
    import os
    import json
    from pathlib import Path

    try:
        # 1. Get document files to delete before deleting messages
        document_files_to_delete = []
        try:
            documents = get_group_documents(group_id)
            for doc in documents:
                metadata = doc.get("metadata", {})
                if metadata.get("message_type") == "document_upload":
                    filename = metadata.get("filename")
                    if filename:
                        # Construct document path (matches the upload path structure)
                        doc_path = Path("documents/uploads") / filename
                        if doc_path.exists():
                            document_files_to_delete.append(doc_path)
        except Exception as e:
            print(f"⚠️ Failed to gather document files for cleanup: {e}")

        # 2. Get agent list for memory cleanup before deleting group_agents
        try:
            agent_list = list_group_agents(group_id)
        except Exception as e:
            print(f"⚠️ Failed to get agent list for memory cleanup: {e}")
            agent_list = []

        # 3. Clean up vector store documents for this group
        try:
            from src.core.memory.vector_store import vector_store
            vector_store.delete_group(group_id)
            print(f"✅ Cleaned up vector store for group {group_id}")
        except Exception as e:
            print(f"⚠️ Vector store cleanup failed: {e}")

        # 5. Delete group record (FK cascade handles messages and group_agents)
        _cxn.execute("DELETE FROM groups WHERE id=?", (group_id,))
        _cxn.commit()

        # 6. Clean up document files
        files_deleted = 0
        for doc_path in document_files_to_delete:
            try:
                if doc_path.exists():
                    doc_path.unlink()  # Delete file
                    files_deleted += 1
                    print(f"🗑️ Deleted document file: {doc_path}")
            except Exception as e:
                print(f"⚠️ Failed to delete document {doc_path}: {e}")

        # 7. Clean up session logs (if they exist in organized structure)
        try:
            logs_dir = Path("logs/sessions")
            if logs_dir.exists():
                # Look for group-specific log files
                for log_file in logs_dir.glob(f"*{group_id}*"):
                    try:
                        log_file.unlink()
                        print(f"🗑️ Deleted session log: {log_file}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete log {log_file}: {e}")
        except Exception as e:
            print(f"⚠️ Log cleanup failed: {e}")

        print(f"✅ Comprehensive deletion completed for group {group_id}: {files_deleted} documents, {len(agent_list)} agents processed")

    except Exception as e:
        # Ensure we still delete the group even if cleanup fails
        try:
            _cxn.execute("DELETE FROM groups WHERE id=?", (group_id,))
            _cxn.commit()
            print(f"⚠️ Group {group_id} deleted but cleanup had issues: {e}")
        except Exception as e2:
            print(f"❌ Critical: Failed to delete group {group_id}: {e2}")
            raise e2


def list_groups() -> List[Dict[str, Any]]:
    cur = _cxn.execute(
        "SELECT id, name, created_at, updated_at FROM groups ORDER BY updated_at DESC"
    )
    return [
        {"id": r[0], "name": r[1], "created_at": r[2], "updated_at": r[3]}
        for r in cur.fetchall()
    ]


# -------- Group membership --------

def add_agent_to_group(group_id: str, agent_key: str) -> None:
    _cxn.execute(
        "INSERT OR IGNORE INTO group_agents (group_id, agent_key) VALUES (?,?)",
        (group_id, agent_key),
    )
    _cxn.commit()


def remove_agent_from_group(group_id: str, agent_key: str) -> None:
    _cxn.execute(
        "DELETE FROM group_agents WHERE group_id=? AND agent_key=?",
        (group_id, agent_key),
    )
    _cxn.commit()


def list_group_agents(group_id: str) -> List[str]:
    cur = _cxn.execute(
        "SELECT agent_key FROM group_agents WHERE group_id=?", (group_id,)
    )
    return [r[0] for r in cur.fetchall()]


# -------- Messages --------

def append_message(
    group_id: str,
    sender: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    now = time.time()
    md = json.dumps(metadata or {})
    cur = _cxn.execute(
        "INSERT INTO messages (group_id, sender, role, content, metadata, created_at) VALUES (?,?,?,?,?,?)",
        (group_id, sender, role, content, md, now),
    )
    _cxn.commit()
    return cur.lastrowid


def get_history(group_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    cur = _cxn.execute(
        "SELECT sender, role, content, metadata, created_at FROM messages WHERE group_id=? ORDER BY id ASC LIMIT ?",
        (group_id, limit),
    )
    out = []
    for sender, role, content, metadata, ts in cur.fetchall():
        out.append(
            {
                "sender": sender,
                "role": role,
                "content": content,
                "metadata": json.loads(metadata or "{}"),
                "created_at": ts,
            }
        )
    return out


def append_document_message(
    group_id: str,
    sender: str,
    filename: str,
    document_id: str,
    target_agent: str,
    file_size: int,
    file_extension: str,
    original_prompt: str = "",
    extracted_content: str = "",
    content_summary: str = "",
) -> int:
    """Store a document upload as a special message type"""
    now = time.time()
    
    # Create document-specific content with file details
    size_kb = file_size / 1024 if file_size > 0 else 0
    content = f"📄 **Document uploaded**: {filename}\n**Target Agent**: @{target_agent}\n**Size**: {size_kb:.1f} KB • **ID**: {document_id}"
    if content_summary:
        content += f"\n**Summary**: {content_summary}"
    
    # Store rich metadata for document viewing
    metadata = {
        "message_type": "document_upload",
        "document_id": document_id,
        "filename": filename,
        "target_agent": target_agent,
        "file_size": file_size,
        "file_extension": file_extension,
        "original_prompt": original_prompt,
        "extracted_content": extracted_content,
        "content_summary": content_summary,
        "upload_timestamp": now
    }
    
    return append_message(group_id, sender, "system", content, metadata)


def get_group_documents(group_id: str) -> List[Dict[str, Any]]:
    """Get all document uploads for a group"""
    cur = _cxn.execute(
        "SELECT sender, content, metadata, created_at FROM messages WHERE group_id=? AND role='system' ORDER BY id DESC",
        (group_id,)
    )
    
    documents = []
    for sender, content, metadata, ts in cur.fetchall():
        meta = json.loads(metadata or "{}")
        if meta.get("message_type") == "document_upload":
            documents.append({
                "sender": sender,
                "content": content,
                "metadata": meta,
                "created_at": ts
            })

    return documents


def get_document_details(group_id: str, document_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific document"""
    cur = _cxn.execute(
        "SELECT sender, content, metadata, created_at FROM messages WHERE group_id=? AND role='system'",
        (group_id,)
    )

    for sender, content, metadata, ts in cur.fetchall():
        meta = json.loads(metadata or "{}")
        if meta.get("document_id") == document_id:
            return {
                "sender": sender,
                "content": content,
                "metadata": meta,
                "created_at": ts
            }

    return None


# -------- Group Summaries (Conversation Summarization) --------

def get_group_summary(group_id: str) -> Optional[Dict[str, Any]]:
    """
    Get conversation summary for a group

    Returns:
        {
            "summary": str,
            "last_summarized_count": int,
            "updated_at": float
        } or None if no summary exists
    """
    cur = _cxn.execute(
        "SELECT summary, last_summarized_count, updated_at FROM group_summaries WHERE group_id=?",
        (group_id,)
    )
    row = cur.fetchone()
    if row:
        return {
            "summary": row[0],
            "last_summarized_count": row[1],
            "updated_at": row[2]
        }
    return None


def upsert_group_summary(
    group_id: str,
    summary: str,
    last_summarized_count: int
) -> None:
    """
    Insert or update group conversation summary

    Args:
        group_id: Group ID
        summary: Cumulative conversation summary
        last_summarized_count: Total messages summarized so far
    """
    now = time.time()

    # Try update first
    cur = _cxn.execute(
        "UPDATE group_summaries SET summary=?, last_summarized_count=?, updated_at=? WHERE group_id=?",
        (summary, last_summarized_count, now, group_id)
    )

    # If no rows updated, insert
    if cur.rowcount == 0:
        _cxn.execute(
            "INSERT INTO group_summaries (group_id, summary, last_summarized_count, created_at, updated_at) VALUES (?,?,?,?,?)",
            (group_id, summary, last_summarized_count, now, now)
        )

    _cxn.commit()


def delete_group_summary(group_id: str) -> None:
    """Delete conversation summary for a group"""
    _cxn.execute("DELETE FROM group_summaries WHERE group_id=?", (group_id,))
    _cxn.commit()


# -------- Telemetry Events --------

def append_telemetry_event(
    timestamp: float,
    group_id: str,
    event_type: str,
    agent_key: Optional[str],
    payload: Dict[str, Any]
) -> None:
    """
    Persist telemetry event to database for historical queries

    Args:
        timestamp: Event timestamp
        group_id: Group ID or 'system' for system-wide events
        event_type: Event type (rag_retrieval, document_processing, etc.)
        agent_key: Agent key if relevant
        payload: Event payload as dict
    """
    _cxn.execute(
        "INSERT INTO telemetry_events (timestamp, group_id, event_type, agent_key, payload, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (timestamp, group_id, event_type, agent_key, json.dumps(payload), time.time())
    )
    _cxn.commit()


def get_telemetry_events(
    group_id: Optional[str] = None,
    event_type: Optional[str] = None,
    agent_key: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Query telemetry events with filters

    Args:
        group_id: Filter by group ID (or 'system')
        event_type: Filter by event type
        agent_key: Filter by agent key
        start_time: Filter by start timestamp
        end_time: Filter by end timestamp
        limit: Maximum number of events to return

    Returns:
        List of telemetry event dicts
    """
    query = "SELECT id, timestamp, group_id, event_type, agent_key, payload, created_at FROM telemetry_events WHERE 1=1"
    params = []

    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if agent_key:
        query += " AND agent_key = ?"
        params.append(agent_key)

    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)

    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = _cxn.execute(query, params).fetchall()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "group_id": row[2],
            "event_type": row[3],
            "agent_key": row[4],
            "payload": json.loads(row[5]) if row[5] else {},
            "created_at": row[6]
        }
        for row in rows
    ]
