"""
Enhanced Conversation History Manager
Optimizes context rebuilding and provides richer conversation history
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import sqlite3
from app.memory.session_store import _db_conn

@dataclass
class EnhancedMessage:
    """Rich message representation with metadata"""
    id: str
    group_id: str
    sender: str
    role: str  # user, agent, system, tool_call, tool_result
    content: str
    created_at: datetime
    metadata: Dict[str, Any]
    
    # Enhanced fields
    message_type: str  # conversation, delegation, collaboration, tool_usage, document_upload
    thread_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    agent_mentions: List[str] = None
    sentiment: str = "neutral"  # positive, negative, neutral
    importance_score: float = 0.5
    context_summary: str = ""
    
    def __post_init__(self):
        if self.agent_mentions is None:
            self.agent_mentions = []

@dataclass  
class ConversationContext:
    """Cached conversation context to reduce rebuilding"""
    group_id: str
    last_updated: datetime
    
    # Core context
    recent_messages: List[EnhancedMessage]
    active_threads: List[str]
    participating_agents: List[str]
    
    # Summary information
    conversation_summary: str
    key_topics: List[str]
    ongoing_tasks: List[Dict[str, Any]]
    
    # Performance optimization
    context_hash: str
    full_context_cache: Optional[str] = None


class ConversationManager:
    """Enhanced conversation history with context caching and optimization"""
    
    def __init__(self):
        self.context_cache: Dict[str, ConversationContext] = {}
        self.cache_ttl_minutes = 30  # Cache contexts for 30 minutes
        self.max_history_messages = 50  # Increased from 10 to 50
        self.context_summary_threshold = 20  # Summarize after 20 messages
        
        self._ensure_enhanced_tables()
    
    def _ensure_enhanced_tables(self):
        """Create enhanced tables for conversation management"""
        schema = '''
        CREATE TABLE IF NOT EXISTS enhanced_messages (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            metadata TEXT,  -- JSON
            message_type TEXT DEFAULT 'conversation',
            thread_id TEXT,
            parent_message_id TEXT,
            agent_mentions TEXT,  -- JSON array
            sentiment TEXT DEFAULT 'neutral',
            importance_score REAL DEFAULT 0.5,
            context_summary TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_enhanced_group ON enhanced_messages(group_id);
        CREATE INDEX IF NOT EXISTS idx_enhanced_created ON enhanced_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_enhanced_thread ON enhanced_messages(thread_id);
        CREATE INDEX IF NOT EXISTS idx_enhanced_importance ON enhanced_messages(importance_score);
        
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            group_id TEXT PRIMARY KEY,
            summary_text TEXT NOT NULL,
            key_topics TEXT,  -- JSON array
            last_updated TIMESTAMP,
            message_count INTEGER,
            participant_agents TEXT  -- JSON array
        );
        '''
        
        try:
            _db_conn.executescript(schema)
            _db_conn.commit()
        except Exception as e:
            print(f"❌ Failed to create enhanced conversation tables: {e}")
    
    def get_enhanced_conversation_context(self, group_id: str, 
                                        for_agent: str,
                                        force_rebuild: bool = False) -> str:
        """Get optimized conversation context with caching"""
        
        # Check cache first (unless force rebuild)
        if not force_rebuild and group_id in self.context_cache:
            cached_context = self.context_cache[group_id]
            
            # Check if cache is still valid
            age = datetime.now() - cached_context.last_updated
            if age.total_seconds() / 60 < self.cache_ttl_minutes:
                # Use cached context if available
                if cached_context.full_context_cache:
                    return cached_context.full_context_cache
        
        # Build fresh context
        context = self._build_conversation_context(group_id, for_agent)
        
        # Cache the result
        self.context_cache[group_id] = context
        
        return context.full_context_cache or self._format_context(context, for_agent)
    
    def _build_conversation_context(self, group_id: str, for_agent: str) -> ConversationContext:
        """Build comprehensive conversation context"""
        
        # Get enhanced messages from database
        recent_messages = self._get_enhanced_messages(group_id, limit=self.max_history_messages)
        
        # Analyze conversation
        participating_agents = list(set([msg.sender for msg in recent_messages if msg.role == "agent"]))
        active_threads = list(set([msg.thread_id for msg in recent_messages if msg.thread_id]))
        
        # Get or generate conversation summary
        conversation_summary, key_topics = self._get_or_generate_summary(group_id, recent_messages)
        
        # Extract ongoing tasks
        ongoing_tasks = self._extract_ongoing_tasks(recent_messages)
        
        # Create context
        context = ConversationContext(
            group_id=group_id,
            last_updated=datetime.now(),
            recent_messages=recent_messages,
            active_threads=active_threads,
            participating_agents=participating_agents,
            conversation_summary=conversation_summary,
            key_topics=key_topics,
            ongoing_tasks=ongoing_tasks,
            context_hash=self._generate_context_hash(recent_messages)
        )
        
        # Generate formatted context
        context.full_context_cache = self._format_context(context, for_agent)
        
        return context
    
    def _get_enhanced_messages(self, group_id: str, limit: int = 50) -> List[EnhancedMessage]:
        """Get enhanced messages from database with fallback to session store"""
        
        try:
            # Try to get from enhanced table first
            cursor = _db_conn.execute(
                '''SELECT id, group_id, sender, role, content, created_at, metadata,
                         message_type, thread_id, parent_message_id, agent_mentions,
                         sentiment, importance_score, context_summary
                   FROM enhanced_messages 
                   WHERE group_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?''',
                (group_id, limit)
            )
            
            enhanced_messages = []
            for row in cursor.fetchall():
                try:
                    metadata = json.loads(row[6]) if row[6] else {}
                    agent_mentions = json.loads(row[10]) if row[10] else []
                    
                    msg = EnhancedMessage(
                        id=row[0], group_id=row[1], sender=row[2], role=row[3],
                        content=row[4], created_at=datetime.fromisoformat(row[5]),
                        metadata=metadata, message_type=row[7], thread_id=row[8],
                        parent_message_id=row[9], agent_mentions=agent_mentions,
                        sentiment=row[11], importance_score=row[12], context_summary=row[13]
                    )
                    enhanced_messages.append(msg)
                except Exception as e:
                    print(f"⚠️ Failed to parse enhanced message: {e}")
                    continue
                    
            if enhanced_messages:
                return enhanced_messages[::-1]  # Reverse to chronological order
            
        except Exception as e:
            print(f"⚠️ Enhanced messages query failed, falling back to session store: {e}")
        
        # Fallback to session store
        from app.memory import session_store
        messages = session_store.get_history(group_id)
        
        enhanced_messages = []
        for i, msg in enumerate(messages[-limit:]):  # Get last N messages
            enhanced_msg = self._convert_to_enhanced_message(msg, i)
            enhanced_messages.append(enhanced_msg)
            
        return enhanced_messages
    
    def _convert_to_enhanced_message(self, msg: Dict[str, Any], index: int) -> EnhancedMessage:
        """Convert session store message to enhanced message"""
        
        import re
        
        content = msg.get("content", "")
        role = msg.get("role", "user")
        sender = msg.get("sender", "user")
        
        # Extract agent mentions
        agent_mentions = re.findall(r'@(\w+)', content)
        
        # Determine message type
        message_type = "conversation"
        if agent_mentions:
            message_type = "collaboration" if len(agent_mentions) > 1 else "delegation"
        elif role in ["tool_call", "tool_result"]:
            message_type = "tool_usage"
        elif "document" in content.lower() or "uploaded" in content.lower():
            message_type = "document_upload"
        
        # Calculate importance based on content
        importance_score = 0.5
        if agent_mentions:
            importance_score += 0.2
        if role == "user":
            importance_score += 0.1
        if len(content) > 100:
            importance_score += 0.1
            
        importance_score = min(importance_score, 1.0)
        
        return EnhancedMessage(
            id=f"msg_{index}_{hash(content) % 10000}",
            group_id=msg.get("group_id", ""),
            sender=sender,
            role=role,
            content=content,
            created_at=datetime.fromtimestamp(msg.get("created_at", datetime.now().timestamp())),
            metadata=msg.get("metadata", {}),
            message_type=message_type,
            agent_mentions=agent_mentions,
            importance_score=importance_score,
            context_summary=content[:100] + "..." if len(content) > 100 else content
        )
    
    def _get_or_generate_summary(self, group_id: str, 
                               messages: List[EnhancedMessage]) -> Tuple[str, List[str]]:
        """Get existing summary or generate new one"""
        
        try:
            # Check for existing summary
            cursor = _db_conn.execute(
                "SELECT summary_text, key_topics, message_count FROM conversation_summaries WHERE group_id = ?",
                (group_id,)
            )
            row = cursor.fetchone()
            
            if row and row[2] >= len(messages) - 5:  # If summary is recent
                topics = json.loads(row[1]) if row[1] else []
                return row[0], topics
                
        except Exception as e:
            print(f"⚠️ Failed to get existing summary: {e}")
        
        # Generate new summary
        if len(messages) < 3:
            return "Conversation just started", []
        
        # Extract key information
        user_messages = [m for m in messages if m.role == "user"]
        agent_responses = [m for m in messages if m.role == "agent"]
        
        # Simple summarization (can be enhanced with LLM)
        if user_messages and agent_responses:
            last_user_msg = user_messages[-1].content[:100]
            participating_agents = list(set([m.sender for m in agent_responses]))
            
            summary = f"Active conversation with {len(participating_agents)} agents. Recent topic: {last_user_msg}..."
            key_topics = []
            
            # Extract topics from important messages
            important_messages = [m for m in messages if m.importance_score > 0.6]
            for msg in important_messages[-5:]:  # Last 5 important messages
                words = msg.content.lower().split()[:10]  # First 10 words
                key_topics.extend([w for w in words if len(w) > 4 and w.isalpha()])
                
            key_topics = list(set(key_topics))[:10]  # Unique topics, max 10
        else:
            summary = "Initial conversation setup"
            key_topics = []
        
        # Store summary
        try:
            _db_conn.execute(
                '''INSERT OR REPLACE INTO conversation_summaries 
                   (group_id, summary_text, key_topics, last_updated, message_count, participant_agents)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (
                    group_id, summary, json.dumps(key_topics), datetime.now(),
                    len(messages), json.dumps(list(set([m.sender for m in messages])))
                )
            )
            _db_conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to store conversation summary: {e}")
        
        return summary, key_topics
    
    def _extract_ongoing_tasks(self, messages: List[EnhancedMessage]) -> List[Dict[str, Any]]:
        """Extract ongoing tasks from conversation"""
        
        tasks = []
        
        # Look for delegation messages
        delegation_messages = [m for m in messages if m.message_type == "delegation"]
        
        for msg in delegation_messages[-5:]:  # Last 5 delegations
            if msg.agent_mentions:
                for mentioned_agent in msg.agent_mentions:
                    task = {
                        "assigned_to": mentioned_agent,
                        "description": msg.content[:100],
                        "assigned_by": msg.sender,
                        "timestamp": msg.created_at.isoformat(),
                        "status": "pending"  # Could be enhanced to track completion
                    }
                    tasks.append(task)
        
        return tasks
    
    def _generate_context_hash(self, messages: List[EnhancedMessage]) -> str:
        """Generate hash for context caching"""
        content_hash = hash(tuple([
            (m.id, m.content[:50], m.created_at.timestamp()) 
            for m in messages[-10:]  # Last 10 messages
        ]))
        return str(abs(content_hash))
    
    def _format_context(self, context: ConversationContext, for_agent: str) -> str:
        """Format context for agent consumption"""
        
        lines = []
        
        # Conversation summary
        lines.append("📜 **CONVERSATION OVERVIEW**:")
        lines.append(f"📋 Summary: {context.conversation_summary}")
        
        if context.key_topics:
            lines.append(f"🏷️ Key Topics: {', '.join(context.key_topics[:5])}")
            
        if context.participating_agents:
            lines.append(f"👥 Participating Agents: {', '.join(['@' + a for a in context.participating_agents])}")
        
        lines.append("")
        
        # Ongoing tasks
        if context.ongoing_tasks:
            lines.append("📋 **ONGOING TASKS**:")
            for task in context.ongoing_tasks[-3:]:  # Show last 3 tasks
                lines.append(f"• @{task['assigned_to']}: {task['description']}")
            lines.append("")
        
        # Recent conversation history
        lines.append(f"💬 **RECENT CONVERSATION** (Last {len(context.recent_messages)} messages):")
        
        for msg in context.recent_messages:
            timestamp = msg.created_at.strftime("%H:%M")
            
            if msg.role == "user":
                lines.append(f"[{timestamp}] **User**: {msg.content}")
            elif msg.role == "agent":
                agent_key = msg.metadata.get("agent_key", msg.sender)
                lines.append(f"[{timestamp}] **@{agent_key}**: {msg.content}")
            elif msg.role == "system":
                lines.append(f"[{timestamp}] *System*: {msg.content}")
            elif msg.role in ["tool_call", "tool_result", "tool_error"]:
                lines.append(f"[{timestamp}] *{msg.role}*: {msg.content}")
        
        lines.append("\n🧠 **CONTEXT INTELLIGENCE**: This rich history helps you understand conversation flow and ongoing collaborations.")
        
        return "\n".join(lines)
    
    def store_enhanced_message(self, message_data: Dict[str, Any]) -> str:
        """Store message with enhanced metadata"""
        
        try:
            import re
            
            # Extract enhanced information
            content = message_data.get("content", "")
            agent_mentions = re.findall(r'@(\w+)', content)
            
            # Determine message type and importance
            role = message_data.get("role", "user")
            message_type = "conversation"
            importance_score = 0.5
            
            if agent_mentions:
                message_type = "collaboration" if len(agent_mentions) > 1 else "delegation"
                importance_score += 0.2
                
            if role in ["tool_call", "tool_result"]:
                message_type = "tool_usage"
                importance_score += 0.1
                
            if "document" in content.lower():
                message_type = "document_upload"
                importance_score += 0.1
            
            # Generate message ID
            import time
            message_id = f"msg_{int(time.time() * 1000)}_{hash(content) % 10000}"
            
            # Store in enhanced table
            _db_conn.execute(
                '''INSERT INTO enhanced_messages 
                   (id, group_id, sender, role, content, created_at, metadata,
                    message_type, agent_mentions, importance_score, context_summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    message_id,
                    message_data.get("group_id", ""),
                    message_data.get("sender", "user"),
                    role,
                    content,
                    datetime.now(),
                    json.dumps(message_data.get("metadata", {})),
                    message_type,
                    json.dumps(agent_mentions),
                    importance_score,
                    content[:100] + "..." if len(content) > 100 else content
                )
            )
            _db_conn.commit()
            
            # Invalidate cache for this group
            group_id = message_data.get("group_id")
            if group_id in self.context_cache:
                del self.context_cache[group_id]
            
            return message_id
            
        except Exception as e:
            print(f"❌ Failed to store enhanced message: {e}")
            return ""
    
    def cleanup_old_context_cache(self):
        """Clean up old context cache entries"""
        cutoff_time = datetime.now() - timedelta(minutes=self.cache_ttl_minutes)
        
        to_remove = []
        for group_id, context in self.context_cache.items():
            if context.last_updated < cutoff_time:
                to_remove.append(group_id)
        
        for group_id in to_remove:
            del self.context_cache[group_id]
        
        if to_remove:
            print(f"🧹 Cleaned up {len(to_remove)} old conversation caches")


# Global instance
conversation_manager = ConversationManager()