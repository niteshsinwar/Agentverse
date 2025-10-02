"""
MCP Management API Endpoints
Handle mcp.json management via API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path

from src.core.validation.mcp_validator import McpValidator

router = APIRouter()

# Configuration file paths
BACKEND_CONFIG_PATH = Path("config")

# Ensure config directories exist
os.makedirs(BACKEND_CONFIG_PATH, exist_ok=True)


# Request models
class MCPRequest(BaseModel):
    command: str
    args: List[str] = []
    env: Optional[Dict[str, str]] = {}

    # For backward compatibility with old format
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


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


@router.post("/")
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

        # Step 2: Test ACTUAL MCP Protocol Startup (REQUIRED)
        if server_config.get("command"):
            try:
                # Test the complete MCP startup process like real agent building
                from src.core.mcp.client import MCPManager
                test_config = {"mcpServers": {mcp_id: server_config}}
                mcp_manager = MCPManager.from_config(test_config)

                # This must succeed or MCP creation fails (with timeout)
                import asyncio
                try:
                    startup_results = await asyncio.wait_for(
                        mcp_manager.start_all(),
                        timeout=15.0  # 15 second timeout for MCP startup
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": f"MCP server '{mcp_id}' startup timeout",
                            "error": "MCP server took too long to start (>15s)",
                            "hint": "Check if the MCP server command is responsive"
                        }
                    )
                if not startup_results.get(mcp_id, False):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": f"MCP server '{mcp_id}' failed to start during validation",
                            "error": "MCP server startup failed - this would cause agent building to fail"
                        }
                    )

                # Test tool discovery
                server = mcp_manager.servers[mcp_id]
                if server.tools_cache:
                    tool_count = len(server.tools_cache)
                    print(f"✅ MCP validation passed: {tool_count} tools discovered")
                else:
                    print("⚠️ MCP validation warning: No tools discovered from server")

                # Clean up
                await mcp_manager.stop_all()

            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as conn_error:
                # Real connectivity failures should FAIL the creation
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"MCP server '{mcp_id}' validation failed",
                        "error": f"Failed to start MCP server: {str(conn_error)}",
                        "hint": "This MCP configuration would cause agent building to fail"
                    }
                )

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


@router.put("/{mcp_id}")
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

        # Step 2: Test ACTUAL MCP Protocol Startup (REQUIRED) - Same as CREATE
        if server_config.get("command"):
            try:
                # Test the complete MCP startup process like real agent building
                from src.core.mcp.client import MCPManager
                test_config = {"mcpServers": {mcp_id: server_config}}
                mcp_manager = MCPManager.from_config(test_config)

                # This must succeed or MCP update fails (with timeout)
                import asyncio
                try:
                    startup_results = await asyncio.wait_for(
                        mcp_manager.start_all(),
                        timeout=15.0  # 15 second timeout for MCP startup
                    )
                except asyncio.TimeoutError:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": f"MCP server '{mcp_id}' startup timeout",
                            "error": "MCP server took too long to start (>15s)",
                            "hint": "Check if the MCP server command is responsive"
                        }
                    )
                if not startup_results.get(mcp_id, False):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": f"MCP server '{mcp_id}' failed to start during validation",
                            "error": "MCP server startup failed - this would cause agent building to fail"
                        }
                    )

                # Test tool discovery
                server = mcp_manager.servers[mcp_id]
                if server.tools_cache:
                    tool_count = len(server.tools_cache)
                    print(f"✅ MCP validation passed: {tool_count} tools discovered")
                else:
                    print("⚠️ MCP validation warning: No tools discovered from server")

                # Clean up
                await mcp_manager.stop_all()

            except HTTPException:
                raise  # Re-raise HTTP exceptions
            except Exception as conn_error:
                # Real connectivity failures should FAIL the update
                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": f"MCP server '{mcp_id}' validation failed",
                        "error": f"Failed to start MCP server: {str(conn_error)}",
                        "hint": "This MCP configuration would cause agent building to fail"
                    }
                )

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

        return {
            "message": f"MCP server '{mcp_id}' deleted successfully",
            "mcp_id": mcp_id,
            "remaining_servers": len(servers)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete MCP server: {str(e)}")
