"""
Advanced Agent Long-Term Memory System using RAG Store
Provides persistent, searchable memory for each agent across sessions
"""
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3

from app.memory.rag_store import add_chunk, search, _rag_cxn


@dataclass
class MemoryEntry:
    """Structured memory entry for agents"""
    entry_type: str  # fact, experience, preference, collaboration, insight
    content: str
    context: Dict[str, Any]  # Additional context (group_id, document_id, etc.)
    importance: float  # 0.0 to 1.0 importance score
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_searchable_text(self) -> str:
        """Convert to text for RAG storage"""
        tags_str = " ".join(self.tags) if self.tags else ""
        return f"[{self.entry_type}] {self.content} | Context: {json.dumps(self.context)} | Tags: {tags_str}"

    @classmethod
    def from_rag_text(cls, rag_text: str) -> 'MemoryEntry':
        """Parse memory entry from RAG text"""
        try:
            # Extract type
            if rag_text.startswith('[') and ']' in rag_text:
                end_bracket = rag_text.find(']')
                entry_type = rag_text[1:end_bracket]
                rest = rag_text[end_bracket + 2:]  # Skip '] '
            else:
                entry_type = "unknown"
                rest = rag_text

            # Split by separators
            parts = rest.split(' | Context: ', 1)
            content = parts[0]
            
            if len(parts) > 1:
                context_and_tags = parts[1].split(' | Tags: ', 1)
                try:
                    context = json.loads(context_and_tags[0])
                except:
                    context = {}
                
                tags = context_and_tags[1].split() if len(context_and_tags) > 1 else []
            else:
                context = {}
                tags = []

            return cls(
                entry_type=entry_type,
                content=content,
                context=context,
                importance=0.5,  # Default importance
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=tags
            )
        except Exception:
            # Fallback for malformed entries
            return cls(
                entry_type="unknown",
                content=rag_text,
                context={},
                importance=0.3,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )


class AgentMemoryManager:
    """Advanced memory management for individual agents using RAG store"""
    
    def __init__(self):
        self.memory_cache: Dict[str, List[MemoryEntry]] = {}  # agent_id -> recent memories
        self.cache_size = 50  # Keep 50 most recent memories in cache per agent
        
        # Create additional tables for memory metadata
        self._ensure_memory_tables()
    
    def _ensure_memory_tables(self):
        """Create additional tables for memory metadata"""
        memory_schema = """
        CREATE TABLE IF NOT EXISTS agent_memory_metadata (
            agent_id TEXT,
            entry_hash TEXT,
            importance REAL,
            created_at TIMESTAMP,
            last_accessed TIMESTAMP,
            access_count INTEGER DEFAULT 0,
            tags TEXT,  -- JSON array of tags
            PRIMARY KEY (agent_id, entry_hash)
        );
        
        CREATE INDEX IF NOT EXISTS idx_memory_agent ON agent_memory_metadata(agent_id);
        CREATE INDEX IF NOT EXISTS idx_memory_importance ON agent_memory_metadata(importance);
        CREATE INDEX IF NOT EXISTS idx_memory_accessed ON agent_memory_metadata(last_accessed);
        """
        
        _rag_cxn.executescript(memory_schema)
        _rag_cxn.commit()
    
    def _get_entry_hash(self, entry: MemoryEntry) -> str:
        """Generate hash for memory entry deduplication"""
        content_str = f"{entry.entry_type}:{entry.content}:{json.dumps(entry.context, sort_keys=True)}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def store_memory(self, agent_id: str, entry: MemoryEntry) -> bool:
        """Store a memory entry for an agent"""
        try:
            entry_hash = self._get_entry_hash(entry)
            
            # Check if already exists
            existing = _rag_cxn.execute(
                "SELECT 1 FROM agent_memory_metadata WHERE agent_id = ? AND entry_hash = ?",
                (agent_id, entry_hash)
            ).fetchone()
            
            if existing:
                # Update access info
                self._update_memory_access(agent_id, entry_hash)
                return False
            
            # Store in RAG store
            rag_id = add_chunk(
                text=entry.to_searchable_text(),
                group_id=None,  # Agent memory is not group-specific
                agent_key=agent_id
            )
            
            # Store metadata
            _rag_cxn.execute(
                """INSERT INTO agent_memory_metadata 
                   (agent_id, entry_hash, importance, created_at, last_accessed, access_count, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    agent_id, entry_hash, entry.importance,
                    entry.created_at, entry.last_accessed, entry.access_count,
                    json.dumps(entry.tags)
                )
            )
            _rag_cxn.commit()
            
            # Update cache
            self._update_cache(agent_id, entry)
            
            print(f"💾 Stored memory for {agent_id}: {entry.entry_type} - {entry.content[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Failed to store memory for {agent_id}: {e}")
            return False
    
    def search_memories(self, agent_id: str, query: str, 
                       entry_types: List[str] = None, 
                       limit: int = 10,
                       min_importance: float = 0.0) -> List[MemoryEntry]:
        """Search agent's memories with optional filtering"""
        
        # Search RAG store
        rag_results = search(query=query, agent_key=agent_id, limit=limit * 2)
        
        memories = []
        for result in rag_results:
            try:
                # Parse memory entry
                entry = MemoryEntry.from_rag_text(result["text"])
                
                # Apply filters
                if entry_types and entry.entry_type not in entry_types:
                    continue
                    
                if entry.importance < min_importance:
                    continue
                
                # Update access tracking
                entry_hash = self._get_entry_hash(entry)
                self._update_memory_access(agent_id, entry_hash)
                
                memories.append(entry)
                
            except Exception as e:
                print(f"⚠️ Failed to parse memory entry: {e}")
                continue
        
        # Sort by relevance + importance + recency
        memories.sort(key=lambda x: (x.importance, -x.access_count, x.last_accessed), reverse=True)
        
        return memories[:limit]
    
    def get_recent_memories(self, agent_id: str, limit: int = 20,
                           hours_back: int = 24) -> List[MemoryEntry]:
        """Get recent memories for an agent"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Query from metadata table for recent entries
        cur = _rag_cxn.execute(
            """SELECT entry_hash FROM agent_memory_metadata 
               WHERE agent_id = ? AND created_at > ? 
               ORDER BY created_at DESC LIMIT ?""",
            (agent_id, cutoff_time, limit)
        )
        
        entry_hashes = [row[0] for row in cur.fetchall()]
        
        memories = []
        for entry_hash in entry_hashes:
            # Get from RAG store
            rag_results = search(query="", agent_key=agent_id, limit=100)
            for result in rag_results:
                entry = MemoryEntry.from_rag_text(result["text"])
                if self._get_entry_hash(entry) == entry_hash:
                    memories.append(entry)
                    break
        
        return memories
    
    def get_memory_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get summary of agent's memory"""
        
        # Get memory statistics
        cur = _rag_cxn.execute(
            "SELECT COUNT(*), AVG(importance), MAX(last_accessed) FROM agent_memory_metadata WHERE agent_id = ?",
            (agent_id,)
        )
        
        stats = cur.fetchone()
        total_memories = stats[0] or 0
        avg_importance = stats[1] or 0.0
        last_access = stats[2] or "Never"
        
        # Get memory type distribution
        cur = _rag_cxn.execute(
            """SELECT entry_hash FROM agent_memory_metadata WHERE agent_id = ? ORDER BY importance DESC LIMIT 50""",
            (agent_id,)
        )
        
        type_counts = {}
        for (entry_hash,) in cur.fetchall():
            # This is simplified - in production you'd want better type extraction
            rag_results = search(query="", agent_key=agent_id, limit=100)
            for result in rag_results:
                if self._get_entry_hash(MemoryEntry.from_rag_text(result["text"])) == entry_hash:
                    entry = MemoryEntry.from_rag_text(result["text"])
                    type_counts[entry.entry_type] = type_counts.get(entry.entry_type, 0) + 1
                    break
        
        return {
            "total_memories": total_memories,
            "average_importance": round(avg_importance, 2),
            "last_access": last_access,
            "memory_types": type_counts,
            "cache_size": len(self.memory_cache.get(agent_id, []))
        }
    
    def learn_from_interaction(self, agent_id: str, interaction_data: Dict[str, Any]):
        """Learn and store memories from agent interactions"""
        
        memories_to_store = []
        
        # Extract different types of learnings
        if "user_feedback" in interaction_data:
            memories_to_store.append(MemoryEntry(
                entry_type="feedback",
                content=f"User feedback: {interaction_data['user_feedback']}",
                context={"interaction_id": interaction_data.get("interaction_id")},
                importance=0.7,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["user", "feedback"]
            ))
        
        if "successful_collaboration" in interaction_data:
            collab = interaction_data["successful_collaboration"]
            memories_to_store.append(MemoryEntry(
                entry_type="collaboration",
                content=f"Successfully collaborated with {collab['agent']} on {collab['task']}",
                context={"collaborator": collab["agent"], "outcome": collab.get("outcome")},
                importance=0.6,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["collaboration", "success", collab["agent"]]
            ))
        
        if "document_insights" in interaction_data:
            for insight in interaction_data["document_insights"]:
                memories_to_store.append(MemoryEntry(
                    entry_type="insight",
                    content=f"Document insight: {insight}",
                    context={"document_id": interaction_data.get("document_id")},
                    importance=0.5,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=["document", "insight"]
                ))
        
        if "tool_usage" in interaction_data:
            tool_info = interaction_data["tool_usage"]
            memories_to_store.append(MemoryEntry(
                entry_type="experience",
                content=f"Used tool {tool_info['tool']} with result: {tool_info.get('outcome', 'completed')}",
                context={"tool": tool_info["tool"], "success": tool_info.get("success", True)},
                importance=0.4,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["tool", tool_info["tool"]]
            ))
        
        # Store all memories
        for memory in memories_to_store:
            self.store_memory(agent_id, memory)
    
    def _update_memory_access(self, agent_id: str, entry_hash: str):
        """Update memory access tracking"""
        try:
            _rag_cxn.execute(
                """UPDATE agent_memory_metadata 
                   SET last_accessed = ?, access_count = access_count + 1
                   WHERE agent_id = ? AND entry_hash = ?""",
                (datetime.now(), agent_id, entry_hash)
            )
            _rag_cxn.commit()
        except Exception as e:
            print(f"⚠️ Failed to update memory access: {e}")
    
    def _update_cache(self, agent_id: str, entry: MemoryEntry):
        """Update in-memory cache"""
        if agent_id not in self.memory_cache:
            self.memory_cache[agent_id] = []
        
        cache = self.memory_cache[agent_id]
        cache.insert(0, entry)  # Add to front
        
        # Keep cache size limited
        if len(cache) > self.cache_size:
            cache.pop()
    
    def get_contextual_memories(self, agent_id: str, current_context: Dict[str, Any], 
                               limit: int = 5) -> List[MemoryEntry]:
        """Get memories relevant to current context"""
        
        # Build search query from context
        search_terms = []
        
        if "group_id" in current_context:
            search_terms.append(current_context["group_id"])
        
        if "document_type" in current_context:
            search_terms.append(current_context["document_type"])
        
        if "other_agents" in current_context:
            search_terms.extend(current_context["other_agents"])
        
        if "topic_keywords" in current_context:
            search_terms.extend(current_context["topic_keywords"])
        
        if not search_terms:
            return self.get_recent_memories(agent_id, limit)
        
        query = " ".join(search_terms)
        return self.search_memories(agent_id, query, limit=limit)
    
    def cleanup_old_memories(self, agent_id: str, keep_days: int = 30, 
                            min_importance: float = 0.3):
        """Clean up old, low-importance memories"""
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        try:
            # Get old, low-importance memories
            cur = _rag_cxn.execute(
                """SELECT entry_hash FROM agent_memory_metadata 
                   WHERE agent_id = ? AND created_at < ? AND importance < ?""",
                (agent_id, cutoff_date, min_importance)
            )
            
            old_hashes = [row[0] for row in cur.fetchall()]
            
            # Remove from metadata
            for entry_hash in old_hashes:
                _rag_cxn.execute(
                    "DELETE FROM agent_memory_metadata WHERE agent_id = ? AND entry_hash = ?",
                    (agent_id, entry_hash)
                )
            
            # Note: RAG chunks cleanup would require mapping between hashes and RAG IDs
            # This is a simplified version
            
            _rag_cxn.commit()
            print(f"🧹 Cleaned up {len(old_hashes)} old memories for {agent_id}")
            
        except Exception as e:
            print(f"❌ Memory cleanup failed for {agent_id}: {e}")

    def store_experience(self, agent_id: str, prompt: str, response: str, group_id: str = None, 
                        tools_used: List[str] = None, success: bool = True, **kwargs):
        """Store interaction experience as memory - compatibility method for base_agent.py"""
        try:
            # Create experience memory entry
            entry = MemoryEntry(
                entry_type="experience",
                content=f"User: {prompt[:100]}{'...' if len(prompt) > 100 else ''} | Response: {response[:100]}{'...' if len(response) > 100 else ''}",
                context={
                    "group_id": group_id,
                    "tools_used": tools_used or [],
                    "success": success,
                    **kwargs
                },
                importance=0.6 if success else 0.4,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["interaction", "experience"] + (tools_used or [])
            )
            
            return self.store_memory(agent_id, entry)
            
        except Exception as e:
            print(f"❌ Failed to store experience for {agent_id}: {e}")
            return False


# Global instance
agent_memory = AgentMemoryManager()