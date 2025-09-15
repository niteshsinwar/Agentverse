"""
Chat API Models
Pydantic models for chat-related API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class SendMessageRequest(BaseModel):
    """Request model for sending a message"""
    agent_id: str = Field(..., description="Target agent identifier")
    message: str = Field(..., min_length=1, description="Message content")


class MessageResponse(BaseModel):
    """Response model for message information"""
    id: int = Field(..., description="Message sequence number")
    group_id: str = Field(..., description="Group identifier")
    sender: str = Field(..., description="Message sender")
    role: str = Field(..., description="Sender role (user/agent/system)")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: float = Field(..., description="Creation timestamp")