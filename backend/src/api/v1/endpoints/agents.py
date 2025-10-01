
"""
Agents API Endpoints
RESTful endpoints for agent management with full CRUD operations and user action tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import yaml
import shutil
import time

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import get_orchestrator_service
from src.core.validation.agent_validator import AgentValidator
from src.core.telemetry.user_actions import (
    user_action_tracker,
    track_agent_creation,
    UserActionType
)

router = APIRouter()

# Pydantic models for request validation
class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"

class CreateAgentRequest(BaseModel):
    name: str
    description: str
    emoji: str = "🤖"
    llm: LLMConfig = LLMConfig()
    key: Optional[str] = None
    # Legacy fields for backward compatibility
    tools_code: Optional[str] = ""
    mcp_config: Optional[Dict[str, Any]] = {}
    selected_tools: Optional[List[str]] = []
    selected_mcps: Optional[List[str]] = []

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    emoji: Optional[str] = None
    llm: Optional[LLMConfig] = None
    new_key: Optional[str] = None  # For agent folder renaming
    # Legacy fields for backward compatibility
    tools_code: Optional[str] = None
    mcp_config: Optional[Dict[str, Any]] = None
    selected_tools: Optional[List[str]] = None
    selected_mcps: Optional[List[str]] = None


@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    List all available agents.

    Returns a list of all agents that can be used in conversations.
    """
    try:
        agents = service.list_available_agents()
        result = []

        for spec in agents.values():
            agent_data = {
                "key": spec.key,
                "name": spec.name,
                "description": spec.description,
                "emoji": spec.emoji,
                "llm": spec.llm,
                "mcp_config": spec.mcp_config
            }

            # Read tools.py content if it exists
            if spec.tools_module and os.path.exists(spec.tools_module):
                try:
                    with open(spec.tools_module, 'r', encoding='utf-8') as f:
                        agent_data["tools_code"] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read tools.py for {spec.key}: {e}")
                    agent_data["tools_code"] = None
            else:
                agent_data["tools_code"] = None

            result.append(agent_data)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")


@router.get("/{agent_key}")
async def get_agent_details(
    agent_key: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get detailed information about a specific agent.

    Returns comprehensive information about an agent including its configuration.
    """
    try:
        agents = service.list_available_agents()

        if agent_key not in agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_key} not found")

        spec = agents[agent_key]

        agent_data = {
            "key": spec.key,
            "name": spec.name,
            "description": spec.description,
            "emoji": spec.emoji,
            "folder": spec.folder,
            "has_tools": spec.tools_module is not None,
            "has_mcp_config": bool(spec.mcp_config),
            "mcp_config": spec.mcp_config
        }

        # Read tools.py content if it exists
        if spec.tools_module and os.path.exists(spec.tools_module):
            try:
                with open(spec.tools_module, 'r', encoding='utf-8') as f:
                    agent_data["tools_code"] = f.read()
            except Exception as e:
                print(f"Warning: Could not read tools.py for {spec.key}: {e}")
                agent_data["tools_code"] = None
        else:
            agent_data["tools_code"] = None

        return agent_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent details: {str(e)}")




@router.post("/create/")
async def create_agent(
    request: CreateAgentRequest,
    http_request: Request,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Create a new agent with tools and MCP configuration with validation.
    Includes comprehensive user action tracking.

    Creates agent folder structure with agent.yaml, mcp.json, and tools.py files.
    """
    agent_key = None
    agent_dir = None

    # Get session context from headers or create one
    session_id = http_request.headers.get('X-Session-ID', 'default_session')

    # Get user context
    user_context = {
        'user_agent': http_request.headers.get('User-Agent'),
        'ip_address': http_request.client.host if http_request.client else None,
        'page_url': str(http_request.url)
    }

    # Start tracking agent creation
    operation_id = track_agent_creation(
        session_id=session_id,
        agent_data=request.dict(),
        user_context=user_context
    )

    try:
        # Generate agent key if not provided
        agent_key = request.key or request.name.lower().replace(' ', '_').replace('-', '_')

        # Remove non-alphanumeric characters except underscores
        import re
        agent_key = re.sub(r'[^a-zA-Z0-9_]', '', agent_key)

        # Step 1: Validate Agent Configuration (Complete Runtime Test)
        validation_result = await AgentValidator.validate_agent_config(
            name=request.name,
            description=request.description,
            emoji=request.emoji,
            tools_code=request.tools_code,
            mcp_config=request.mcp_config,
            agent_key=agent_key,
            llm_config=request.llm.dict() if request.llm else None,
            selected_tools=request.selected_tools,
            selected_mcps=request.selected_mcps
        )

        if not validation_result.valid:
            # Track validation errors
            user_action_tracker.complete_operation(
                session_id=session_id,
                operation_id=operation_id,
                action_type=UserActionType.AGENT_CREATE_START,
                success=False,
                resource_type="agent",
                resource_id=agent_key,
                error_message="Agent configuration validation failed",
                validation_errors=[validation_result.to_dict()]
            )

            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Agent configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Validate Agent Uniqueness
        agents = service.list_available_agents()
        if agent_key in agents:
            raise HTTPException(status_code=400, detail=f"Agent with key '{agent_key}' already exists")

        # Step 3: Create Agent Files
        agent_dir = os.path.join("agent_store", agent_key)
        os.makedirs(agent_dir, exist_ok=True)

        # Create agent.yaml with simplified schema
        agent_yaml = {
            "name": request.name,
            "description": request.description,
            "emoji": request.emoji,
            "llm": {
                "provider": request.llm.provider,
                "model": request.llm.model
            }
        }

        with open(os.path.join(agent_dir, "agent.yaml"), 'w') as f:
            yaml.dump(agent_yaml, f, default_flow_style=False)

        # Create mcp.json
        mcp_config = request.mcp_config or {}
        with open(os.path.join(agent_dir, "mcp.json"), 'w') as f:
            json.dump(mcp_config, f, indent=2)

        # Create tools.py if tools_code provided
        if request.tools_code and request.tools_code.strip():
            with open(os.path.join(agent_dir, "tools.py"), 'w') as f:
                f.write(request.tools_code)
        else:
            # Create empty tools.py
            with open(os.path.join(agent_dir, "tools.py"), 'w') as f:
                f.write("# Agent tools will be defined here\n")

        # Refresh agents to pick up the new agent
        service.refresh_agents()

        # Track successful completion
        user_action_tracker.complete_operation(
            session_id=session_id,
            operation_id=operation_id,
            action_type=UserActionType.AGENT_CREATE_START,
            success=True,
            resource_type="agent",
            resource_id=agent_key,
            result_data={
                "agent_dir": agent_dir,
                "has_tools": bool(request.tools_code and request.tools_code.strip()),
                "has_mcp_config": bool(request.mcp_config),
                "selected_tools_count": len(request.selected_tools or []),
                "selected_mcps_count": len(request.selected_mcps or [])
            }
        )

        return {
            "message": f"Agent '{request.name}' created successfully",
            "agent_key": agent_key,
            "agent_dir": agent_dir,
            "validation_passed": True
        }

    except HTTPException as e:
        # Track HTTP errors (validation, conflicts, etc.)
        user_action_tracker.complete_operation(
            session_id=session_id,
            operation_id=operation_id,
            action_type=UserActionType.AGENT_CREATE_START,
            success=False,
            resource_type="agent",
            resource_id=agent_key,
            error_message=str(e.detail)
        )
        raise
    except Exception as e:
        # Track system errors and clean up
        user_action_tracker.complete_operation(
            session_id=session_id,
            operation_id=operation_id,
            action_type=UserActionType.AGENT_CREATE_START,
            success=False,
            resource_type="agent",
            resource_id=agent_key,
            error_message=f"System error during agent creation: {str(e)}"
        )

        # Clean up if creation failed
        if agent_dir and os.path.exists(agent_dir):
            shutil.rmtree(agent_dir)
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.put("/{agent_key}/")
async def update_agent(
    agent_key: str,
    request: UpdateAgentRequest,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Update an existing agent's configuration with validation.

    Updates agent.yaml, mcp.json, and tools.py files.
    """
    try:
        # Verify agent exists
        agents = service.list_available_agents()
        if agent_key not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found")

        agent_spec = agents[agent_key]
        agent_dir = agent_spec.folder

        # Load current configuration for validation
        agent_yaml_path = os.path.join(agent_dir, "agent.yaml")
        if os.path.exists(agent_yaml_path):
            with open(agent_yaml_path, 'r') as f:
                current_yaml = yaml.safe_load(f) or {}
        else:
            current_yaml = {}

        # Prepare updated values for validation
        updated_name = request.name if request.name is not None else current_yaml.get('name', '')
        updated_description = request.description if request.description is not None else current_yaml.get('description', '')
        updated_emoji = request.emoji if request.emoji is not None else current_yaml.get('emoji', '🤖')
        updated_llm = None
        if request.llm is not None:
            updated_llm = {
                "provider": request.llm.provider,
                "model": request.llm.model
            }
        else:
            updated_llm = current_yaml.get('llm', {"provider": "openai", "model": "gpt-4o-mini"})
        updated_tools_code = request.tools_code if request.tools_code is not None else None
        updated_mcp_config = request.mcp_config if request.mcp_config is not None else None

        # Step 1: Validate Updated Agent Configuration (Complete Runtime Test)
        validation_result = await AgentValidator.validate_agent_config(
            name=updated_name,
            description=updated_description,
            emoji=updated_emoji,
            tools_code=updated_tools_code,
            mcp_config=updated_mcp_config,
            agent_key=agent_key,
            llm_config=updated_llm,
            selected_tools=request.selected_tools,
            selected_mcps=request.selected_mcps
        )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Agent configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Handle agent key renaming (folder rename) if new_key is provided
        new_agent_key = agent_key
        if request.new_key and request.new_key != agent_key:
            # Clean the new key
            import re
            new_key_clean = re.sub(r'[^a-zA-Z0-9_]', '', request.new_key.lower().replace(' ', '_').replace('-', '_'))

            # Check if new key already exists
            if new_key_clean in agents:
                raise HTTPException(status_code=400, detail=f"Agent with key '{new_key_clean}' already exists")

            # Rename the folder
            new_agent_dir = os.path.join("agent_store", new_key_clean)
            shutil.move(agent_dir, new_agent_dir)
            agent_dir = new_agent_dir
            agent_yaml_path = os.path.join(agent_dir, "agent.yaml")
            new_agent_key = new_key_clean

        # Step 2: Update Files
        # Update agent.yaml with simplified schema
        if request.name is not None:
            current_yaml['name'] = request.name
        if request.description is not None:
            current_yaml['description'] = request.description
        if request.emoji is not None:
            current_yaml['emoji'] = request.emoji
        if request.llm is not None:
            current_yaml['llm'] = {
                "provider": request.llm.provider,
                "model": request.llm.model
            }

        # Ensure LLM configuration exists
        if 'llm' not in current_yaml:
            current_yaml['llm'] = {"provider": "openai", "model": "gpt-4o-mini"}

        # Write updated agent.yaml
        with open(agent_yaml_path, 'w') as f:
            yaml.dump(current_yaml, f, default_flow_style=False)

        # Update mcp.json if provided
        if request.mcp_config is not None:
            mcp_path = os.path.join(agent_dir, "mcp.json")
            with open(mcp_path, 'w') as f:
                json.dump(request.mcp_config, f, indent=2)

        # Update tools.py if provided
        if request.tools_code is not None:
            tools_path = os.path.join(agent_dir, "tools.py")
            with open(tools_path, 'w') as f:
                f.write(request.tools_code)

        # Step 3: Refresh and Deploy
        service.refresh_agents()

        return {
            "message": f"Agent '{new_agent_key}' updated successfully",
            "agent_key": new_agent_key,
            "original_key": agent_key,
            "validation_passed": True,
            "folder_renamed": new_agent_key != agent_key
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/{agent_key}/")
async def delete_agent(
    agent_key: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Delete an agent and its configuration.

    Removes the agent directory and all associated files.
    """
    try:
        # Verify agent exists
        agents = service.list_available_agents()
        if agent_key not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found")

        agent_spec = agents[agent_key]
        agent_dir = agent_spec.folder

        # Don't delete the TEMPLATE agent
        if agent_key == "TEMPLATE":
            raise HTTPException(status_code=400, detail="Cannot delete the TEMPLATE agent")

        # Remove agent directory
        if os.path.exists(agent_dir):
            shutil.rmtree(agent_dir)

        # Refresh agents to remove from list
        service.refresh_agents()

        return {
            "message": f"Agent '{agent_key}' deleted successfully",
            "agent_key": agent_key
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


@router.post("/test-register/")
async def test_register_agent(request: dict):
    """
    Test agent registration without saving (validation endpoint)
    This endpoint validates an agent configuration by attempting to build it
    """
    try:
        from src.core.validation.agent_validator import AgentValidator

        result = await AgentValidator.validate_agent_config(
            name=request.get("name", ""),
            description=request.get("description", ""),
            emoji=request.get("emoji", "🔧"),
            tools_code=request.get("tools_code"),
            mcp_config=request.get("mcp_config"),
            agent_key=request.get("agent_key"),
            llm_config=request.get("llm_config"),
            selected_tools=request.get("selected_tools"),
            selected_mcps=request.get("selected_mcps")
        )

        return {
            "is_valid": result.valid,
            "errors": [error.message for error in result.errors],
            "warnings": [warning.message for warning in result.warnings],
            "agent_preview": {
                "name": request.get("name"),
                "description": request.get("description"),
                "emoji": request.get("emoji")
            } if result.valid else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test agent registration: {str(e)}")


