"""
Agent Response Models
Simplified Pydantic models for structured agent outputs - only 3 action types
"""

from enum import Enum
from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    FINAL = "final"
    CALL_TOOL = "call_tool"
    CALL_MCP = "call_mcp"


class AgentResponse(BaseModel):
    """Base agent response model ensuring proper JSON structure"""
    action: ActionType = Field(..., description="The action type the agent wants to perform")


class FinalResponse(AgentResponse):
    """Final response with text content"""
    action: Literal[ActionType.FINAL] = ActionType.FINAL
    text: str = Field(..., description="The final response text with proper @mention")


class ToolCallResponse(AgentResponse):
    """Tool call response"""
    action: Literal[ActionType.CALL_TOOL] = ActionType.CALL_TOOL
    tool: str = Field(..., description="Tool name to call")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Tool inputs")


class MCPCallResponse(AgentResponse):
    """MCP call response"""
    action: Literal[ActionType.CALL_MCP] = ActionType.CALL_MCP
    server: str = Field(..., description="MCP server name")
    tool: str = Field(..., description="MCP tool name")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="MCP tool inputs", alias="params")

    class Config:
        populate_by_name = True  # Allow both 'inputs' and 'params'


def get_response_schema() -> str:
    """Get JSON schema for agent responses"""
    return """
You MUST respond with valid JSON matching one of these 3 schemas:

1. Final Response (most common):
{
  "action": "final",
  "text": "Your response here with proper @mention"
}

2. Tool Call:
{
  "action": "call_tool",
  "tool": "tool_name",
  "inputs": {"param": "value"}
}

3. MCP Call:
{
  "action": "call_mcp",
  "server": "server_name",
  "tool": "tool_name",
  "inputs": {"param": "value"}
}

IMPORTANT:
- Always include proper @mention in final responses!
- Use ONLY these 3 action types
- Return valid JSON only
"""


def parse_agent_response(raw_response: str) -> AgentResponse:
    """Parse and validate agent response with proper error handling"""
    import json
    from pydantic import ValidationError

    # Clean the response
    clean_response = raw_response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
    clean_response = clean_response.strip()

    try:
        # Parse JSON
        data = json.loads(clean_response)

        # Validate based on action type
        action = data.get("action")
        if action == "final":
            return FinalResponse(**data)
        elif action == "call_tool":
            return ToolCallResponse(**data)
        elif action == "call_mcp":
            return MCPCallResponse(**data)
        else:
            # Unknown action, treat as final response
            return FinalResponse(action="final", text=clean_response)

    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        # If parsing fails, treat entire response as final text
        print(f"⚠️ Agent response parsing failed: {e}")
        print(f"Raw response: {repr(raw_response)}")

        # Try to extract @mention if present
        import re
        mention_match = re.search(r'@\w+', clean_response)
        if mention_match:
            # Response contains mention, use as-is
            return FinalResponse(action="final", text=clean_response)
        else:
            # No mention found, this needs validation wall correction
            return FinalResponse(action="final", text=clean_response + " @user")
