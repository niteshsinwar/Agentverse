"""
MCP Management API Endpoints - Modern Architecture
Uses Official Anthropic MCP SDK for validation and testing
Includes OAuth flow for remote MCP servers
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import asyncio
from pathlib import Path

from src.core.validation.mcp_validator import McpValidator
from src.core.mcp.client import MCPManager
from src.core.mcp.oauth_manager import oauth_manager, OAuthFlowTimeout, OAuthFlowError
from src.core.utils.mcp_auth import requires_oauth, has_valid_oauth_token

router = APIRouter()

# Configuration file paths
BACKEND_CONFIG_PATH = Path("config")
BACKEND_CONFIG_PATH.mkdir(parents=True, exist_ok=True)


# Request models
class MCPRequest(BaseModel):
    """Modern MCP server request - simplified format"""
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}


# MCP Management Endpoints
@router.get("/")
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


@router.post("/{mcp_id}/check-oauth")
async def check_oauth_requirement(mcp_id: str, mcp_data: MCPRequest):
    """
    Check if MCP server requires OAuth and if token exists.
    Returns oauth status without initiating flow.
    """
    try:
        # Check if OAuth required
        needs_oauth = requires_oauth(mcp_data.command, mcp_data.args)

        if not needs_oauth:
            return {
                "requires_oauth": False,
                "has_token": False,
                "message": "This MCP server does not require OAuth"
            }

        # Check if token exists
        from src.core.utils.mcp_auth import BASE_AUTH_DIR
        safe_name = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in mcp_id)
        auth_store_dir = BASE_AUTH_DIR / safe_name

        has_token = has_valid_oauth_token(auth_store_dir)

        return {
            "requires_oauth": True,
            "has_token": has_token,
            "auth_store": str(auth_store_dir),
            "message": "OAuth token found" if has_token else "OAuth authentication required"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check OAuth: {str(e)}")


@router.post("/{mcp_id}/oauth/initiate")
async def initiate_oauth(mcp_id: str, mcp_data: MCPRequest):
    """
    Initiate OAuth flow for mcp-remote server.
    This will start the process that opens browser for user authentication.
    """
    try:
        # Verify it's an OAuth server
        if not requires_oauth(mcp_data.command, mcp_data.args):
            raise HTTPException(
                status_code=400,
                detail="This MCP server does not require OAuth (not using mcp-remote)"
            )

        print(f"🔐 Initiating OAuth flow for MCP '{mcp_id}'...")

        # Start OAuth flow (this will open browser automatically)
        result = await oauth_manager.initiate_oauth_flow(
            server_name=mcp_id,
            command=mcp_data.command,
            args=mcp_data.args,
            env=mcp_data.env,
            timeout=120.0  # 2 minutes for user to complete auth
        )

        return {
            "success": True,
            "mcp_id": mcp_id,
            **result
        }

    except OAuthFlowTimeout as e:
        raise HTTPException(
            status_code=408,
            detail={
                "message": "OAuth authentication timed out",
                "error": str(e),
                "hint": "Please ensure you completed the browser authentication"
            }
        )
    except OAuthFlowError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "OAuth authentication failed",
                "error": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate OAuth: {str(e)}"
        )


@router.post("/")
async def add_mcp_server(mcp_id: str, mcp_data: MCPRequest):
    """
    Add a new MCP server with OAuth-aware validation.

    Flow:
    1. Check if OAuth required
    2. If OAuth needed and no token -> return error (client should call /oauth/initiate first)
    3. Validate config
    4. Test connectivity
    5. Save
    """
    try:
        # Step 1: Create server config (modern format)
        server_config = {
            "command": mcp_data.command,
            "args": mcp_data.args,
            "env": mcp_data.env
        }

        # Step 2: Check OAuth requirement
        # Note: For remote MCP servers, OAuth is handled on first tool use
        # We allow saving without OAuth validation since the server may not
        # require authentication until actual API calls are made
        is_remote = requires_oauth(mcp_data.command, mcp_data.args)

        if is_remote:
            print(f"ℹ️  Remote MCP server '{mcp_id}' - OAuth will be handled on first use")

        # Step 3: Validate using McpValidator
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

        # Step 4: Test MCP connectivity using validator
        # For remote OAuth servers, skip validation as it requires user interaction
        if is_remote:
            print(f"ℹ️  Skipping connectivity validation for remote MCP '{mcp_id}' - will validate on first use")
        else:
            print(f"🔍 Validating MCP '{mcp_id}' connectivity...")
            connectivity_result = await McpValidator.validate_mcp_server_connectivity(
                name=mcp_id,
                config=server_config,
                timeout=15.0
            )

            if not connectivity_result.valid:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"MCP server '{mcp_id}' validation failed",
                        "validation_errors": connectivity_result.to_dict()
                    }
                )

        # Step 4: Save MCP Server
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

        # Emit telemetry for comprehensive log panel
        from src.core.telemetry.events import emit_agent_management
        await emit_agent_management(
            agent_key=f"mcp_{mcp_id}",
            operation="mcp_created",
            meta={
                "mcp_id": mcp_id,
                "command": server_config["command"],
                "args_count": len(server_config.get("args", [])),
                "env_vars_count": len(server_config.get("env", {})),
                "total_servers": len(mcps["mcpServers"])
            }
        )

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


@router.put("/{mcp_id}")
async def update_mcp_server(mcp_id: str, mcp_data: MCPRequest):
    """Update an existing MCP server with Official SDK validation"""
    try:
        # Step 1: Create server config (modern format)
        server_config = {
            "command": mcp_data.command,
            "args": mcp_data.args,
            "env": mcp_data.env
        }

        # Step 2: Validate using McpValidator
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

        # Step 3: Test MCP connectivity using validator
        print(f"🔍 Validating MCP '{mcp_id}' connectivity...")
        connectivity_result = await McpValidator.validate_mcp_server_connectivity(
            name=mcp_id,
            config=server_config,
            timeout=15.0
        )

        if not connectivity_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": f"MCP server '{mcp_id}' validation failed",
                    "validation_errors": connectivity_result.to_dict()
                }
            )

        # Step 4: Update MCP Server
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

        # Emit telemetry for comprehensive log panel
        from src.core.telemetry.events import emit_agent_management
        await emit_agent_management(
            agent_key=f"mcp_{mcp_id}",
            operation="mcp_updated",
            meta={
                "mcp_id": mcp_id,
                "command": server_config["command"],
                "args_count": len(server_config.get("args", [])),
                "env_vars_count": len(server_config.get("env", {}))
            }
        )

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


@router.delete("/{mcp_id}")
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

        # Emit telemetry for comprehensive log panel
        from src.core.telemetry.events import emit_agent_management
        await emit_agent_management(
            agent_key=f"mcp_{mcp_id}",
            operation="mcp_deleted",
            meta={
                "mcp_id": mcp_id,
                "remaining_servers": len(servers)
            }
        )

        return {
            "message": f"MCP server '{mcp_id}' deleted successfully",
            "mcp_id": mcp_id,
            "remaining_servers": len(servers)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete MCP server: {str(e)}")
