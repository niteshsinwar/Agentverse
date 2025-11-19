"""
Orchestrator Service
Business logic layer for agent orchestration and management
"""

from typing import Dict, List, Optional, Any, Set
import asyncio
import os
import time

from src.core.agents.agent_coordinator import AgentOrchestrator
from src.core.agents.router import Router
from src.core.agents.registry import AgentSpec
from src.core.memory import session_store
from src.core.config.settings import get_settings


class OrchestratorService:
    """
    High-level service for managing agents and orchestration.

    This service provides:
    - Agent lifecycle management
    - Business logic for agent operations
    - Clean interface between API and core logic
    - Error handling and validation
    """

    def __init__(self):
        self.settings = get_settings()
        self.orchestrator: Optional[AgentOrchestrator] = None
        self.router: Optional[Router] = None
        self._initialized = False
        self._stopped_groups: Set[str] = set()  # Track stopped group chains

    async def initialize(self) -> None:
        """Initialize the orchestrator service"""
        if self._initialized:
            return

        try:
            print("🔧 OrchestratorService: Initializing...")

            # Initialize core orchestrator
            self.orchestrator = AgentOrchestrator()
            self.router = Router(self)

            # Load cloud agents if cloud mode is enabled
            if self.settings.cloud_enabled:
                await self.orchestrator._load_cloud_agents()

            # Verify agents are loaded directly from orchestrator
            agents = self.orchestrator.list_available_agents()
            print(f"✅ OrchestratorService: Loaded {len(agents)} agents")

            # Initialize session store
            await asyncio.sleep(0.1)  # Allow for any async initialization
            session_store.list_groups()  # Touch the database

            self._initialized = True

        except Exception as e:
            print(f"❌ OrchestratorService: Initialization failed: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources"""
        self._initialized = False

    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self._initialized and self.orchestrator is not None

    # Agent Management Methods
    def list_available_agents(self) -> Dict[str, AgentSpec]:
        """List all available agents"""
        if not self.is_ready():
            raise RuntimeError("Service not initialized")
        return self.orchestrator.list_available_agents()

    async def get_agent(self, agent_key: str):
        """Get a specific agent instance"""
        if not self.is_ready():
            raise RuntimeError("Service not initialized")
        return await self.orchestrator.get_agent(agent_key)

    def refresh_agents(self) -> None:
        """Refresh agent discovery (after creating new agents)"""
        if not self.is_ready():
            raise RuntimeError("Service not initialized")
        self.orchestrator.refresh_agents()

    # Hot-reload methods for configuration changes
    def reload_settings(self) -> None:
        """Reload settings.json without server restart"""
        print("🔄 Reloading settings.json...")
        try:
            # Force reload of settings singleton
            from src.core.config.settings import reload_settings
            reload_settings()
            self.settings = get_settings()

            # Reload singleton services that cache settings
            try:
                from src.core.document_processing.embedder import reload_embedder_settings
                reload_embedder_settings()
                print("  ✅ Embedding and vision clients reloaded")
            except Exception as embedder_error:
                print(f"  ⚠️ Failed to reload embedder clients: {embedder_error}")

            # Note: RAG service now uses @property for settings (supports hot-reload)
            # Some services (like summarizer, vector_store) cache config in __init__
            # These will pick up changes gradually or need full server restart for complete reload
            print("  ⚙️ Settings cache cleared")
            print("  ✅ Most settings will take effect immediately")
            print("  ⚠️ Some changes (embedding model, vector store config) may require server restart")
            print("✅ Settings reloaded successfully")
        except Exception as e:
            print(f"❌ Failed to reload settings: {e}")

    def reload_tools(self) -> None:
        """Reload tools.json without server restart"""
        print("🔄 Reloading tools.json...")
        try:
            # Tools are loaded on-demand from filesystem, no caching
            # Just notify that tools have changed
            print("✅ Tools configuration updated (loaded on-demand)")
        except Exception as e:
            print(f"❌ Failed to reload tools: {e}")

    def reload_mcp(self) -> None:
        """Reload mcp.json without server restart"""
        print("🔄 Reloading mcp.json...")
        try:
            # MCP servers are loaded on-demand from filesystem
            # Just notify that MCP configuration has changed
            print("✅ MCP configuration updated (loaded on-demand)")
        except Exception as e:
            print(f"❌ Failed to reload MCP: {e}")

    # Message Processing Methods
    async def process_message(self, group_id: str, message: str, sender: str = "user") -> None:
        """Process a message through the unified router (user or agent)"""
        if not self.is_ready():
            raise RuntimeError("Service not initialized")

        try:
            await self.router.route_message(group_id, message, sender)
        except Exception as e:
            # Log error and store error message
            error_msg = f"Error processing message: {str(e)}"
            print(f"❌ Service error processing message: {e}")

            session_store.append_message(
                group_id=group_id,
                sender="system",
                role="system",
                content=error_msg,
                metadata={
                    "error_type": "message_processing",
                    "original_message": message
                }
            )
            raise

    async def process_agent_message(self, group_id: str, agent_id: str, message: str) -> Dict[str, Any]:
        """Process a message with a specific agent"""
        if not self.is_ready():
            raise RuntimeError("Service not initialized")

        return await self.orchestrator.process_user_message(group_id, agent_id, message)

    # Group Management Methods
    def create_group(self, name: str) -> str:
        """Create a new group"""
        return session_store.create_group(name)

    def list_groups(self) -> List[Dict[str, Any]]:
        """List all groups"""
        return session_store.list_groups()

    def delete_group(self, group_id: str) -> None:
        """Delete a group"""
        session_store.delete_group(group_id)

    def add_agent_to_group(self, group_id: str, agent_key: str) -> None:
        """Add an agent to a group"""
        # Validate agent exists
        agents = self.list_available_agents()
        if agent_key not in agents:
            raise ValueError(f"Agent {agent_key} not found")

        session_store.add_agent_to_group(group_id, agent_key)

    def remove_agent_from_group(self, group_id: str, agent_key: str) -> None:
        """Remove an agent from a group"""
        session_store.remove_agent_from_group(group_id, agent_key)

    def list_group_agents(self, group_id: str) -> List[str]:
        """List agents in a group"""
        return session_store.list_group_agents(group_id)

    # Message History Methods
    def get_group_messages(self, group_id: str) -> List[Dict[str, Any]]:
        """Get message history for a group"""
        return session_store.get_history(group_id)

    def get_group_documents(self, group_id: str) -> List[Dict[str, Any]]:
        """Get documents for a group"""
        return session_store.get_group_documents(group_id)

    async def process_document_upload(self, group_id: str, agent_id: str, file, message: str) -> Dict[str, Any]:
        """
        Process document upload through MM-RAG pipeline

        Flow:
        1. Read file content
        2. Process through document_service (Extract → Chunk → Embed → Store)
        3. Store metadata in SQLite
        4. Route user message to agent (with RAG retrieval)
        """
        if not self.is_ready():
            raise RuntimeError("Orchestrator service not initialized")

        try:
            from src.services.document_service import document_service
            from src.core.telemetry.events import emit_message

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            print(f"📄 Processing document: {file.filename} ({file_size} bytes)")
            print(f"   Target: @{agent_id} in group {group_id}")

            # Process through MM-RAG pipeline (notification sent inside pipeline at start)
            print(f"🔄 Starting MM-RAG pipeline...")
            result = await document_service.process_upload(
                file_content=file_content,
                filename=file.filename,
                group_id=group_id,
                agent_id=agent_id
            )

            if not result['success']:
                print(f"❌ MM-RAG pipeline failed: {result['error']}")
                raise RuntimeError(result['error'])

            print(f"✅ MM-RAG pipeline complete:")
            print(f"   • Document ID: {result['document_id']}")
            print(f"   • Modality: {result['modality']}")
            print(f"   • Total chunks: {result['total_chunks']}")
            print(f"   • Chunks stored in ChromaDB vector store")

            # Step 2: Route user's message to agent (router will retrieve RAG context and emit SSE)
            user_message_content = f"@{agent_id} {message}" if message else f"@{agent_id}"
            await self.router.route_message(
                group_id=group_id,
                message=user_message_content,
                mentioner="user"
            )

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to process document upload: {str(e)}")

    # Group Chain Control Methods
    async def stop_group_chain(self, group_id: str) -> None:
        """Stop agent chain for a specific group"""
        self._stopped_groups.add(group_id)

        # Add system message to inform user
        stop_message = "🛑 Agent chain paused by user. Send another message to resume agent responses."
        session_store.append_message(
            group_id=group_id,
            sender="system",
            role="system",
            content=stop_message,
            metadata={
                "message_type": "chain_stopped",
                "stopped_at": time.time()
            }
        )

        # Emit the system message via SSE for real-time UI update
        from src.core.telemetry.events import emit_message
        await emit_message(group_id, sender="system", role="system", content=stop_message)

        print(f"🛑 Group {group_id} chain paused")

    def is_group_chain_active(self, group_id: str) -> bool:
        """Check if group chain is active (not stopped)"""
        return group_id not in self._stopped_groups

    def restart_group_chain(self, group_id: str) -> None:
        """Restart agent chain for a specific group"""
        if group_id in self._stopped_groups:
            self._stopped_groups.remove(group_id)
            print(f"✅ Group {group_id} chain restarted")

    # Service Status Methods
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        agents = self.list_available_agents() if self.is_ready() else {}
        api_keys = self.settings.validate_api_keys()

        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "agents_count": len(agents),
            "agents_list": list(agents.keys()) if agents else [],
            "api_keys_configured": api_keys,
            "settings": {
                "environment": self.settings.environment.value,
                "debug": self.settings.debug,
                "max_iterations": self.settings.max_agent_iterations
            }
        }
