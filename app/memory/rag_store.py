# =========================================
# File: app/memory/rag_store.py
# Purpose: Minimal persistent snippet store + naive search (keyword)
# =========================================
from __future__ import annotations
import sqlite3, os
from typing import List, Dict, Any

DEFAULT_DB_PATH = os.environ.get("AGENTIC_DB_PATH", os.path.join("data", "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS rag_chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id TEXT,
  agent_key TEXT,
  text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rag_group ON rag_chunks(group_id);
CREATE INDEX IF NOT EXISTS idx_rag_agent ON rag_chunks(agent_key);
"""

_rag_cxn = sqlite3.connect(DEFAULT_DB_PATH, check_same_thread=False)
_rag_cxn.execute("PRAGMA foreign_keys=ON")
_rag_cxn.executescript(SCHEMA)
_rag_cxn.commit()


def add_chunk(text: str, group_id: str | None = None, agent_key: str | None = None) -> int:
    cur = _rag_cxn.execute(
        "INSERT INTO rag_chunks (group_id, agent_key, text) VALUES (?,?,?)",
        (group_id, agent_key, text),
    )
    _rag_cxn.commit()
    return cur.lastrowid


def search(query: str, group_id: str | None = None, agent_key: str | None = None, limit: int = 10) -> List[Dict[str, Any]]:
    base = "SELECT id, text FROM rag_chunks WHERE text LIKE ?"
    params = [f"%{query}%"]
    if group_id:
        base += " AND group_id=?"
        params.append(group_id)
    if agent_key:
        base += " AND agent_key=?"
        params.append(agent_key)
    base += " LIMIT ?"
    params.append(limit)
    cur = _rag_cxn.execute(base, params)
    return [{"id": r[0], "text": r[1]} for r in cur.fetchall()]