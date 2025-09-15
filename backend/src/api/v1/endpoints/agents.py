
"""
Agents API Endpoints
RESTful endpoints for agent management with full CRUD operations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import yaml
import shutil

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import get_orchestrator_service
from src.core.validation.agent_validator import AgentValidator

router = APIRouter()

# Pydantic models for request validation
class CreateAgentRequest(BaseModel):
    name: str
    description: str
    emoji: str = "🤖"
    key: Optional[str] = None
    tools_code: Optional[str] = ""
    mcp_config: Optional[Dict[str, Any]] = {}
    selected_tools: Optional[List[str]] = []
    selected_mcps: Optional[List[str]] = []

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    emoji: Optional[str] = None
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


@router.post("/refresh")
async def refresh_agents(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Refresh agent discovery.

    Rescans the agents directory for new or updated agents.
    """
    try:
        service.refresh_agents()
        agents = service.list_available_agents()

        return {
            "message": "Agents refreshed successfully",
            "agents_count": len(agents),
            "agents": list(agents.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh agents: {str(e)}")


@router.post("/create/")
async def create_agent(
    request: CreateAgentRequest,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Create a new agent with tools and MCP configuration with validation.

    Creates agent folder structure with agent.yaml, mcp.json, and tools.py files.
    """
    agent_key = None
    agent_dir = None

    try:
        # Generate agent key if not provided
        agent_key = request.key or request.name.lower().replace(' ', '_').replace('-', '_')

        # Remove non-alphanumeric characters except underscores
        import re
        agent_key = re.sub(r'[^a-zA-Z0-9_]', '', agent_key)

        # Step 1: Validate Agent Configuration
        validation_result = AgentValidator.validate_agent_config(
            name=request.name,
            description=request.description,
            emoji=request.emoji,
            tools_code=request.tools_code,
            mcp_config=request.mcp_config,
            agent_key=agent_key
        )

        if not validation_result.valid:
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

        # Create agent.yaml
        agent_yaml = {
            "name": request.name,
            "description": request.description,
            "emoji": request.emoji
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

        return {
            "message": f"Agent '{request.name}' created successfully",
            "agent_key": agent_key,
            "agent_dir": agent_dir,
            "validation_passed": True
        }

    except HTTPException:
        raise
    except Exception as e:
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
        updated_tools_code = request.tools_code if request.tools_code is not None else None
        updated_mcp_config = request.mcp_config if request.mcp_config is not None else None

        # Step 1: Validate Updated Agent Configuration
        validation_result = AgentValidator.validate_agent_config(
            name=updated_name,
            description=updated_description,
            emoji=updated_emoji,
            tools_code=updated_tools_code,
            mcp_config=updated_mcp_config,
            agent_key=agent_key
        )

        if not validation_result.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Agent configuration validation failed",
                    "validation_errors": validation_result.to_dict()
                }
            )

        # Step 2: Update Files
        # Update agent.yaml
        if request.name is not None:
            current_yaml['name'] = request.name
        if request.description is not None:
            current_yaml['description'] = request.description
        if request.emoji is not None:
            current_yaml['emoji'] = request.emoji

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
            "message": f"Agent '{agent_key}' updated successfully",
            "agent_key": agent_key,
            "validation_passed": True
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


@router.get("/{agent_key}/config/")
async def get_agent_config(
    agent_key: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get the full configuration of an agent including tools and MCP settings.
    """
    try:
        # Verify agent exists
        agents = service.list_available_agents()
        if agent_key not in agents:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found")

        agent_spec = agents[agent_key]
        agent_dir = agent_spec.folder

        config = {
            "key": agent_spec.key,
            "name": agent_spec.name,
            "description": agent_spec.description,
            "emoji": agent_spec.emoji,
            "folder": agent_spec.folder
        }

        # Load tools.py content
        tools_path = os.path.join(agent_dir, "tools.py")
        if os.path.exists(tools_path):
            with open(tools_path, 'r') as f:
                config['tools_code'] = f.read()

        # Load mcp.json content
        mcp_path = os.path.join(agent_dir, "mcp.json")
        if os.path.exists(mcp_path):
            with open(mcp_path, 'r') as f:
                config['mcp_config'] = json.load(f)

        return config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent config: {str(e)}")


@router.get("/status/")
async def get_agents_status(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get comprehensive status of the agent system.

    Returns detailed information about the agent system status.
    """
    try:
        return service.get_service_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents status: {str(e)}")