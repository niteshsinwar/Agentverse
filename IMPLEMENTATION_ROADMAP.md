# AgentVerse Implementation Roadmap
## Based on Architecture Review Feedback (2025-11-19)

---

## 🎯 **SCOPE & PRIORITIES**

### **Confirmed YES (Implement):**
- ✅ Protocol/Interface classes for core components
- ✅ Dependency injection container
- ✅ Consolidated tool registry (isolated/agent-bundled/linked)
- ✅ Split god objects into focused services
- ✅ Explicit public contracts with documentation
- ✅ Dependency validation for custom tools
- ✅ Standardized tool loading (3 types)
- ✅ AgentFactory pattern
- ✅ Consolidated EventBus
- ✅ Simplified message pipeline
- ✅ Centralized session_store access
- ✅ Frontend API client
- ✅ TypeScript interfaces
- ✅ Centralized error handling
- ✅ Loading states (if standard practice)
- ✅ Unified configuration manager
- ✅ Hot-reloadable configs
- ✅ Config validation
- ✅ Standardized error codes
- ✅ User-friendly dependency errors
- ✅ MCP timeout feedback
- ✅ Retry logic with backoff
- ✅ Contract tests
- ✅ Public API documentation
- ✅ Integration tests
- ✅ DI for testability
- ✅ Remove duplicate code
- ✅ Extract magic numbers/strings
- ✅ Add type hints everywhere
- ✅ Remove dead code
- ✅ Input validation
- ✅ Rate limiting
- ✅ Security headers
- ✅ Tool code security validation
- ✅ Caching for expensive operations
- ✅ Database optimization
- ✅ Pagination
- ✅ Connection pooling

### **SKIP (Not Now):**
- ❌ API request/response validation endpoints (unnecessary for now)

### **KEEP AS-IS:**
- 🔒 LangChain framework (standard, don't abstract)

### **SPECIAL CONSIDERATIONS:**
1. **Code vs Data:** Only refactor `backend/src/`, treat `agent_store/`, `config/`, `logs/` as data
2. **Tool Types:** Support isolated/agent-bundled/linked tool files
3. **Future WebSocket:** Design for WebSocket migration path

---

## 📅 **PHASE 1: CORE ARCHITECTURE (Week 1-4)**

### **Week 1: Contracts & Protocols**

#### **Milestone 1.1: Define Core Protocols**
**Files to create:**
```
backend/src/core/contracts/
├── __init__.py
├── agents.py          # Agent, AgentRegistry protocols
├── tools.py           # Tool, ToolRegistry protocols
├── storage.py         # ConversationStore, VectorStore protocols
├── events.py          # Event, EventBus protocols
├── config.py          # ConfigManager protocol
└── llm.py            # LLM protocol
```

**Implementation:**

**File: `backend/src/core/contracts/agents.py`**
```python
"""
Agent System Contracts
PUBLIC CONTRACTS - Never change without version bump
"""
from typing import Protocol, Dict, Any, List
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentSpec:
    """Immutable agent specification - PUBLIC DATA"""
    key: str
    name: str
    description: str
    emoji: str
    llm_provider: str
    llm_model: str
    folder_path: str

class Agent(Protocol):
    """PUBLIC CONTRACT: All agents must implement this"""

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
        Main entry point for agent response.

        Returns:
            {"text": str, "agent_id": str, "group_id": str}
        """
        ...

    def get_capabilities_summary(self) -> str:
        """Human-readable capabilities description"""
        ...

class AgentRegistry(Protocol):
    """PUBLIC CONTRACT: Agent discovery and creation"""

    def list_available(self) -> Dict[str, AgentSpec]:
        """List all available agent specifications"""
        ...

    async def get_agent(self, agent_id: str) -> Agent:
        """Get or create agent instance"""
        ...

    def refresh(self) -> None:
        """Refresh agent discovery from data sources"""
        ...
```

**File: `backend/src/core/contracts/tools.py`**
```python
"""
Tool System Contracts
Supports: isolated tools, agent-bundled tools, linked tools
"""
from typing import Protocol, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ToolSource(Enum):
    """Tool source types"""
    ISOLATED = "isolated"      # Standalone tool file
    AGENT_BUNDLED = "agent"    # In agent_store/agent/tools.py
    LINKED = "linked"          # Isolated tool linked to agent
    MCP = "mcp"                # MCP server tool

@dataclass(frozen=True)
class ToolDefinition:
    """PUBLIC DATA: Tool metadata"""
    name: str
    description: str
    source: ToolSource
    file_path: Optional[str]   # For file-based tools
    server_name: Optional[str]  # For MCP tools
    dependencies: List[str]     # Required Python packages

class Tool(Protocol):
    """PUBLIC CONTRACT: All tools implement this"""

    @property
    def name(self) -> str:
        """Tool name"""
        ...

    @property
    def description(self) -> str:
        """Tool description"""
        ...

    @property
    def parameters(self) -> Dict[str, Any]:
        """Tool parameter schema"""
        ...

    async def execute(self, **kwargs) -> Any:
        """Execute tool with parameters"""
        ...

class ToolRegistry(Protocol):
    """PUBLIC CONTRACT: Tool discovery and management"""

    def discover_all(self) -> List[Tool]:
        """Discover all available tools from all sources"""
        ...

    def discover_for_agent(self, agent_id: str) -> List[Tool]:
        """Discover tools for specific agent (bundled + linked)"""
        ...

    def discover_isolated(self) -> List[Tool]:
        """Discover standalone tool files"""
        ...

    def link_tool_to_agent(self, tool_id: str, agent_id: str) -> None:
        """Link isolated tool to agent"""
        ...

    def validate_dependencies(self, tool: Tool) -> List[str]:
        """
        Check tool dependencies.

        Returns:
            List of missing packages (empty if all satisfied)
        """
        ...
```

**File: `backend/src/core/contracts/events.py`**
```python
"""
Event System Contracts
Design for SSE now, WebSocket migration later
"""
from typing import Protocol, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class EventType(Enum):
    """Standard event types"""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    AGENT_THOUGHT = "agent_thought"
    MCP_CALL = "mcp_call"
    MCP_RESULT = "mcp_result"
    ERROR = "error"
    SUMMARIZATION = "summarization"

@dataclass(frozen=True)
class Event:
    """PUBLIC DATA: Standard event structure"""
    type: EventType
    group_id: str
    agent_id: str
    payload: Dict[str, Any]
    timestamp: datetime

class EventBus(Protocol):
    """
    PUBLIC CONTRACT: Event emission and subscription

    DESIGN NOTE: Built for SSE, will support WebSocket migration:
    - emit() works for both SSE and WebSocket
    - subscribe() for in-process listeners
    - Future: add broadcast() for WebSocket rooms
    """

    async def emit(self, event: Event) -> None:
        """
        Emit event to all subscribers.
        Works for SSE now, WebSocket later.
        """
        ...

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ) -> str:
        """
        Subscribe to event type.

        Returns:
            Subscription ID (for unsubscribe)
        """
        ...

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events"""
        ...
```

**File: `backend/src/core/contracts/storage.py`**
```python
"""Storage Contracts"""
from typing import Protocol, List, Dict, Any, Optional

class ConversationStore(Protocol):
    """PUBLIC CONTRACT: Conversation persistence"""

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

class VectorStore(Protocol):
    """PUBLIC CONTRACT: Vector storage for RAG"""

    async def store_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """Store document chunks with embeddings"""
        ...

    async def search(
        self,
        query: str,
        group_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        ...
```

**File: `backend/src/core/contracts/config.py`**
```python
"""Configuration Contracts"""
from typing import Protocol, Any, Dict

class ConfigManager(Protocol):
    """
    PUBLIC CONTRACT: Unified configuration management

    Data sources (outside backend/src/):
    - config/settings.json
    - config/tools.json
    - config/mcp.json
    - agent_store/*/agent.yaml
    - agent_store/*/mcp.json
    """

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        ...

    def reload(self, source: str) -> None:
        """
        Hot-reload configuration source.

        Args:
            source: 'settings' | 'tools' | 'mcp' | 'agents'
        """
        ...

    def validate(self) -> Dict[str, Any]:
        """
        Validate all configurations.

        Returns:
            {"valid": bool, "errors": [...], "warnings": [...]}
        """
        ...
```

**Deliverable:** All protocol files created with clear contracts

---

#### **Milestone 1.2: Dependency Injection Container**

**File: `backend/src/core/di_container.py`**
```python
"""
Dependency Injection Container
Wires up all dependencies, treats data sources as external
"""
from typing import Dict, Any, Optional
from src.core.contracts.agents import AgentRegistry
from src.core.contracts.tools import ToolRegistry
from src.core.contracts.storage import ConversationStore, VectorStore
from src.core.contracts.events import EventBus
from src.core.contracts.config import ConfigManager

class Container:
    """
    Dependency injection container.

    PRINCIPLE: Modules NEVER import concrete implementations.
    All dependencies come from here.

    DATA SOURCES (outside src/):
    - agent_store/ → AgentRegistry reads
    - config/ → ConfigManager reads
    - logs/ → Written by services
    """

    def __init__(self):
        self._singletons: Dict[str, Any] = {}
        self._data_root = "."  # Project root for data access

    # ===================================================================
    # PUBLIC: Get service instances
    # ===================================================================

    def get_config_manager(self) -> ConfigManager:
        """Get configuration manager (reads config/, agent_store/)"""
        if 'config_manager' not in self._singletons:
            from src.core.config.manager_impl import ConfigManagerImpl
            self._singletons['config_manager'] = ConfigManagerImpl(
                data_root=self._data_root
            )
        return self._singletons['config_manager']

    def get_conversation_store(self) -> ConversationStore:
        """Get conversation store"""
        if 'conversation_store' not in self._singletons:
            from src.core.storage.session_store_impl import SessionStoreImpl
            self._singletons['conversation_store'] = SessionStoreImpl(
                config=self.get_config_manager()
            )
        return self._singletons['conversation_store']

    def get_event_bus(self) -> EventBus:
        """Get event bus (SSE now, WebSocket-ready)"""
        if 'event_bus' not in self._singletons:
            from src.core.events.event_bus_impl import EventBusImpl
            self._singletons['event_bus'] = EventBusImpl()
        return self._singletons['event_bus']

    def get_tool_registry(self) -> ToolRegistry:
        """Get tool registry (reads config/tools.json, agent_store/)"""
        if 'tool_registry' not in self._singletons:
            from src.core.tools.registry_impl import ToolRegistryImpl
            self._singletons['tool_registry'] = ToolRegistryImpl(
                config=self.get_config_manager(),
                data_root=self._data_root
            )
        return self._singletons['tool_registry']

    def get_agent_registry(self) -> AgentRegistry:
        """Get agent registry (reads agent_store/)"""
        if 'agent_registry' not in self._singletons:
            from src.core.agents.registry_impl import AgentRegistryImpl
            self._singletons['agent_registry'] = AgentRegistryImpl(
                config=self.get_config_manager(),
                tool_registry=self.get_tool_registry(),
                event_bus=self.get_event_bus(),
                conversation_store=self.get_conversation_store(),
                data_root=self._data_root
            )
        return self._singletons['agent_registry']

    # ===================================================================
    # TESTING: Injectable mocks
    # ===================================================================

    def register_singleton(self, key: str, instance: Any) -> None:
        """Register singleton (for testing with mocks)"""
        self._singletons[key] = instance

    def clear(self) -> None:
        """Clear all singletons (for testing)"""
        self._singletons.clear()

# Global container instance
container = Container()
```

**Deliverable:** DI container with all core services

---

### **Week 2: Tool Registry Implementation**

#### **Milestone 2.1: Unified Tool Registry**

**File: `backend/src/core/tools/registry_impl.py`**
```python
"""
Unified Tool Registry Implementation
Handles: isolated tools, agent-bundled tools, linked tools, MCP tools
"""
from typing import List, Dict, Any, Set
import os
import json
import importlib.util
from pathlib import Path

from src.core.contracts.tools import (
    Tool, ToolRegistry, ToolDefinition, ToolSource
)
from src.core.contracts.config import ConfigManager

class ToolRegistryImpl:
    """
    Implementation of ToolRegistry contract.

    Tool Discovery Strategy:
    1. Isolated tools: Scan configured tool directories
    2. Agent-bundled: Scan agent_store/*/tools.py
    3. Linked: Read from config (which isolated→agent mappings)
    4. MCP: Discover from MCP servers

    PUBLIC (from protocol):
    - discover_all()
    - discover_for_agent()
    - discover_isolated()
    - link_tool_to_agent()
    - validate_dependencies()

    PRIVATE:
    - All other methods
    """

    def __init__(
        self,
        config: ConfigManager,
        data_root: str = "."
    ):
        self._config = config
        self._data_root = Path(data_root)
        self._tool_cache: Dict[str, Tool] = {}
        self._linked_tools: Dict[str, Set[str]] = {}  # agent_id → tool_ids

        # Load linked tools from config
        self._load_tool_links()

    # ===================================================================
    # PUBLIC CONTRACT IMPLEMENTATION
    # ===================================================================

    def discover_all(self) -> List[Tool]:
        """Discover all tools from all sources"""
        tools = []
        tools.extend(self._discover_isolated_tools())
        tools.extend(self._discover_agent_bundled_tools())
        tools.extend(self._discover_mcp_tools())
        return tools

    def discover_for_agent(self, agent_id: str) -> List[Tool]:
        """Discover tools for specific agent"""
        tools = []

        # 1. Agent-bundled tools (agent_store/agent_id/tools.py)
        tools.extend(self._discover_agent_bundled_tools(agent_id))

        # 2. Linked isolated tools
        if agent_id in self._linked_tools:
            for tool_id in self._linked_tools[agent_id]:
                tool = self._get_isolated_tool(tool_id)
                if tool:
                    tools.append(tool)

        # 3. Agent's MCP tools (agent_store/agent_id/mcp.json)
        tools.extend(self._discover_agent_mcp_tools(agent_id))

        return tools

    def discover_isolated(self) -> List[Tool]:
        """Discover standalone tool files"""
        return self._discover_isolated_tools()

    def link_tool_to_agent(self, tool_id: str, agent_id: str) -> None:
        """Link isolated tool to agent"""
        if agent_id not in self._linked_tools:
            self._linked_tools[agent_id] = set()
        self._linked_tools[agent_id].add(tool_id)

        # Persist to config
        self._save_tool_links()

    def validate_dependencies(self, tool: Tool) -> List[str]:
        """
        Check if tool dependencies are installed.

        Returns:
            List of missing package names
        """
        # Get tool definition from metadata
        tool_def = self._get_tool_definition(tool)
        if not tool_def or not tool_def.dependencies:
            return []

        missing = []
        for package in tool_def.dependencies:
            # Parse package name (handle "package>=1.0.0" format)
            pkg_name = package.split('>=')[0].split('==')[0].split('<')[0].strip()

            # Check if importable
            if importlib.util.find_spec(pkg_name) is None:
                missing.append(package)

        return missing

    # ===================================================================
    # PRIVATE: Discovery implementations
    # ===================================================================

    def _discover_isolated_tools(self) -> List[Tool]:
        """
        Discover tools from configured isolated tool directories.

        Data source: config/tools.json → {"tools_directories": ["path/to/tools"]}
        """
        tools = []

        # Get directories from config
        tool_dirs = self._config.get('tools_directories', [])

        for tool_dir in tool_dirs:
            tools_path = self._data_root / tool_dir
            if not tools_path.exists():
                continue

            # Scan for .py files
            for tool_file in tools_path.glob("*.py"):
                if tool_file.name.startswith("__"):
                    continue

                tools.extend(self._load_tools_from_file(
                    tool_file,
                    ToolSource.ISOLATED
                ))

        return tools

    def _discover_agent_bundled_tools(
        self,
        agent_id: Optional[str] = None
    ) -> List[Tool]:
        """
        Discover tools bundled with agents.

        Data source: agent_store/*/tools.py
        """
        tools = []
        agent_store = self._data_root / "agent_store"

        if not agent_store.exists():
            return tools

        # If specific agent, only load that agent's tools
        if agent_id:
            agent_dir = agent_store / agent_id
            tools_file = agent_dir / "tools.py"
            if tools_file.exists():
                tools.extend(self._load_tools_from_file(
                    tools_file,
                    ToolSource.AGENT_BUNDLED,
                    agent_id=agent_id
                ))
        else:
            # Load all agents' tools
            for agent_dir in agent_store.iterdir():
                if not agent_dir.is_dir():
                    continue
                if agent_dir.name.startswith("__"):
                    continue

                tools_file = agent_dir / "tools.py"
                if tools_file.exists():
                    tools.extend(self._load_tools_from_file(
                        tools_file,
                        ToolSource.AGENT_BUNDLED,
                        agent_id=agent_dir.name
                    ))

        return tools

    def _discover_mcp_tools(self) -> List[Tool]:
        """
        Discover tools from global MCP servers.

        Data source: config/mcp.json
        """
        # Delegate to MCP manager
        # This will be implemented when refactoring MCP integration
        return []

    def _discover_agent_mcp_tools(self, agent_id: str) -> List[Tool]:
        """
        Discover MCP tools for specific agent.

        Data source: agent_store/{agent_id}/mcp.json
        """
        # Delegate to MCP manager
        return []

    def _load_tools_from_file(
        self,
        file_path: Path,
        source: ToolSource,
        agent_id: Optional[str] = None
    ) -> List[Tool]:
        """
        Load tools from Python file.

        Looks for functions with @agent_tool decorator.
        """
        tools = []

        try:
            # Import module
            module_name = f"tool_module_{file_path.stem}_{id(file_path)}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return tools

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find @agent_tool decorated functions
            import inspect
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if getattr(obj, "__agent_tool__", False):
                    # Wrap in Tool implementation
                    tool = self._create_tool_from_function(
                        obj, source, str(file_path), agent_id
                    )
                    tools.append(tool)

        except Exception as e:
            print(f"Error loading tools from {file_path}: {e}")

        return tools

    def _create_tool_from_function(
        self,
        func: Callable,
        source: ToolSource,
        file_path: str,
        agent_id: Optional[str]
    ) -> Tool:
        """Create Tool implementation from function"""
        # Implementation here - wraps function as Tool
        # This will use existing langchain_tool_wrapper logic
        pass

    # ===================================================================
    # PRIVATE: Tool linking persistence
    # ===================================================================

    def _load_tool_links(self) -> None:
        """Load tool→agent links from config"""
        links = self._config.get('tool_links', {})
        for agent_id, tool_ids in links.items():
            self._linked_tools[agent_id] = set(tool_ids)

    def _save_tool_links(self) -> None:
        """Save tool→agent links to config"""
        links = {
            agent_id: list(tool_ids)
            for agent_id, tool_ids in self._linked_tools.items()
        }
        # Save to config (ConfigManager will handle persistence)
        self._config.set('tool_links', links)
```

**Deliverable:** Unified tool registry handling all 3 tool types

---

#### **Milestone 2.2: Tool Dependency Validation**

**Enhancement to validation:**

**File: `backend/src/core/validation/tool_validator.py`** (UPDATE)
```python
# Add to existing ToolValidator class:

@staticmethod
def validate_dependencies(dependencies: List[str]) -> ValidationResult:
    """
    Validate tool dependencies are installed.

    Args:
        dependencies: List of package specs (e.g., ["numpy>=1.24.0", "requests"])

    Returns:
        ValidationResult with missing dependencies
    """
    result = ValidationResult(valid=True, errors=[], warnings=[])

    import importlib.util

    for dep_spec in dependencies:
        # Parse package name
        pkg_name = dep_spec.split('>=')[0].split('==')[0].split('<')[0].strip()

        # Check if importable
        if importlib.util.find_spec(pkg_name) is None:
            result.add_error(
                "dependencies",
                f"Required package '{dep_spec}' not installed",
                "MISSING_DEPENDENCY",
                {
                    "package": dep_spec,
                    "install_command": f"pip install {dep_spec}"
                }
            )

    return result
```

**Deliverable:** Dependency validation with clear error messages

---

### **Week 3-4: Agent System Refactoring**

#### **Milestone 3.1: AgentFactory Pattern**

**File: `backend/src/core/agents/factory.py`** (NEW)
```python
"""
AgentFactory - Single source of truth for agent creation
Consolidates logic from registry.py, base_agent.py
"""
from typing import Dict, Any
from src.core.contracts.agents import Agent, AgentSpec
from src.core.contracts.tools import ToolRegistry
from src.core.contracts.storage import ConversationStore
from src.core.contracts.events import EventBus
from src.core.contracts.config import ConfigManager

class AgentFactory:
    """
    Factory for creating agents.

    PUBLIC:
    - build(spec: AgentSpec) -> Agent

    PRIVATE:
    - All other methods
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        conversation_store: ConversationStore,
        event_bus: EventBus,
        config: ConfigManager
    ):
        self._tool_registry = tool_registry
        self._conversation_store = conversation_store
        self._event_bus = event_bus
        self._config = config

    async def build(self, spec: AgentSpec) -> Agent:
        """
        Build agent from specification.

        This is the ONLY way to create agents.
        """
        # Import implementation (not in imports to avoid circular deps)
        from src.core.agents.base_agent import EnhancedBaseAgent

        # Create agent instance with injected dependencies
        agent = EnhancedBaseAgent(
            agent_id=spec.key,
            llm_config={"provider": spec.llm_provider, "model": spec.llm_model},
            conversation_store=self._conversation_store,
            event_bus=self._event_bus,
            config=self._config
        )

        # Load metadata
        agent.load_metadata(
            name=spec.name,
            description=spec.description,
            folder_path=spec.folder_path
        )

        # Load tools for this agent
        tools = self._tool_registry.discover_for_agent(spec.key)

        # Validate tool dependencies
        for tool in tools:
            missing = self._tool_registry.validate_dependencies(tool)
            if missing:
                raise ValueError(
                    f"Agent '{spec.key}' has tools with missing dependencies:\n" +
                    "\n".join(f"  - {pkg}" for pkg in missing) +
                    f"\n\nInstall with: pip install {' '.join(missing)}"
                )

        # Register tools with agent
        agent.register_tools(tools)

        return agent
```

**Deliverable:** Centralized agent creation with dependency validation

---

## 📅 **PHASE 2: SERVICE LAYER (Week 5-6)**

### **Week 5: Refactor God Objects**

#### **Split OrchestratorService:**

**BEFORE (single file doing everything):**
```
orchestrator_service.py (316 lines)
- Agent management
- Message processing
- Group management
- Document processing
- Configuration
- Status reporting
```

**AFTER (focused services):**
```
services/
├── agent_service.py        # Agent management only
├── message_service.py      # Message processing only
├── group_service.py        # Group management only
├── document_service.py     # Document processing only (already exists)
└── config_service.py       # Configuration management
```

---

## 📅 **PHASE 3: EVENT SYSTEM (Week 7-8)**

### **Consolidated EventBus**

**File: `backend/src/core/events/event_bus_impl.py`**
```python
"""
Unified EventBus Implementation
SSE now, WebSocket-ready for future
"""
from typing import Dict, List, Callable, Any
import asyncio
from collections import defaultdict

from src.core.contracts.events import EventBus, Event, EventType

class EventBusImpl:
    """
    EventBus implementation.

    DESIGN:
    - Current: SSE via drain() method
    - Future: WebSocket via broadcast() method (to be added)
    """

    def __init__(self):
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._subscription_ids: Dict[str, tuple] = {}

    async def emit(self, event: Event) -> None:
        """Emit event (SSE + in-process subscribers)"""
        # Add to queue for SSE consumers
        await self._event_queue.put(event)

        # Notify in-process subscribers
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"Event handler error: {e}")

    async def drain(self, limit: int = 50) -> List[Event]:
        """Drain events for SSE (current implementation)"""
        events = []
        try:
            for _ in range(limit):
                event = self._event_queue.get_nowait()
                events.append(event)
        except asyncio.QueueEmpty:
            pass
        return events

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any]
    ) -> str:
        """Subscribe to event type"""
        import uuid
        sub_id = str(uuid.uuid4())
        self._subscribers[event_type].append(handler)
        self._subscription_ids[sub_id] = (event_type, handler)
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events"""
        if subscription_id in self._subscription_ids:
            event_type, handler = self._subscription_ids[subscription_id]
            self._subscribers[event_type].remove(handler)
            del self._subscription_ids[subscription_id]
```

---

## 📅 **PHASE 4: FRONTEND (Week 9-10)**

### **API Client**

**File: `frontend/src/api/client.ts`**
```typescript
/**
 * AgentVerse API Client
 * Unified interface for all backend communication
 *
 * Design: REST now, WebSocket migration ready
 */

// Type definitions
export interface Message {
  id: number;
  sender: string;
  role: string;
  content: string;
  timestamp: number;
}

export interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
}

export interface Group {
  id: string;
  name: string;
  agents: string[];
}

class AgentVerseClient {
  private baseURL = '/api';

  // Message operations
  readonly messages = {
    list: async (groupId: string): Promise<Message[]> => {
      return this._fetch(`/groups/${groupId}/messages`);
    },

    send: async (groupId: string, agentId: string, content: string): Promise<void> => {
      await this._fetch(`/groups/${groupId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ agent_id: agentId, message: content })
      });
    }
  };

  // Agent operations
  readonly agents = {
    list: async (): Promise<Agent[]> => {
      return this._fetch('/agents');
    },

    get: async (agentId: string): Promise<Agent> => {
      return this._fetch(`/agents/${agentId}`);
    }
  };

  // Private fetch wrapper
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

export const apiClient = new AgentVerseClient();
```

---

## 📅 **REMAINING PHASES (Week 11-16)**

- **Week 11-12:** Testing (contract tests, integration tests)
- **Week 13-14:** Performance optimization (caching, connection pooling)
- **Week 15-16:** Documentation, cleanup, final review

---

## 🎯 **SUCCESS CRITERIA**

### **Architecture Quality:**
- ✅ All modules depend on contracts, not implementations
- ✅ Can swap BaseAgent/MCP/DocProcessing without breaking (1-3 files changed max)
- ✅ Tool system handles isolated/agent-bundled/linked cleanly
- ✅ Data (agent_store/, config/) separate from code (src/)
- ✅ All dependencies validated before agent creation

### **Code Quality:**
- ✅ Type hints on all functions
- ✅ Public contracts documented
- ✅ No duplicate code
- ✅ No dead code
- ✅ Magic numbers extracted to config

### **User Experience:**
- ✅ Clear error messages for missing dependencies
- ✅ Loading states for all async operations
- ✅ Timeout feedback for slow operations
- ✅ Real-time updates via events

### **Future-Ready:**
- ✅ WebSocket migration path clear
- ✅ Can add new tool types without refactoring
- ✅ Can swap LLM providers easily
- ✅ Can swap storage backends easily

---

## 📊 **PROGRESS TRACKING**

| Phase | Status | Completion | Notes |
|-------|--------|------------|-------|
| Phase 1: Contracts | 🟡 In Progress | 0% | Starting Week 1 |
| Phase 2: Services | ⚪ Not Started | 0% | Week 5-6 |
| Phase 3: Events | ⚪ Not Started | 0% | Week 7-8 |
| Phase 4: Frontend | ⚪ Not Started | 0% | Week 9-10 |
| Phase 5: Testing | ⚪ Not Started | 0% | Week 11-12 |
| Phase 6: Performance | ⚪ Not Started | 0% | Week 13-14 |
| Phase 7: Docs | ⚪ Not Started | 0% | Week 15-16 |

**Estimated Total Time:** 16 weeks (4 months)

---

## 🚀 **NEXT STEPS**

1. **Review this roadmap** - confirm approach
2. **Start Phase 1, Week 1** - create contract files
3. **Incremental implementation** - merge PRs after each milestone
4. **Continuous testing** - ensure no regressions

**Ready to start implementation?** Let me know and I'll begin with Phase 1, Week 1!
