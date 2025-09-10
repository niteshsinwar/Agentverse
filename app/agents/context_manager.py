"""
Enhanced Context Manager for Multi-Agent Collaboration
Optimizes context transmission and agent memory management
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from .agent_memory import agent_memory, MemoryEntry

@dataclass
class AgentMemory:
    """Persistent memory for each agent across conversations"""
    agent_id: str
    group_id: str
    learned_facts: List[str]
    preferences: Dict[str, Any]
    collaboration_history: Dict[str, List[str]]  # {agent_id: [successful_interactions]}
    document_expertise: List[str]  # Documents this agent has analyzed
    last_updated: datetime

@dataclass 
class ConversationThread:
    """Track conversation threads for better context"""
    thread_id: str
    participants: List[str]  # Agent IDs involved
    topic: str
    messages: List[Dict[str, Any]]
    status: str  # active, completed, paused
    created_at: datetime

class EnhancedContextManager:
    """Advanced context management for multi-agent collaboration"""
    
    def __init__(self):
        self.agent_memories: Dict[str, AgentMemory] = {}
        self.conversation_threads: Dict[str, ConversationThread] = {}
        self.group_dynamics: Dict[str, Dict[str, Any]] = {}  # Group-specific settings
        
    def get_enhanced_context(self, agent_id: str, group_id: str, 
                           current_prompt: str) -> Dict[str, Any]:
        """Build comprehensive context with memory and thread awareness"""
        
        context = {
            'agent_memory': self._get_agent_memory(agent_id, group_id),
            'relevant_threads': self._get_relevant_threads(agent_id, group_id, current_prompt),
            'collaboration_insights': self._get_collaboration_insights(agent_id, group_id),
            'document_context': self._get_smart_document_context(agent_id, group_id, current_prompt),
            'group_dynamics': self._get_group_dynamics(group_id),
        }
        
        return context
    
    def _get_agent_memory(self, agent_id: str, group_id: str) -> Dict[str, Any]:
        """Get enhanced agent memory using RAG store"""
        
        # Get memory summary from RAG-based system
        memory_summary = agent_memory.get_memory_summary(agent_id)
        
        # Get recent contextual memories
        context = {
            "group_id": group_id,
            "recent_interaction": True
        }
        contextual_memories = agent_memory.get_contextual_memories(agent_id, context, limit=10)
        
        # Build enhanced memory context
        enhanced_memory = {
            "summary": memory_summary,
            "recent_facts": [m.content for m in contextual_memories if m.entry_type == "fact"][:5],
            "collaboration_patterns": [m.content for m in contextual_memories if m.entry_type == "collaboration"][:3],
            "learned_insights": [m.content for m in contextual_memories if m.entry_type == "insight"][:3],
            "successful_experiences": [m.content for m in contextual_memories if m.entry_type == "experience"][:3],
            "contextual_memories": contextual_memories
        }
        
        return enhanced_memory
    
    def _get_relevant_threads(self, agent_id: str, group_id: str, 
                            prompt: str) -> List[ConversationThread]:
        """Find conversation threads relevant to current prompt"""
        # Smart thread matching based on keywords, participants, etc.
        relevant = []
        for thread in self.conversation_threads.values():
            if (agent_id in thread.participants and 
                group_id in thread.thread_id and
                self._is_thread_relevant(thread, prompt)):
                relevant.append(thread)
        
        return sorted(relevant, key=lambda x: x.created_at, reverse=True)[:3]
    
    def _is_thread_relevant(self, thread: ConversationThread, prompt: str) -> bool:
        """Determine if a thread is relevant to current conversation"""
        # Simple keyword matching - can be enhanced with embedding similarity
        prompt_words = set(prompt.lower().split())
        thread_words = set(thread.topic.lower().split())
        
        # If 30% of words overlap, consider relevant
        overlap = len(prompt_words & thread_words) / max(len(prompt_words), 1)
        return overlap > 0.3
        
    def _get_collaboration_insights(self, agent_id: str, group_id: str) -> Dict[str, Any]:
        """Get insights about how this agent collaborates with others"""
        memory = self._get_agent_memory(agent_id, group_id)
        
        insights = {
            'frequent_collaborators': [],
            'successful_delegation_patterns': [],
            'preferred_workflows': []
        }
        
        # Analyze collaboration history
        for other_agent, interactions in memory.collaboration_history.items():
            if len(interactions) > 3:
                insights['frequent_collaborators'].append({
                    'agent': other_agent,
                    'interaction_count': len(interactions),
                    'success_rate': self._calculate_success_rate(interactions)
                })
        
        return insights
    
    def _calculate_success_rate(self, interactions: List[str]) -> float:
        """Calculate success rate of interactions (simplified)"""
        # This would analyze outcomes of interactions
        successful = sum(1 for i in interactions if 'success' in i.lower())
        return successful / len(interactions) if interactions else 0.0
    
    def _get_smart_document_context(self, agent_id: str, group_id: str, 
                                   prompt: str) -> Dict[str, Any]:
        """Get contextually relevant document information"""
        from app.document_processing.manager import document_manager
        
        # Get documents relevant to this specific query
        documents = document_manager.get_recent_documents(agent_id, group_id, limit=5)
        
        if not documents:
            return {'documents': [], 'context': 'No documents available'}
            
        # Filter documents based on prompt relevance
        relevant_docs = self._filter_relevant_documents(documents, prompt)
        
        return {
            'documents': relevant_docs,
            'context': document_manager.get_agent_document_context(agent_id, group_id),
            'document_count': len(relevant_docs),
            'total_available': len(documents)
        }
    
    def _filter_relevant_documents(self, documents: List[Dict], prompt: str) -> List[Dict]:
        """Filter documents based on relevance to current prompt"""
        # Simple relevance scoring - can be enhanced with embeddings
        relevant = []
        prompt_words = set(prompt.lower().split())
        
        for doc in documents:
            doc_content = (doc.get('extracted_content', '') + ' ' + 
                          doc.get('content_summary', '')).lower()
            doc_words = set(doc_content.split())
            
            # Calculate relevance score
            overlap = len(prompt_words & doc_words) / max(len(prompt_words), 1)
            if overlap > 0.1:  # At least 10% word overlap
                doc['relevance_score'] = overlap
                relevant.append(doc)
        
        return sorted(relevant, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _get_group_dynamics(self, group_id: str) -> Dict[str, Any]:
        """Get group-specific collaboration patterns and rules"""
        return self.group_dynamics.get(group_id, {
            'collaboration_style': 'democratic',  # democratic, hierarchical, specialized
            'preferred_workflows': [],
            'group_memory': {},
            'established_patterns': []
        })
    
    def update_agent_memory(self, agent_id: str, group_id: str, 
                          interaction_data: Dict[str, Any]):
        """Update agent memory based on interaction outcomes"""
        memory = self._get_agent_memory(agent_id, group_id)
        
        # Update learned facts
        if 'learned_facts' in interaction_data:
            memory.learned_facts.extend(interaction_data['learned_facts'])
            
        # Update collaboration history
        if 'collaborated_with' in interaction_data:
            collaborator = interaction_data['collaborated_with']
            if collaborator not in memory.collaboration_history:
                memory.collaboration_history[collaborator] = []
            memory.collaboration_history[collaborator].append(
                f"{datetime.now()}: {interaction_data.get('outcome', 'completed')}"
            )
        
        # Update document expertise
        if 'analyzed_documents' in interaction_data:
            memory.document_expertise.extend(interaction_data['analyzed_documents'])
            
        memory.last_updated = datetime.now()

# Global instance
enhanced_context_manager = EnhancedContextManager()