"""
Groups API Endpoints
RESTful endpoints for group management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import os

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.models.groups import (
    GroupResponse,
    CreateGroupRequest,
    AddAgentRequest
)
from src.api.v1.dependencies import get_orchestrator_service

router = APIRouter()


@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    List all groups.

    Returns a list of all conversation groups with their metadata.
    """
    try:
        groups = service.list_groups()
        return [
            GroupResponse(
                id=group["id"],
                name=group["name"],
                created_at=group["created_at"],
                updated_at=group["updated_at"]
            )
            for group in groups
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list groups: {str(e)}")


@router.post("/", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Create a new group.

    Creates a new conversation group with the specified name.
    """
    try:
        group_id = service.create_group(request.name)

        # Get the created group
        groups = service.list_groups()
        group = next((g for g in groups if g["id"] == group_id), None)

        if not group:
            raise HTTPException(status_code=500, detail="Failed to retrieve created group")

        return GroupResponse(
            id=group["id"],
            name=group["name"],
            created_at=group["created_at"],
            updated_at=group["updated_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Delete a group.

    Permanently deletes a group and all its associated data.
    """
    try:
        service.delete_group(group_id)
        return {"message": f"Group {group_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete group: {str(e)}")


@router.get("/{group_id}/agents")
async def list_group_agents(
    group_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    List agents in a group.

    Returns all agents currently assigned to the specified group.
    """
    try:
        agent_keys = service.list_group_agents(group_id)
        available_agents = service.list_available_agents()

        # Return detailed agent information
        agents = []
        for key in agent_keys:
            if key in available_agents:
                spec = available_agents[key]
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

                agents.append(agent_data)

        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list group agents: {str(e)}")


@router.post("/{group_id}/agents")
async def add_agent_to_group(
    group_id: str,
    request: AddAgentRequest,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Add an agent to a group.

    Assigns an agent to a group for participation in conversations.
    """
    try:
        service.add_agent_to_group(group_id, request.agent_key)
        return {"message": f"Agent {request.agent_key} added to group {group_id}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add agent to group: {str(e)}")


@router.delete("/{group_id}/agents/{agent_key}")
async def remove_agent_from_group(
    group_id: str,
    agent_key: str,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Remove an agent from a group.

    Removes an agent from a group, preventing further participation.
    """
    try:
        service.remove_agent_from_group(group_id, agent_key)
        return {"message": f"Agent {agent_key} removed from group {group_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove agent from group: {str(e)}")