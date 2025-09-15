"""
Group API Models
Pydantic models for group-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional


class CreateGroupRequest(BaseModel):
    """Request model for creating a new group"""
    name: str = Field(..., min_length=1, max_length=100, description="Group name")


class GroupResponse(BaseModel):
    """Response model for group information"""
    id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group display name")
    created_at: float = Field(..., description="Creation timestamp")
    updated_at: float = Field(..., description="Last update timestamp")


class AddAgentRequest(BaseModel):
    """Request model for adding an agent to a group"""
    agent_key: str = Field(..., description="Agent identifier key")