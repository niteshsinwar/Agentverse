
# =========================================
# File: app/memory/session_store.py
# Purpose: SQLite persistence for groups, memberships, and messages
# =========================================
from __future__ import annotations
import sqlite3, json, uuid, os, time
from typing import List, Dict, Any, Optional

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
"""

def _cxn(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    cxn = sqlite3.connect(db_path, check_same_thread=False)
    cxn.execute("PRAGMA foreign_keys=ON")
    return cxn

_cxn = _cxn()
_cxn.executescript(SCHEMA)
_cxn.commit()

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
    _cxn.execute("DELETE FROM groups WHERE id=?", (group_id,))
    _cxn.commit()


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
