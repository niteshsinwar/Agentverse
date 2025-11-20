"""
Execution Context - Track agent execution chain metadata

Tracks who initiated an execution chain, which device is running it,
and the full call stack for analytics and debugging.

Author: AgentVerse Team
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """
    Track execution chain context across agent calls.

    When User A @mentions Agent B, which then calls Agent C,
    this context tracks that User A initiated the chain on Device X.

    Attributes:
        execution_id: Unique ID for this execution chain
        initiator_user_id: User who started the chain (@mentioned first agent)
        initiator_device_id: Device running the execution
        group_id: Group where execution is happening
        tenant_id: Tenant context
        started_at: When execution chain started
        call_stack: Agent call chain (e.g., ["agent_A", "agent_B", "agent_C"])
        depth: Current depth in call chain
        metadata: Additional metadata

    Example:
        # User @john_doe mentions @agent_A in group-123
        ctx = ExecutionContext.create(
            initiator_user_id="user-uuid",
            initiator_device_id="device-uuid",
            group_id="group-123",
            tenant_id="tenant-uuid"
        )

        # Agent A calls Agent B
        ctx.push_agent("agent_A")
        ctx.push_agent("agent_B")

        # Full chain: john_doe -> agent_A -> agent_B
        print(ctx.call_stack)  # ["agent_A", "agent_B"]
        print(ctx.depth)  # 2
    """

    execution_id: str
    initiator_user_id: str
    initiator_device_id: str
    group_id: str
    tenant_id: str
    started_at: datetime
    call_stack: List[str] = field(default_factory=list)
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        initiator_user_id: str,
        initiator_device_id: str,
        group_id: str,
        tenant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ExecutionContext":
        """
        Create new execution context.

        Args:
            initiator_user_id: User who @mentioned the first agent
            initiator_device_id: Device running the execution
            group_id: Group ID
            tenant_id: Tenant ID
            metadata: Optional additional metadata

        Returns:
            New ExecutionContext instance

        Example:
            ctx = ExecutionContext.create(
                initiator_user_id="user-123",
                initiator_device_id="device-456",
                group_id="group-789",
                tenant_id="tenant-abc"
            )
        """
        return cls(
            execution_id=str(uuid.uuid4()),
            initiator_user_id=initiator_user_id,
            initiator_device_id=initiator_device_id,
            group_id=group_id,
            tenant_id=tenant_id,
            started_at=datetime.utcnow(),
            metadata=metadata or {}
        )

    def push_agent(self, agent_id: str):
        """
        Push agent to call stack (entering agent execution).

        Args:
            agent_id: Agent being called

        Example:
            ctx.push_agent("agent_A")
            ctx.push_agent("agent_B")
            # call_stack: ["agent_A", "agent_B"]
        """
        self.call_stack.append(agent_id)
        self.depth = len(self.call_stack)
        logger.debug(f"Execution {self.execution_id}: Pushed {agent_id} (depth={self.depth})")

    def pop_agent(self) -> Optional[str]:
        """
        Pop agent from call stack (exiting agent execution).

        Returns:
            Agent ID that was popped, or None if stack empty

        Example:
            ctx.push_agent("agent_A")
            ctx.push_agent("agent_B")
            agent = ctx.pop_agent()  # Returns "agent_B"
            # call_stack: ["agent_A"]
        """
        if self.call_stack:
            agent_id = self.call_stack.pop()
            self.depth = len(self.call_stack)
            logger.debug(f"Execution {self.execution_id}: Popped {agent_id} (depth={self.depth})")
            return agent_id
        return None

    def get_current_agent(self) -> Optional[str]:
        """
        Get currently executing agent (top of stack).

        Returns:
            Current agent ID or None if stack empty
        """
        return self.call_stack[-1] if self.call_stack else None

    def get_call_chain_str(self) -> str:
        """
        Get human-readable call chain string.

        Returns:
            Call chain as string (e.g., "user -> agent_A -> agent_B")

        Example:
            ctx.push_agent("agent_A")
            ctx.push_agent("agent_B")
            print(ctx.get_call_chain_str())
            # Output: "user -> agent_A -> agent_B"
        """
        chain = [f"user:{self.initiator_user_id[:8]}"] + self.call_stack
        return " -> ".join(chain)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation

        Example:
            ctx_dict = ctx.to_dict()
            # Can be sent in API request or saved to database
        """
        return {
            "execution_id": self.execution_id,
            "initiator_user_id": self.initiator_user_id,
            "initiator_device_id": self.initiator_device_id,
            "group_id": self.group_id,
            "tenant_id": self.tenant_id,
            "started_at": self.started_at.isoformat(),
            "call_stack": self.call_stack,
            "depth": self.depth,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """
        Create ExecutionContext from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ExecutionContext instance

        Example:
            ctx_dict = {...}  # From API response
            ctx = ExecutionContext.from_dict(ctx_dict)
        """
        return cls(
            execution_id=data["execution_id"],
            initiator_user_id=data["initiator_user_id"],
            initiator_device_id=data["initiator_device_id"],
            group_id=data["group_id"],
            tenant_id=data["tenant_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            call_stack=data.get("call_stack", []),
            depth=data.get("depth", 0),
            metadata=data.get("metadata", {})
        )

    def __str__(self) -> str:
        """String representation"""
        return f"ExecutionContext(id={self.execution_id[:8]}, chain={self.get_call_chain_str()})"

    def __repr__(self) -> str:
        """Repr representation"""
        return (
            f"ExecutionContext(execution_id={self.execution_id}, "
            f"initiator={self.initiator_user_id}, "
            f"device={self.initiator_device_id}, "
            f"depth={self.depth})"
        )
