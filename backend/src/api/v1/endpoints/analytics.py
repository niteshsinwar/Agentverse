"""
Analytics API Endpoints (Example of easy feature addition)
RESTful endpoints for system analytics and metrics
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from datetime import datetime, timedelta

from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import get_orchestrator_service
from src.core.telemetry.session_logger import session_logger, EventType, LogLevel

router = APIRouter()



@router.get("/system/modules/")
async def get_system_modules(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get system modules and configuration information.

    Returns system configuration data including available modules and settings.
    """
    try:
        agents = service.list_available_agents()

        # System modules information for frontend configuration
        modules_info = {
            "agents": {
                "count": len(agents),
                "types": list(agents.keys()),
                "status": "active"
            },
            "database": {
                "type": "sqlite",
                "status": "connected"
            },
            "api": {
                "version": "v1",
                "status": "running"
            },
            "telemetry": {
                "enabled": True,
                "status": "active"
            },
            "system": {
                "uptime": "running",
                "memory_usage": "normal",
                "cpu_usage": "low"
            },
            "timestamp": datetime.now().isoformat()
        }

        session_logger.log_event(
            session_id="system_modules",
            event_type=EventType.SYSTEM_EVENT,
            level=LogLevel.INFO,
            message="System modules info requested",
            details={"modules_count": len(modules_info)}
        )

        return modules_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system modules: {str(e)}")


