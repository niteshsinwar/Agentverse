"""
Validation API Endpoints
Handle configuration validation using the same logic as registry.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from src.core.validation.agent_validator import AgentValidator
from src.core.validation.tool_validator import ToolValidator
from src.core.validation.mcp_validator import McpValidator

router = APIRouter()


# Request models
class ToolRequest(BaseModel):
    name: str
    description: str
    category: str
    code: str
    functions: List[str]


class MCPRequest(BaseModel):
    command: str
    args: List[str] = []
    env: Optional[Dict[str, str]] = {}
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# ===== VALIDATION ENDPOINTS =====
# These endpoints validate configurations before creation/modification
# using the same logic as registry.py

@router.post("/agent/")
async def validate_agent_config(request: dict):
    """
    Validate agent configuration before creation/modification.
    Uses the COMPLETE agent building process to test runtime
    functionality.
    """
    try:
        result = await AgentValidator.validate_agent_config(
            name=request.get("name", ""),
            description=request.get("description", ""),
            emoji=request.get("emoji", "🔧"),
            tools_code=request.get("tools_code"),
            mcp_config=request.get("mcp_config"),
            agent_key=request.get("key"),
            llm_config=request.get("llm_config"),
            selected_tools=request.get("selected_tools"),
            selected_mcps=request.get("selected_mcps")
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate agent config: {str(e)}"
        )


@router.post("/agent/folder/")
async def validate_agent_folder(request: dict):
    """
    Validate existing agent folder structure.
    Uses the exact same logic as discover_agents() in registry.py.
    """
    try:
        folder_path = request.get("folder_path", "")

        if not folder_path:
            raise HTTPException(
                status_code=400, detail="folder_path is required"
            )

        result = AgentValidator.validate_agent_folder(folder_path)

        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate agent folder: {str(e)}"
        )


@router.post("/tool/")
async def validate_tool_config(tool_data: ToolRequest):
    """
    Validate tool configuration before creation/modification.
    Uses the exact same validation logic as tool registration.
    """
    try:
        result = ToolValidator.validate_tool_config(
            name=tool_data.name,
            description=tool_data.description,
            category=tool_data.category,
            code=tool_data.code,
            functions=tool_data.functions
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate tool config: {str(e)}"
        )


@router.post("/tool/code/")
async def validate_tool_code(request: dict):
    """
    Validate tool code execution without saving.
    Tests compilation and execution in isolation.
    """
    try:
        code = request.get("code", "")
        function_names = request.get("function_names", [])

        result = ToolValidator.validate_tool_code_execution(
            code, function_names
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate tool code: {str(e)}"
        )


@router.post("/mcp/")
async def validate_mcp_config(mcp_data: MCPRequest):
    """
    Validate MCP server configuration before creation/modification.
    Uses the exact same validation logic as MCP server initialization.
    """
    try:
        result = McpValidator.validate_mcp_server_config(
            name=mcp_data.name,
            description=mcp_data.description,
            category=mcp_data.category,
            config=mcp_data.config
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate MCP config: {str(e)}"
        )


@router.post("/mcp/connectivity/")
async def validate_mcp_connectivity(request: dict):
    """
    Test MCP server connectivity without persistent connection.
    Validates that the command exists and responds correctly.
    """
    try:
        name = request.get("name", "test_server")
        config = request.get("config", {})
        timeout = request.get("timeout", 10.0)

        result = await McpValidator.validate_mcp_server_connectivity(
            name, config, timeout
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test MCP connectivity: {str(e)}"
        )


# Template endpoints
@router.get("/templates/tools/")
async def get_tool_templates():
    """Get common tool templates and patterns"""
    try:
        templates = ToolValidator.get_common_tool_patterns()
        code_template = ToolValidator.get_tool_code_template()

        return {
            "templates": templates,
            "base_template": code_template
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tool templates: {str(e)}"
        )


@router.get("/templates/mcp/")
async def get_mcp_templates():
    """Get common MCP server templates"""
    try:
        templates = McpValidator.get_common_mcp_templates()

        return {
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get MCP templates: {str(e)}"
        )
