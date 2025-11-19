# AgentVerse Refactoring Plan - Public Contracts & Black Box Architecture

## 🎯 GOAL: Each File as Black Box with Limited Public Contract

### **PRINCIPLE:**
- Every module exposes a **small, stable public contract**
- Modules **never** access internals of other modules
- All dependencies **injected**, not imported directly
- Changes to internal implementation **never** affect callers

---

## 📋 STEP 1: Define Core Public Contracts

### **File: `backend/src/core/contracts/agents.py`** (NEW)

```python
"""
Public contracts for agent system.
All modules must depend on THIS, not implementation files.
"""
from typing import Protocol, Dict, Any, List
from dataclasses import dataclass

# ============================================================================
# PUBLIC CONTRACT: Agent
# ============================================================================
class Agent(Protocol):
    """
    Public interface for all agents.

    BLACK BOX: Callers don't know:
    - How agents are built
    - What LLM they use
    - How they load tools
    - Internal state management

    PUBLIC CONTRACT: Callers only know:
    - They can send a prompt and get a response
    - They can get capabilities summary
    """

    @property
    def agent_id(self) -> str:
        """Unique agent identifier"""
        ...

    async def respond(
        self,
        prompt: str,
        group_id: str,
        **context
    ) -> Dict[str, Any]:
        """
        Process prompt and return response.

        Returns:
            {"text": str, "agent_id": str, "group_id": str}
        """
        ...

    def get_capabilities_summary(self) -> str:
        """Get human-readable capabilities"""
        ...


# ============================================================================
# PUBLIC CONTRACT: AgentRegistry
# ============================================================================
class AgentRegistry(Protocol):
    """
    Public interface for agent discovery and creation.

    BLACK BOX: Callers don't know:
    - Where agents are stored
    - How agents are discovered
    - How agents are built

    PUBLIC CONTRACT: Callers only know:
    - They can list available agents
    - They can get an agent by ID
    """

    def list_available(self) -> Dict[str, 'AgentSpec']:
        """List all available agent specifications"""
        ...

    async def get_agent(self, agent_id: str) -> Agent:
        """Get or create agent instance"""
        ...

    def refresh(self) -> None:
        """Refresh agent discovery"""
        ...


# ============================================================================
# PUBLIC DATA: AgentSpec (immutable)
# ============================================================================
@dataclass(frozen=True)
class AgentSpec:
    """
    Agent specification - PUBLIC data structure.
    This is the ONLY way to describe an agent.
    """
    key: str
    name: str
    description: str
    emoji: str
    llm_provider: str
    llm_model: str
    folder_path: str
```

### **File: `backend/src/core/contracts/tools.py`** (NEW)

```python
"""Public contracts for tool system"""
from typing import Protocol, List, Dict, Any, Callable

# ============================================================================
# PUBLIC CONTRACT: Tool
# ============================================================================
class Tool(Protocol):
    """
    Public interface for all tools.

    BLACK BOX: Callers don't know:
    - Where tool came from (MCP, custom, global)
    - How tool is implemented
    - Internal validation logic

    PUBLIC CONTRACT: Callers only know:
    - Tool name, description, parameters
    - They can execute it
    """

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def parameters(self) -> Dict[str, Any]: ...

    async def execute(self, **kwargs) -> Any:
        """Execute tool with parameters"""
        ...


# ============================================================================
# PUBLIC CONTRACT: ToolRegistry
# ============================================================================
class ToolRegistry(Protocol):
    """
    Public interface for tool discovery.

    BLACK BOX: Callers don't know:
    - How tools are discovered
    - How tools are loaded
    - How tools are validated

    PUBLIC CONTRACT: Callers only know:
    - They can get all tools
    - They can get tools for specific agent
    """

    def discover_all(self) -> List[Tool]:
        """Discover all available tools"""
        ...

    def discover_for_agent(self, agent_id: str) -> List[Tool]:
        """Discover tools for specific agent"""
        ...
```

### **File: `backend/src/core/contracts/storage.py`** (NEW)

```python
"""Public contracts for storage/persistence"""
from typing import Protocol, List, Dict, Any, Optional

# ============================================================================
# PUBLIC CONTRACT: ConversationStore
# ============================================================================
class ConversationStore(Protocol):
    """
    Public interface for conversation persistence.

    BLACK BOX: Callers don't know:
    - Database technology (SQLite, PostgreSQL, etc.)
    - Table schema
    - Indexing strategy

    PUBLIC CONTRACT: Callers only know:
    - They can append messages
    - They can retrieve history
    - They can manage groups
    """

    def append_message(
        self,
        group_id: str,
        sender: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append message to conversation"""
        ...

    def get_history(self, group_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        ...

    def create_group(self, name: str) -> str:
        """Create new group, return group_id"""
        ...

    def list_groups(self) -> List[Dict[str, Any]]:
        """List all groups"""
        ...


# ============================================================================
# PUBLIC CONTRACT: VectorStore
# ============================================================================
class VectorStore(Protocol):
    """
    Public interface for vector storage.

    BLACK BOX: Callers don't know:
    - Vector database (ChromaDB, Pinecone, etc.)
    - Embedding strategy
    - Indexing details

    PUBLIC CONTRACT: Callers only know:
    - They can store documents
    - They can search by similarity
    """

    def store_chunks(
        self,
        chunks: List[str],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Store document chunks with metadata"""
        ...

    def search(
        self,
        query: str,
        group_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        ...
```

### **File: `backend/src/core/contracts/events.py`** (NEW)

```python
"""Public contracts for event system"""
from typing import Protocol, Callable, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# PUBLIC DATA: Event
# ============================================================================
class EventType(Enum):
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    AGENT_THOUGHT = "agent_thought"
    ERROR = "error"
    MCP_CALL = "mcp_call"

@dataclass(frozen=True)
class Event:
    """Public event structure"""
    type: EventType
    group_id: str
    agent_id: str
    payload: Dict[str, Any]


# ============================================================================
# PUBLIC CONTRACT: EventBus
# ============================================================================
class EventBus(Protocol):
    """
    Public interface for event emission.

    BLACK BOX: Callers don't know:
    - Event transport (SSE, WebSocket, etc.)
    - Event storage
    - Subscriber management

    PUBLIC CONTRACT: Callers only know:
    - They can emit events
    - They can subscribe to events
    """

    async def emit(self, event: Event) -> None:
        """Emit event to all subscribers"""
        ...

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ) -> None:
        """Subscribe to event type"""
        ...
```

---

## 📋 STEP 2: Refactor Implementations to Use Contracts

### **Before: base_agent.py (Tight Coupling)**

```python
# ❌ BAD: Direct imports, tight coupling
from src.core.memory import session_store
from src.core.llm.factory import get_llm
from src.core.agents.context_builder import context_builder
from src.core.telemetry.events import emit_error

class EnhancedBaseAgent:
    def __init__(self, agent_id, llm_config):
        self.agent_id = agent_id
        self.llm_config = llm_config

    async def respond(self, prompt, group_id, orchestrator, ...):
        # ❌ Directly accessing globals
        roster = orchestrator.group_roster(group_id)
        agent_identity = await context_builder.build_react_agent_identity(...)
        llm_instance = get_llm(provider=self.llm_config.get("provider"), ...)
```

### **After: base_agent.py (Dependency Injection)**

```python
# ✅ GOOD: Depends on contracts only
from src.core.contracts.agents import Agent
from src.core.contracts.storage import ConversationStore
from src.core.contracts.events import EventBus, Event, EventType

class EnhancedBaseAgent:
    """
    Implementation of Agent contract.

    PUBLIC CONTRACT (from Protocol):
    - agent_id property
    - respond() method
    - get_capabilities_summary() method

    PRIVATE (internal implementation):
    - All other methods and attributes
    """

    def __init__(
        self,
        agent_id: str,
        llm_config: Dict[str, str],
        conversation_store: ConversationStore,  # ✅ Injected
        event_bus: EventBus,                    # ✅ Injected
        context_builder: ContextBuilder,        # ✅ Injected
        llm_factory: LLMFactory                 # ✅ Injected
    ):
        self._agent_id = agent_id
        self._llm_config = llm_config
        self._conversation_store = conversation_store  # ✅ Treat as black box
        self._event_bus = event_bus                    # ✅ Treat as black box
        self._context_builder = context_builder        # ✅ Treat as black box
        self._llm_factory = llm_factory                # ✅ Treat as black box

    @property
    def agent_id(self) -> str:
        """PUBLIC: Part of Agent protocol"""
        return self._agent_id

    async def respond(self, prompt: str, group_id: str, **context) -> Dict[str, Any]:
        """PUBLIC: Part of Agent protocol"""
        # ✅ Use injected dependencies through their public contracts
        history = self._conversation_store.get_history(group_id)
        llm = self._llm_factory.create(self._llm_config)

        # ✅ Emit event through public contract
        await self._event_bus.emit(Event(
            type=EventType.MESSAGE,
            group_id=group_id,
            agent_id=self._agent_id,
            payload={"content": prompt}
        ))

        # ... rest of implementation

    def get_capabilities_summary(self) -> str:
        """PUBLIC: Part of Agent protocol"""
        return f"Agent {self._agent_id} with {len(self._tools)} tools"

    # ✅ PRIVATE methods (not part of protocol)
    def _build_context(self, ...):
        """PRIVATE: Internal helper"""
        pass
```

---

## 📋 STEP 3: Create Dependency Injection Container

### **File: `backend/src/core/di_container.py`** (NEW)

```python
"""
Dependency Injection Container
Wires up all dependencies so modules don't need to know about each other
"""
from typing import Dict, Any
from src.core.contracts.agents import Agent, AgentRegistry
from src.core.contracts.tools import ToolRegistry
from src.core.contracts.storage import ConversationStore, VectorStore
from src.core.contracts.events import EventBus

class Container:
    """
    Dependency injection container.

    All modules get their dependencies from here.
    Modules NEVER import concrete implementations directly.
    """

    def __init__(self):
        self._singletons: Dict[str, Any] = {}

    def get_conversation_store(self) -> ConversationStore:
        """Get conversation store instance"""
        if 'conversation_store' not in self._singletons:
            from src.core.storage.session_store import SessionStore
            self._singletons['conversation_store'] = SessionStore()
        return self._singletons['conversation_store']

    def get_event_bus(self) -> EventBus:
        """Get event bus instance"""
        if 'event_bus' not in self._singletons:
            from src.core.events.event_bus import EventBusImpl
            self._singletons['event_bus'] = EventBusImpl()
        return self._singletons['event_bus']

    def get_tool_registry(self) -> ToolRegistry:
        """Get tool registry instance"""
        if 'tool_registry' not in self._singletons:
            from src.core.tools.registry import ToolRegistryImpl
            self._singletons['tool_registry'] = ToolRegistryImpl()
        return self._singletons['tool_registry']

    def get_agent_registry(self) -> AgentRegistry:
        """Get agent registry instance"""
        if 'agent_registry' not in self._singletons:
            from src.core.agents.registry_impl import AgentRegistryImpl
            # ✅ Inject all dependencies
            registry = AgentRegistryImpl(
                conversation_store=self.get_conversation_store(),
                event_bus=self.get_event_bus(),
                tool_registry=self.get_tool_registry()
            )
            self._singletons['agent_registry'] = registry
        return self._singletons['agent_registry']


# Global container instance
container = Container()
```

---

## 📋 STEP 4: Update Callers to Use Container

### **Before: orchestrator_service.py**

```python
# ❌ BAD: Direct imports
from src.core.agents.agent_coordinator import AgentOrchestrator
from src.core.memory import session_store

class OrchestratorService:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()  # ❌ Direct creation

    def get_group_messages(self, group_id):
        return session_store.get_history(group_id)  # ❌ Direct access to global
```

### **After: orchestrator_service.py**

```python
# ✅ GOOD: Use contracts via DI container
from src.core.contracts.agents import AgentRegistry
from src.core.contracts.storage import ConversationStore
from src.core.di_container import container

class OrchestratorService:
    def __init__(
        self,
        agent_registry: AgentRegistry = None,      # ✅ Injectable
        conversation_store: ConversationStore = None  # ✅ Injectable
    ):
        # ✅ Use container as default, but allow injection for testing
        self._agent_registry = agent_registry or container.get_agent_registry()
        self._conversation_store = conversation_store or container.get_conversation_store()

    def get_group_messages(self, group_id: str):
        # ✅ Use through public contract
        return self._conversation_store.get_history(group_id)
```

---

## 📋 STEP 5: Consolidate Scattered Logic

### **Tool Registry Consolidation**

**Before (4 files):**
```
registry.py → _import_tools_py()
base_agent.py → register_tools_from_module()
langchain_tool_wrapper.py → _wrap_custom_tool()
tool_validator.py → validate_tool_code_execution()
```

**After (1 file):**

```python
# File: backend/src/core/tools/registry_impl.py

from src.core.contracts.tools import Tool, ToolRegistry
from typing import List

class ToolRegistryImpl:
    """
    Implementation of ToolRegistry contract.

    PUBLIC (from protocol):
    - discover_all()
    - discover_for_agent()

    PRIVATE (internal):
    - All other methods
    """

    def discover_all(self) -> List[Tool]:
        """PUBLIC: Part of ToolRegistry protocol"""
        tools = []
        tools.extend(self._discover_custom_tools())
        tools.extend(self._discover_global_tools())
        tools.extend(self._discover_mcp_tools())
        return tools

    # ✅ PRIVATE - can refactor without affecting callers
    def _discover_custom_tools(self) -> List[Tool]:
        """PRIVATE: Load tools from agent folders"""
        pass

    def _discover_global_tools(self) -> List[Tool]:
        """PRIVATE: Load tools from config/tools.json"""
        pass

    def _discover_mcp_tools(self) -> List[Tool]:
        """PRIVATE: Load tools from MCP servers"""
        pass
```

---

## 📋 STEP 6: Frontend API Client

### **Before: Direct fetch() calls**

```typescript
// ❌ Scattered throughout components
await fetch('/api/groups/' + groupId + '/messages')
await fetch('/api/groups', {method: 'POST', ...})
await fetch('/api/agents')
```

### **After: Unified API client**

```typescript
// File: frontend/src/api/client.ts

/**
 * AgentVerse API Client
 *
 * PUBLIC CONTRACT:
 * - All API methods are clearly defined
 * - Returns typed responses
 * - Handles errors consistently
 *
 * BLACK BOX:
 * - Components don't know about fetch()
 * - Components don't know about URL structure
 * - Components don't know about error handling
 */

export interface Message {
  id: number;
  sender: string;
  content: string;
  timestamp: number;
}

export interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
}

class AgentVerseClient {
  private baseURL = '/api';

  // ============================================================================
  // PUBLIC CONTRACT: Messages
  // ============================================================================
  async getMessages(groupId: string): Promise<Message[]> {
    return this._fetch<Message[]>(`/groups/${groupId}/messages`);
  }

  async sendMessage(groupId: string, agentId: string, content: string): Promise<void> {
    await this._fetch('/groups/' + groupId + '/messages', {
      method: 'POST',
      body: JSON.stringify({ agent_id: agentId, message: content })
    });
  }

  // ============================================================================
  // PUBLIC CONTRACT: Agents
  // ============================================================================
  async getAgents(): Promise<Agent[]> {
    return this._fetch<Agent[]>('/agents');
  }

  async getAgent(agentId: string): Promise<Agent> {
    return this._fetch<Agent>(`/agents/${agentId}`);
  }

  // ============================================================================
  // PRIVATE: Implementation details
  // ============================================================================
  private async _fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(this.baseURL + path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton
export const apiClient = new AgentVerseClient();
```

**Usage in components:**

```typescript
// ✅ Components only use public contract
import { apiClient } from '@/api/client';

function ConversationView({ groupId }: Props) {
  useEffect(() => {
    // ✅ Simple, typed, no fetch() details
    apiClient.getMessages(groupId).then(setMessages);
  }, [groupId]);

  const handleSend = async (message: string) => {
    // ✅ Clear API
    await apiClient.sendMessage(groupId, agentId, message);
  };
}
```

---

## 🎯 FINAL ARCHITECTURE

### **Dependency Graph (After Refactoring):**

```
┌─────────────────────────────────────────────────────┐
│         src/core/contracts/                          │
│  (PUBLIC INTERFACES - All modules depend on this)    │
│  - agents.py (Agent, AgentRegistry)                  │
│  - tools.py (Tool, ToolRegistry)                     │
│  - storage.py (ConversationStore, VectorStore)       │
│  - events.py (Event, EventBus)                       │
└─────────────────────────────────────────────────────┘
                        ▲
                        │ depends on
                        │
┌───────────────────────┴─────────────────────────────┐
│         src/core/di_container.py                     │
│  (Wires up all dependencies)                         │
└─────────────────────────────────────────────────────┘
        ▲               ▲               ▲
        │               │               │
        │               │               │
┌───────┴────┐  ┌──────┴─────┐  ┌─────┴──────┐
│  Agents    │  │   Tools     │  │  Storage   │
│  (impl)    │  │   (impl)    │  │  (impl)    │
└────────────┘  └────────────┘  └────────────┘
     ▲                                  ▲
     │                                  │
     │                                  │
┌────┴──────────────────────────────────┴─────┐
│         OrchestratorService                  │
│  (Uses all via contracts)                    │
└──────────────────────────────────────────────┘
                        ▲
                        │
                        │
┌───────────────────────┴──────────────────────┐
│         API Endpoints (chat.py, etc.)        │
│  (Uses service via contract)                 │
└──────────────────────────────────────────────┘
```

**✅ Benefits:**
1. **Black Box:** Each module only knows public contracts
2. **Limited Contracts:** Each interface has 3-5 methods max
3. **Testable:** Can inject mocks for testing
4. **Maintainable:** Change implementation without affecting callers
5. **Clear Ownership:** Each file has single responsibility

---

## 📊 BEFORE vs AFTER Comparison

### **Changing Tool Loading Mechanism:**

**BEFORE (touches 4 files):**
```
1. registry.py → Update _import_tools_py()
2. base_agent.py → Update register_tools_from_module()
3. langchain_tool_wrapper.py → Update _wrap_custom_tool()
4. tool_validator.py → Update validation logic
```

**AFTER (touches 1 file):**
```
1. tools/registry_impl.py → Update _discover_custom_tools()
   (Public contract unchanged, callers unaffected)
```

---

## 🚀 IMPLEMENTATION TIMELINE

### **Phase 1: Define Contracts (Week 1-2)**
- Create `src/core/contracts/` directory
- Define all Protocol classes
- Document public APIs

### **Phase 2: Create DI Container (Week 3)**
- Implement container
- Wire up existing implementations

### **Phase 3: Refactor Core (Week 4-8)**
- Refactor agents to use DI
- Consolidate tool registry
- Consolidate event emission
- Update storage to implement contracts

### **Phase 4: Refactor Frontend (Week 9-10)**
- Create API client
- Update all components
- Remove direct fetch() calls

### **Phase 5: Testing & Documentation (Week 11-12)**
- Add contract tests
- Update documentation
- Remove old code

---

**Total: 12 weeks to full black box architecture**

This is **significant work** but will make the codebase **dramatically more maintainable**.
