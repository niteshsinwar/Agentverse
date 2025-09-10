"""
Memory Integration Hooks for Agent Learning
Automatically captures and stores agent memories from interactions
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from .agent_memory import agent_memory, MemoryEntry


class MemoryLearningHooks:
    """Hooks to automatically capture agent learning from interactions"""
    
    def __init__(self):
        self.learning_patterns = {
            "success_indicators": [
                r"successfully.*(?:completed|finished|solved)",
                r"great job", r"well done", r"excellent work",
                r"that helped", r"useful", r"exactly what I needed"
            ],
            "collaboration_indicators": [
                r"@(\w+).*(?:helped|assisted|collaborated)",
                r"working together with @(\w+)",
                r"thanks to @(\w+)"
            ],
            "insight_indicators": [
                r"I learned that", r"now I understand", r"the key insight is",
                r"it turns out", r"discovered that", r"found out"
            ],
            "preference_indicators": [
                r"I prefer", r"I usually", r"I typically",
                r"my approach is", r"I like to"
            ]
        }
    
    async def capture_interaction_learning(self, agent_id: str, interaction_data: Dict[str, Any]):
        """Main hook to capture learning from agent interactions"""
        
        try:
            # Extract context
            group_id = interaction_data.get("group_id", "")
            user_message = interaction_data.get("user_message", "")
            agent_response = interaction_data.get("agent_response", "")
            tool_calls = interaction_data.get("tool_calls", [])
            other_agents = interaction_data.get("other_agents_involved", [])
            document_context = interaction_data.get("document_context", {})
            
            memories_to_store = []
            
            # 1. Learn from successful interactions
            memories_to_store.extend(
                self._extract_success_memories(agent_id, user_message, agent_response)
            )
            
            # 2. Learn from collaboration patterns
            memories_to_store.extend(
                self._extract_collaboration_memories(agent_id, agent_response, other_agents)
            )
            
            # 3. Learn from insights and discoveries
            memories_to_store.extend(
                self._extract_insight_memories(agent_id, agent_response, user_message)
            )
            
            # 4. Learn from tool usage patterns
            memories_to_store.extend(
                self._extract_tool_memories(agent_id, tool_calls, agent_response)
            )
            
            # 5. Learn from document analysis
            memories_to_store.extend(
                self._extract_document_memories(agent_id, document_context, agent_response)
            )
            
            # 6. Learn user preferences and feedback
            memories_to_store.extend(
                self._extract_preference_memories(agent_id, user_message, agent_response)
            )
            
            # Store all extracted memories
            for memory in memories_to_store:
                agent_memory.store_memory(agent_id, memory)
                
            if memories_to_store:
                print(f"🧠 Captured {len(memories_to_store)} memories for {agent_id}")
                
        except Exception as e:
            print(f"❌ Memory capture failed for {agent_id}: {e}")
    
    def _extract_success_memories(self, agent_id: str, user_message: str, 
                                agent_response: str) -> List[MemoryEntry]:
        """Extract memories from successful interactions"""
        memories = []
        
        # Check for success indicators in user feedback
        combined_text = f"{user_message} {agent_response}".lower()
        
        for pattern in self.learning_patterns["success_indicators"]:
            if re.search(pattern, combined_text):
                memory = MemoryEntry(
                    entry_type="experience",
                    content=f"Successfully handled request: {user_message[:100]}...",
                    context={"success_pattern": pattern, "response_preview": agent_response[:50]},
                    importance=0.7,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=["success", "experience", "user_satisfaction"]
                )
                memories.append(memory)
                break
        
        return memories
    
    def _extract_collaboration_memories(self, agent_id: str, agent_response: str, 
                                      other_agents: List[str]) -> List[MemoryEntry]:
        """Extract collaboration learning"""
        memories = []
        
        # Look for collaboration mentions in response
        for pattern in self.learning_patterns["collaboration_indicators"]:
            matches = re.finditer(pattern, agent_response.lower())
            for match in matches:
                if match.groups():
                    collaborator = match.group(1)
                    memory = MemoryEntry(
                        entry_type="collaboration",
                        content=f"Successfully collaborated with @{collaborator} on task",
                        context={"collaborator": collaborator, "interaction_context": agent_response[:100]},
                        importance=0.6,
                        created_at=datetime.now(),
                        last_accessed=datetime.now(),
                        tags=["collaboration", collaborator, "teamwork"]
                    )
                    memories.append(memory)
        
        # Learn from agent mentions in response (even without explicit success)
        agent_mentions = re.findall(r"@(\w+)", agent_response)
        for mentioned_agent in agent_mentions:
            if mentioned_agent != agent_id and mentioned_agent in other_agents:
                memory = MemoryEntry(
                    entry_type="collaboration",
                    content=f"Worked with @{mentioned_agent} - delegated or coordinated task",
                    context={"collaborator": mentioned_agent, "delegation": True},
                    importance=0.4,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=["collaboration", mentioned_agent, "delegation"]
                )
                memories.append(memory)
        
        return memories
    
    def _extract_insight_memories(self, agent_id: str, agent_response: str, 
                                user_message: str) -> List[MemoryEntry]:
        """Extract insights and learning discoveries"""
        memories = []
        
        combined_text = f"{user_message} {agent_response}".lower()
        
        # Look for insight patterns
        for pattern in self.learning_patterns["insight_indicators"]:
            matches = re.finditer(pattern + r"(.{0,100})", combined_text)
            for match in matches:
                insight_text = match.group(1) if match.groups() else match.group(0)
                
                memory = MemoryEntry(
                    entry_type="insight",
                    content=f"Key insight: {insight_text.strip()}",
                    context={"discovery_context": user_message[:50]},
                    importance=0.8,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=["insight", "learning", "discovery"]
                )
                memories.append(memory)
        
        return memories
    
    def _extract_tool_memories(self, agent_id: str, tool_calls: List[Dict], 
                             agent_response: str) -> List[MemoryEntry]:
        """Extract learning from tool usage"""
        memories = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "unknown")
            success = tool_call.get("success", True)
            
            # Determine importance based on success and complexity
            importance = 0.6 if success else 0.4
            
            memory = MemoryEntry(
                entry_type="experience",
                content=f"Used tool '{tool_name}' with {'success' if success else 'issues'}",
                context={
                    "tool": tool_name,
                    "success": success,
                    "parameters": tool_call.get("parameters", {}),
                    "result_preview": str(tool_call.get("result", ""))[:50]
                },
                importance=importance,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["tool", tool_name, "success" if success else "failure"]
            )
            memories.append(memory)
        
        return memories
    
    def _extract_document_memories(self, agent_id: str, document_context: Dict, 
                                 agent_response: str) -> List[MemoryEntry]:
        """Extract learning from document analysis"""
        memories = []
        
        if document_context and document_context.get("documents"):
            for doc in document_context["documents"][:3]:  # Limit to 3 docs
                doc_type = doc.get("file_extension", "unknown")
                doc_name = doc.get("filename", "document")
                
                # Extract insights about document handling
                if "analyzed" in agent_response.lower() or "image" in agent_response.lower():
                    memory = MemoryEntry(
                        entry_type="insight",
                        content=f"Successfully analyzed {doc_type} document: {doc_name}",
                        context={
                            "document_type": doc_type,
                            "document_name": doc_name,
                            "analysis_approach": agent_response[:100]
                        },
                        importance=0.5,
                        created_at=datetime.now(),
                        last_accessed=datetime.now(),
                        tags=["document", doc_type, "analysis"]
                    )
                    memories.append(memory)
        
        return memories
    
    def _extract_preference_memories(self, agent_id: str, user_message: str, 
                                   agent_response: str) -> List[MemoryEntry]:
        """Extract user preferences and agent behavioral patterns"""
        memories = []
        
        # Look for preference indicators in agent's own response
        for pattern in self.learning_patterns["preference_indicators"]:
            matches = re.finditer(pattern + r"(.{0,80})", agent_response.lower())
            for match in matches:
                preference_text = match.group(1) if match.groups() else match.group(0)
                
                memory = MemoryEntry(
                    entry_type="preference",
                    content=f"Agent preference: {preference_text.strip()}",
                    context={"context": user_message[:50]},
                    importance=0.3,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    tags=["preference", "behavior", "style"]
                )
                memories.append(memory)
        
        return memories
    
    def capture_conversation_outcome(self, agent_id: str, outcome_data: Dict[str, Any]):
        """Capture high-level conversation outcomes"""
        
        try:
            outcome_type = outcome_data.get("outcome", "completed")
            user_satisfied = outcome_data.get("user_satisfied", True)
            agents_involved = outcome_data.get("agents_involved", [])
            
            # Store conversation outcome memory
            memory = MemoryEntry(
                entry_type="fact",
                content=f"Conversation outcome: {outcome_type} ({'successful' if user_satisfied else 'needs improvement'})",
                context={
                    "agents_involved": agents_involved,
                    "duration": outcome_data.get("duration_minutes", 0),
                    "messages_count": outcome_data.get("message_count", 0)
                },
                importance=0.5 if user_satisfied else 0.7,  # Higher importance for failures to learn from
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                tags=["conversation", "outcome", outcome_type]
            )
            
            agent_memory.store_memory(agent_id, memory)
            
        except Exception as e:
            print(f"❌ Failed to capture conversation outcome for {agent_id}: {e}")


# Global instance
memory_hooks = MemoryLearningHooks()