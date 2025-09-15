"""
Configuration Management API Endpoints
Handle tools.json, mcp.json, and settings.json management via API
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import get_orchestrator_service
from src.core.validation.agent_validator import AgentValidator
from src.core.validation.tool_validator import ToolValidator
from src.core.validation.mcp_validator import McpValidator

router = APIRouter()

# Configuration file paths
FRONTEND_DATA_PATH = Path("../frontend/desktop-ui/src/data")
BACKEND_CONFIG_PATH = Path("config")

# Ensure config directories exist
os.makedirs(BACKEND_CONFIG_PATH, exist_ok=True)

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

    # For backward compatibility with old format
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class SettingsRequest(BaseModel):
    settings: Dict[str, Any]

# Tools Management Endpoints
@router.get("/tools/")
async def get_tools():
    """Get all available tools from tools.json"""
    try:
        tools_path = BACKEND_CONFIG_PATH / "tools.json"
        if tools_path.exists():
            with open(tools_path, 'r') as f:
                tools = json.load(f)
            return {"tools": tools, "count": len(tools)}
        return {"tools": {}, "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tools: {str(e)}")

@router.post("/tools/")
async def add_tool(tool_id: str, tool_data: ToolRequest):
    """Add a new tool to tools.json with validation"""
    try:
        # Step 1: Validate Tool Configuration
        validation_result = ToolValidator.validate_tool_config(
            name=tool_data.name,
            description=tool_data.description,
            category=tool_data.category,
            code=tool_data.code,
            functions=tool_data.functions
        )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Tool configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Validate Code Execution
        if tool_data.code.strip():
            code_validation_result = ToolValidator.validate_tool_code_execution(
                code=tool_data.code,
                function_names=tool_data.functions
            )
            # Continue even if code execution test has warnings
            if not code_validation_result.valid:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Tool code validation failed",
                        "validation_errors": code_validation_result.to_dict()
                    }
                )

        # Step 3: Save Tool
        tools_path = BACKEND_CONFIG_PATH / "tools.json"

        # Load existing tools
        tools = {}
        if tools_path.exists():
            with open(tools_path, 'r') as f:
                tools = json.load(f)

        # Check if tool already exists
        if tool_id in tools:
            raise HTTPException(status_code=400, detail=f"Tool '{tool_id}' already exists")

        # Add new tool
        tools[tool_id] = tool_data.dict()

        # Save back to file
        with open(tools_path, 'w') as f:
            json.dump(tools, f, indent=2)

        return {
            "message": f"Tool '{tool_id}' added successfully",
            "tool_id": tool_id,
            "total_tools": len(tools),
            "validation_passed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add tool: {str(e)}")

@router.put("/tools/{tool_id}")
async def update_tool(tool_id: str, tool_data: ToolRequest):
    """Update an existing tool in tools.json with validation"""
    try:
        # Step 1: Validate Tool Configuration
        validation_result = ToolValidator.validate_tool_config(
            name=tool_data.name,
            description=tool_data.description,
            category=tool_data.category,
            code=tool_data.code,
            functions=tool_data.functions
        )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Tool configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Validate Code Execution
        if tool_data.code.strip():
            code_validation_result = ToolValidator.validate_tool_code_execution(
                code=tool_data.code,
                function_names=tool_data.functions
            )
            # Continue even if code execution test has warnings
            if not code_validation_result.valid:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": "Tool code validation failed",
                        "validation_errors": code_validation_result.to_dict()
                    }
                )

        # Step 3: Update Tool
        tools_path = BACKEND_CONFIG_PATH / "tools.json"

        # Load existing tools
        if not tools_path.exists():
            raise HTTPException(status_code=404, detail="Tools configuration file not found")

        with open(tools_path, 'r') as f:
            tools = json.load(f)

        # Check if tool exists
        if tool_id not in tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Update tool
        tools[tool_id] = tool_data.dict()

        # Save back to file
        with open(tools_path, 'w') as f:
            json.dump(tools, f, indent=2)

        return {
            "message": f"Tool '{tool_id}' updated successfully",
            "tool_id": tool_id,
            "validation_passed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")

@router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool from tools.json"""
    try:
        tools_path = BACKEND_CONFIG_PATH / "tools.json"

        # Load existing tools
        if not tools_path.exists():
            raise HTTPException(status_code=404, detail="Tools configuration file not found")

        with open(tools_path, 'r') as f:
            tools = json.load(f)

        # Check if tool exists
        if tool_id not in tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Delete tool
        del tools[tool_id]

        # Save back to file
        with open(tools_path, 'w') as f:
            json.dump(tools, f, indent=2)

        return {
            "message": f"Tool '{tool_id}' deleted successfully",
            "tool_id": tool_id,
            "remaining_tools": len(tools)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")

# MCP Management Endpoints
@router.get("/mcp/")
async def get_mcp_servers():
    """Get all available MCP servers from mcp.json"""
    try:
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"
        if mcp_path.exists():
            with open(mcp_path, 'r') as f:
                mcps = json.load(f)

            # Handle new format with mcpServers wrapper
            if "mcpServers" in mcps:
                servers = mcps["mcpServers"]
                return {"mcpServers": servers, "count": len(servers)}
            else:
                # Handle old format (direct server mapping)
                return {"mcpServers": mcps, "count": len(mcps)}

        return {"mcpServers": {}, "count": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load MCP servers: {str(e)}")

@router.post("/mcp/")
async def add_mcp_server(mcp_id: str, mcp_data: MCPRequest):
    """Add a new MCP server to mcp.json with validation"""
    try:
        # Step 1: Validate Configuration - handle both old and new format
        if mcp_data.config is not None:
            # Old format - use existing validation
            validation_result = McpValidator.validate_mcp_server_config(
                name=mcp_data.name or mcp_id,
                description=mcp_data.description or "",
                category=mcp_data.category or "",
                config=mcp_data.config
            )
            server_config = mcp_data.config
        else:
            # New simplified format - create config from direct fields
            server_config = {
                "command": mcp_data.command,
                "args": mcp_data.args,
                "env": mcp_data.env or {}
            }
            # Validate using the new simplified format
            validation_result = McpValidator.validate_mcp_servers_config(
                {mcp_id: server_config}
            )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "MCP configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Test Connectivity
        if server_config.get("command"):
            try:
                connectivity_result = await McpValidator.validate_mcp_server_connectivity(
                    name=mcp_id,
                    config=server_config,
                    timeout=10.0
                )
                # Continue even if connectivity test fails (warnings only)
            except Exception as conn_error:
                # Log connectivity issues but don't fail the creation
                print(f"Warning: Connectivity test failed for {mcp_id}: {conn_error}")

        # Step 3: Save MCP Server
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"

        # Load existing MCPs
        mcps = {}
        if mcp_path.exists():
            with open(mcp_path, 'r') as f:
                mcps = json.load(f)

        # Ensure mcpServers structure exists
        if "mcpServers" not in mcps:
            mcps = {"mcpServers": mcps}  # Migrate old format

        # Check if MCP already exists
        if mcp_id in mcps["mcpServers"]:
            raise HTTPException(status_code=400, detail=f"MCP server '{mcp_id}' already exists")

        # Add new MCP in simplified format
        mcps["mcpServers"][mcp_id] = server_config

        # Save back to file
        with open(mcp_path, 'w') as f:
            json.dump(mcps, f, indent=2)

        return {
            "message": f"MCP server '{mcp_id}' added successfully",
            "mcp_id": mcp_id,
            "mcp_data": server_config,
            "validation_passed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add MCP server: {str(e)}")

@router.put("/mcp/{mcp_id}")
async def update_mcp_server(mcp_id: str, mcp_data: MCPRequest):
    """Update an existing MCP server in mcp.json with validation"""
    try:
        # Step 1: Validate Configuration - handle both old and new format
        if mcp_data.config is not None:
            # Old format - use existing validation
            validation_result = McpValidator.validate_mcp_server_config(
                name=mcp_data.name or mcp_id,
                description=mcp_data.description or "",
                category=mcp_data.category or "",
                config=mcp_data.config
            )
            server_config = mcp_data.config
        else:
            # New simplified format - create config from direct fields
            server_config = {
                "command": mcp_data.command,
                "args": mcp_data.args,
                "env": mcp_data.env or {}
            }
            # Validate using the new simplified format
            validation_result = McpValidator.validate_mcp_servers_config(
                {mcp_id: server_config}
            )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "MCP configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Test Connectivity
        if server_config.get("command"):
            try:
                connectivity_result = await McpValidator.validate_mcp_server_connectivity(
                    name=mcp_id,
                    config=server_config,
                    timeout=10.0
                )
                # Continue even if connectivity test fails (warnings only)
            except Exception as conn_error:
                # Log connectivity issues but don't fail the update
                print(f"Warning: Connectivity test failed for {mcp_id}: {conn_error}")

        # Step 3: Update MCP Server
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"

        # Load existing MCPs
        if not mcp_path.exists():
            raise HTTPException(status_code=404, detail="MCP configuration file not found")

        with open(mcp_path, 'r') as f:
            mcps = json.load(f)

        # Handle new format with mcpServers wrapper
        servers = mcps
        if "mcpServers" in mcps:
            servers = mcps["mcpServers"]

        # Check if MCP exists
        if mcp_id not in servers:
            raise HTTPException(status_code=404, detail=f"MCP server '{mcp_id}' not found")

        # Update MCP with simplified format
        servers[mcp_id] = server_config

        # Update the original structure
        if "mcpServers" in mcps:
            mcps["mcpServers"] = servers

        # Save back to file
        with open(mcp_path, 'w') as f:
            json.dump(mcps, f, indent=2)

        return {
            "message": f"MCP server '{mcp_id}' updated successfully",
            "mcp_id": mcp_id,
            "mcp_data": server_config,
            "validation_passed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update MCP server: {str(e)}")

@router.delete("/mcp/{mcp_id}")
async def delete_mcp_server(mcp_id: str):
    """Delete an MCP server from mcp.json"""
    try:
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"

        # Load existing MCPs
        if not mcp_path.exists():
            raise HTTPException(status_code=404, detail="MCP configuration file not found")

        with open(mcp_path, 'r') as f:
            mcps = json.load(f)

        # Handle new format with mcpServers wrapper
        servers = mcps
        if "mcpServers" in mcps:
            servers = mcps["mcpServers"]

        # Check if MCP exists
        if mcp_id not in servers:
            raise HTTPException(status_code=404, detail=f"MCP server '{mcp_id}' not found")

        # Delete MCP
        del servers[mcp_id]

        # Update the original structure
        if "mcpServers" in mcps:
            mcps["mcpServers"] = servers

        # Save back to file
        with open(mcp_path, 'w') as f:
            json.dump(mcps, f, indent=2)

        return {
            "message": f"MCP server '{mcp_id}' deleted successfully",
            "mcp_id": mcp_id,
            "remaining_servers": len(servers)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete MCP server: {str(e)}")

# Settings Management Endpoints
@router.get("/settings/")
async def get_settings():
    """Get current settings from settings.json (overrides) and default settings"""
    try:
        # Load default settings from Python settings
        from src.core.config.settings import get_settings
        default_settings = get_settings()

        # Convert to dict
        settings_dict = {}
        for field_name, field_info in default_settings.__fields__.items():
            settings_dict[field_name] = getattr(default_settings, field_name)

        # Load overrides from settings.json if exists
        settings_path = BACKEND_CONFIG_PATH / "settings.json"
        overrides = {}
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                overrides = json.load(f)

        # Merge settings
        final_settings = {**settings_dict, **overrides}

        return {
            "settings": final_settings,
            "overrides": overrides,
            "has_overrides": len(overrides) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")

@router.post("/settings/")
async def update_settings(settings_request: SettingsRequest):
    """Update settings by saving to settings.json (overrides default settings.py)"""
    try:
        settings_path = BACKEND_CONFIG_PATH / "settings.json"

        # Load existing overrides
        existing_overrides = {}
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                existing_overrides = json.load(f)

        # Merge with new settings
        updated_overrides = {**existing_overrides, **settings_request.settings}

        # Save overrides to settings.json
        with open(settings_path, 'w') as f:
            json.dump(updated_overrides, f, indent=2)

        # Refresh settings cache to pick up changes
        from src.core.config.settings import refresh_settings
        refresh_settings()

        return {
            "message": "Settings updated successfully",
            "overrides_count": len(updated_overrides),
            "updated_keys": list(settings_request.settings.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.delete("/settings/")
async def reset_settings():
    """Reset settings by removing settings.json overrides"""
    try:
        settings_path = BACKEND_CONFIG_PATH / "settings.json"

        if settings_path.exists():
            os.remove(settings_path)
            # Refresh settings cache to pick up changes
            from src.core.config.settings import refresh_settings
            refresh_settings()
            return {"message": "Settings reset to defaults successfully"}
        else:
            return {"message": "No settings overrides found, already using defaults"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")

@router.get("/settings/validate/")
async def validate_settings():
    """Validate current settings configuration"""
    try:
        from src.core.config.settings import get_settings
        settings = get_settings()

        # Basic validation
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }

        # Check API keys
        if not settings.openai_api_key:
            validation_results["warnings"].append("OpenAI API key not configured")
        if not settings.github_token:
            validation_results["warnings"].append("GitHub token not configured")

        # Check database URL
        if not settings.database_url:
            validation_results["errors"].append("Database URL not configured")
            validation_results["valid"] = False

        # Check file size limits
        if settings.max_upload_size_mb <= 0:
            validation_results["errors"].append("Max upload size must be greater than 0")
            validation_results["valid"] = False

        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate settings: {str(e)}")

# Backup and Restore
@router.post("/backup/")
async def create_backup():
    """Create a backup of current configuration files"""
    try:
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKEND_CONFIG_PATH / f"backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)

        # Backup configuration files
        files_backed_up = []

        # Backup tools.json
        tools_path = BACKEND_CONFIG_PATH / "tools.json"
        if tools_path.exists():
            shutil.copy2(tools_path, backup_dir / "tools.json")
            files_backed_up.append("tools.json")

        # Backup mcp.json
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"
        if mcp_path.exists():
            shutil.copy2(mcp_path, backup_dir / "mcp.json")
            files_backed_up.append("mcp.json")

        # Backup settings.json
        settings_path = BACKEND_CONFIG_PATH / "settings.json"
        if settings_path.exists():
            shutil.copy2(settings_path, backup_dir / "settings.json")
            files_backed_up.append("settings.json")

        return {
            "message": "Backup created successfully",
            "backup_path": str(backup_dir),
            "timestamp": timestamp,
            "files_backed_up": files_backed_up
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")

@router.get("/status/")
async def get_config_status():
    """Get status of all configuration files"""
    try:
        status = {
            "tools": {
                "exists": (BACKEND_CONFIG_PATH / "tools.json").exists(),
                "path": str(BACKEND_CONFIG_PATH / "tools.json"),
                "count": 0
            },
            "mcp": {
                "exists": (BACKEND_CONFIG_PATH / "mcp.json").exists(),
                "path": str(BACKEND_CONFIG_PATH / "mcp.json"),
                "count": 0
            },
            "settings": {
                "overrides_exist": (BACKEND_CONFIG_PATH / "settings.json").exists(),
                "overrides_path": str(BACKEND_CONFIG_PATH / "settings.json"),
                "overrides_count": 0
            }
        }

        # Count tools
        if status["tools"]["exists"]:
            with open(BACKEND_CONFIG_PATH / "tools.json", 'r') as f:
                tools = json.load(f)
                status["tools"]["count"] = len(tools)

        # Count MCPs
        if status["mcp"]["exists"]:
            with open(BACKEND_CONFIG_PATH / "mcp.json", 'r') as f:
                mcps = json.load(f)
                status["mcp"]["count"] = len(mcps)

        # Count settings overrides
        if status["settings"]["overrides_exist"]:
            with open(BACKEND_CONFIG_PATH / "settings.json", 'r') as f:
                overrides = json.load(f)
                status["settings"]["overrides_count"] = len(overrides)

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config status: {str(e)}")


# ===== VALIDATION ENDPOINTS =====
# These endpoints validate configurations before creation/modification using the same logic as registry.py

@router.post("/validate/agent/")
async def validate_agent_config(request: dict):
    """
    Validate agent configuration before creation/modification
    Uses the exact same validation logic as registry.py
    """
    try:
        result = AgentValidator.validate_agent_config(
            name=request.get("name", ""),
            description=request.get("description", ""),
            emoji=request.get("emoji", "🔧"),
            tools_code=request.get("tools_code"),
            mcp_config=request.get("mcp_config"),
            agent_key=request.get("key")
        )

        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate agent config: {str(e)}")


@router.post("/validate/tool/")
async def validate_tool_config(tool_data: ToolRequest):
    """
    Validate tool configuration before creation/modification
    Uses the exact same validation logic as tool registration
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
        raise HTTPException(status_code=500, detail=f"Failed to validate tool config: {str(e)}")


@router.post("/validate/tool/code/")
async def validate_tool_code(request: dict):
    """
    Validate tool code execution without saving
    Tests compilation and execution in isolation
    """
    try:
        code = request.get("code", "")
        function_names = request.get("function_names", [])

        result = ToolValidator.validate_tool_code_execution(code, function_names)

        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate tool code: {str(e)}")


@router.post("/validate/mcp/")
async def validate_mcp_config(mcp_data: MCPRequest):
    """
    Validate MCP server configuration before creation/modification
    Uses the exact same validation logic as MCP server initialization
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
        raise HTTPException(status_code=500, detail=f"Failed to validate MCP config: {str(e)}")


@router.post("/validate/mcp/connectivity/")
async def validate_mcp_connectivity(request: dict):
    """
    Test MCP server connectivity without persistent connection
    Validates that the command exists and responds correctly
    """
    try:
        name = request.get("name", "test_server")
        config = request.get("config", {})
        timeout = request.get("timeout", 10.0)

        result = await McpValidator.validate_mcp_server_connectivity(name, config, timeout)

        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test MCP connectivity: {str(e)}")


@router.get("/validate/templates/tools/")
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
        raise HTTPException(status_code=500, detail=f"Failed to get tool templates: {str(e)}")


@router.get("/validate/templates/mcp/")
async def get_mcp_templates():
    """Get common MCP server templates"""
    try:
        templates = McpValidator.get_common_mcp_templates()

        return {
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get MCP templates: {str(e)}")


@router.post("/validate/agent/folder/")
async def validate_agent_folder(request: dict):
    """
    Validate existing agent folder structure
    Uses the exact same logic as discover_agents() in registry.py
    """
    try:
        folder_path = request.get("folder_path", "")

        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")

        result = AgentValidator.validate_agent_folder(folder_path)

        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate agent folder: {str(e)}")