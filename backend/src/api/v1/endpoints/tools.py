"""
Tools Management API Endpoints
Handle tools.json management via API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os
from pathlib import Path

from src.core.validation.tool_validator import ToolValidator

router = APIRouter()

# Configuration file paths
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


# Tools Management Endpoints
@router.get("/")
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


@router.post("/")
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


@router.put("/{tool_id}")
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


@router.delete("/{tool_id}")
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