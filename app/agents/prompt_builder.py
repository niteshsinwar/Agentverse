"""
Advanced System Prompt Builder for Multi-Agent Collaboration
Creates contextually rich, dynamic prompts for optimal agent behavior
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime
from .context_manager import enhanced_context_manager

class AdvancedPromptBuilder:
    """Builds optimized system prompts with rich context and collaboration guidance"""
    
    def __init__(self):
        self.context_manager = enhanced_context_manager
    
    def build_collaborative_prompt(self, agent_id: str, group_id: str, 
                                 current_prompt: str, orchestrator=None) -> str:
        """Build an enhanced system prompt for multi-agent collaboration"""
        
        # Get enhanced context
        context = self.context_manager.get_enhanced_context(agent_id, group_id, current_prompt)
        
        # Get agent metadata
        from app.agents.registry import discover_agents
        agent_specs = discover_agents()
        agent_spec = agent_specs.get(agent_id)
        
        if not agent_spec:
            return self._fallback_prompt(agent_id)
            
        # Build comprehensive prompt
        prompt_sections = []
        
        # 1. Core Identity (Enhanced)
        prompt_sections.append(self._build_identity_section(agent_spec, context))
        
        # 2. Advanced Capabilities 
        prompt_sections.append(self._build_capabilities_section(agent_id, context))
        
        # 3. Collaboration Intelligence
        prompt_sections.append(self._build_collaboration_section(group_id, orchestrator, context))
        
        # 4. Memory & Learning
        prompt_sections.append(self._build_memory_section(context['agent_memory']))
        
        # 5. Document & Context Intelligence
        prompt_sections.append(self._build_document_section(context['document_context']))
        
        # 6. Conversation Threads
        prompt_sections.append(self._build_threads_section(context['relevant_threads']))
        
        # 7. Advanced Action Framework
        prompt_sections.append(self._build_action_framework())
        
        # 8. Collaboration Rules & Ethics
        prompt_sections.append(self._build_collaboration_rules())
        
        return "\\n\\n".join(prompt_sections)
    
    def _build_identity_section(self, agent_spec, context: Dict[str, Any]) -> str:
        """Enhanced agent identity with personality and expertise"""
        return f"""🤖 **AGENT IDENTITY & EXPERTISE**
Agent ID: {agent_spec.key}
Name: {agent_spec.name} {agent_spec.emoji}
Specialty: {agent_spec.description}

🧠 **KNOWLEDGE BASE**:
• Document Expertise: {len(context['agent_memory'].document_expertise)} documents analyzed
• Collaboration Experience: {len(context['agent_memory'].collaboration_history)} partnerships
• Learned Facts: {len(context['agent_memory'].learned_facts)} insights accumulated

🎯 **MISSION**: You are an expert collaborative AI agent specialized in your domain. 
Your goal is to provide accurate, helpful responses while actively collaborating 
with other agents to create comprehensive solutions."""
    
    def _build_capabilities_section(self, agent_id: str, context: Dict[str, Any]) -> str:
        """Enhanced capabilities with smart tool awareness"""
        from app.agents.orchestrator import AgentOrchestrator
        
        # This would get the actual agent instance to check capabilities
        capabilities_text = "📋 **YOUR CAPABILITIES**:\\n"
        
        # Custom tools
        capabilities_text += "🛠️ **Custom Tools**: [Will be dynamically loaded]\\n"
        
        # MCP Tools  
        capabilities_text += "🔌 **MCP Integrations**: [Will be dynamically loaded]\\n"
        
        # Collaboration insights
        insights = context['collaboration_insights']
        if insights['frequent_collaborators']:
            capabilities_text += f"🤝 **Frequent Collaborators**: "
            for collab in insights['frequent_collaborators'][:3]:
                capabilities_text += f"@{collab['agent']} ({collab['success_rate']:.0%} success) "
            capabilities_text += "\\n"
            
        return capabilities_text
    
    def _build_collaboration_section(self, group_id: str, orchestrator, context: Dict[str, Any]) -> str:
        """Advanced collaboration intelligence"""
        
        # Get group roster
        roster_lines = "👥 **GROUP MEMBERS & SPECIALTIES**:\\n"
        if orchestrator:
            roster = orchestrator.group_roster(group_id)
            for key, name, desc in roster:
                roster_lines += f"• @{key} — **{name}**: {desc}\\n"
        else:
            roster_lines += "• No other members currently active\\n"
            
        # Group dynamics
        dynamics = context['group_dynamics']
        collaboration_style = dynamics.get('collaboration_style', 'democratic')
        
        collaboration_text = f"""{roster_lines}

🎭 **GROUP DYNAMICS**:
• Collaboration Style: {collaboration_style}
• Workflow Preference: Efficient multi-agent coordination
• Communication Style: Professional, clear, action-oriented

🧭 **COLLABORATION INTELLIGENCE**:
• Study other agents' specialties before responding
• Delegate tasks that match other agents' expertise  
• Build on previous conversations and established patterns
• Maintain conversation threads and context continuity"""

        return collaboration_text
    
    def _build_memory_section(self, enhanced_memory: Dict[str, Any]) -> str:
        """Enhanced agent memory and learning context using RAG store"""
        
        summary = enhanced_memory.get("summary", {})
        
        memory_text = f"""🧠 **YOUR LONG-TERM MEMORY** (RAG-Enhanced):
📊 **Memory Stats**: {summary.get('total_memories', 0)} memories stored | Avg Importance: {summary.get('average_importance', 0.0)}
🕒 **Last Access**: {summary.get('last_access', 'Never')}
📁 **Memory Types**: {summary.get('memory_types', {})}

"""
        
        # Recent facts learned
        recent_facts = enhanced_memory.get("recent_facts", [])
        if recent_facts:
            memory_text += "💡 **Recent Key Facts**:\\n"
            for fact in recent_facts[:3]:
                memory_text += f"  • {fact}\\n"
            memory_text += "\\n"
        
        # Collaboration patterns
        collab_patterns = enhanced_memory.get("collaboration_patterns", [])
        if collab_patterns:
            memory_text += "🤝 **Collaboration Patterns**:\\n"
            for pattern in collab_patterns[:3]:
                memory_text += f"  • {pattern}\\n"
            memory_text += "\\n"
        
        # Learned insights
        insights = enhanced_memory.get("learned_insights", [])
        if insights:
            memory_text += "🎯 **Learned Insights**:\\n"
            for insight in insights[:3]:
                memory_text += f"  • {insight}\\n"
            memory_text += "\\n"
        
        # Successful experiences
        experiences = enhanced_memory.get("successful_experiences", [])
        if experiences:
            memory_text += "✅ **Successful Experiences**:\\n"
            for exp in experiences[:2]:
                memory_text += f"  • {exp}\\n"
            memory_text += "\\n"
        
        memory_text += "🧠 **Memory Intelligence**: Your memories are searchable and contextually retrieved to inform your responses."
        
        return memory_text
    
    def _build_document_section(self, doc_context: Dict[str, Any]) -> str:
        """Enhanced document context"""
        
        if not doc_context or doc_context.get('document_count', 0) == 0:
            return "📄 **DOCUMENT CONTEXT**: No documents currently available for analysis."
            
        doc_text = f"""📄 **DOCUMENT INTELLIGENCE**:
• Available Documents: {doc_context['document_count']} relevant, {doc_context['total_available']} total
• Context Status: ✅ Document content loaded and ready for analysis
• Analysis Capability: You can directly analyze document content using your LLM capabilities

{doc_context['context']}"""

        return doc_text
    
    def _build_threads_section(self, threads: List) -> str:
        """Conversation thread awareness"""
        
        if not threads:
            return "💬 **CONVERSATION THREADS**: Starting fresh conversation."
            
        threads_text = f"💬 **RELEVANT CONVERSATION THREADS** ({len(threads)} found):\\n"
        
        for i, thread in enumerate(threads[:2], 1):  # Show top 2 threads
            threads_text += f"{i}. **{thread.topic}** - {len(thread.messages)} messages, "
            threads_text += f"participants: {', '.join(thread.participants)}\\n"
            
        threads_text += "\\n💡 **Thread Intelligence**: Reference these conversations for context continuity."
        
        return threads_text
    
    def _build_action_framework(self) -> str:
        """Advanced action framework with collaboration patterns"""
        
        return """🎮 **ACTION FRAMEWORK** - Return STRICT JSON:

**Primary Actions**:
• `{"action":"final","text":"Your response"}` - Normal conversation & conclusions
• `{"action":"call_tool","tool_name":"tool","kwargs":{...}}` - Use your registered tools
• `{"action":"call_mcp","server":"server","tool":"tool","params":{...}}` - MCP operations
• `{"action":"collaborate","target":"@agent_id","request":"specific_task","context":"background_info"}` - Enhanced agent collaboration

**Collaboration Patterns**:
• **Delegation**: `{"action":"final","text":"@agent_name please handle X because you specialize in Y"}`
• **Information Gathering**: Ask other agents for their expertise before proceeding
• **Workflow Continuation**: Build upon other agents' work rather than starting over
• **Result Synthesis**: Combine insights from multiple agents for comprehensive solutions

**Decision Priority**:
1. Can I handle this with my tools/knowledge? → Use appropriate action
2. Would another agent be better suited? → Delegate with clear context
3. Do I need more information? → Request from relevant agents
4. Should I collaborate for a better outcome? → Initiate multi-agent workflow"""
    
    def _build_collaboration_rules(self) -> str:
        """Enhanced collaboration rules and ethics"""
        
        return """⚖️ **COLLABORATION PROTOCOL & ETHICS**:

**🎯 Communication Excellence**:
• Be clear, specific, and actionable in all communications
• Provide context when delegating or requesting help
• Acknowledge other agents' contributions explicitly
• Use professional, respectful language

**🔄 Workflow Intelligence**:
• PREFER multi-agent solutions over single-agent limitations
• Continue conversations rather than breaking to user prematurely
• Build comprehensive solutions through agent collaboration
• Maintain conversation context and thread continuity

**🏷️ Smart Tagging Strategy**:
• Tag `@user` ONLY when: solution complete, user input needed, or unrecoverable error
• Tag `@agent_name` when: delegating, requesting help, or collaborating
• Think: "Who is best equipped to handle this?" before responding
• NEVER tag non-existent agents or agents outside the group

**🛡️ Quality & Safety**:
• Only use tools you have registered - never invent tools
• If tools fail, use document context and LLM capabilities to proceed
• Validate information before sharing with other agents
• Maintain data privacy and security in all interactions

**📈 Continuous Learning**:
• Learn from successful collaboration patterns
• Adapt communication style based on other agents' responses
• Build on established group workflows and preferences
• Contribute to group knowledge and efficiency

**⚡ Performance Rules**:
• Execute ONE action per response - no multiple JSON objects
• Default to 'final' action for normal conversation
• Use tools/MCP only when specifically required
• Process requests efficiently while maintaining quality"""
    
    def _fallback_prompt(self, agent_id: str) -> str:
        """Fallback prompt when agent spec not found"""
        return f"""🤖 Agent: {agent_id}
Basic collaborative agent ready to assist.
Please specify your capabilities and collaborate with other agents as needed.
Return JSON: {{"action":"final","text":"your response"}}"""

# Global instance
advanced_prompt_builder = AdvancedPromptBuilder()