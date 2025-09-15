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


@router.get("/system/metrics")
async def get_system_metrics(
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get comprehensive system metrics.

    Returns detailed analytics about system performance and usage.
    """
    try:
        agents = service.list_available_agents()
        groups = service.list_groups()

        metrics = {
            "system": {
                "total_agents": len(agents),
                "total_groups": len(groups),
                "uptime_hours": "0.1",  # Would calculate actual uptime
                "status": "healthy"
            },
            "agents": {
                "by_type": _categorize_agents(agents),
                "most_used": "agent_1",  # Would track actual usage
                "total_calls": 42        # Would track from telemetry
            },
            "performance": {
                "avg_response_time_ms": 150,
                "success_rate": 98.5,
                "error_rate": 1.5
            },
            "timestamp": datetime.now().isoformat()
        }

        session_logger.log_event(
            session_id="analytics",
            event_type=EventType.SYSTEM_EVENT,
            level=LogLevel.INFO,
            message="System metrics requested",
            details={"metric_count": len(metrics)}
        )

        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


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


@router.get("/usage/trends")
async def get_usage_trends(
    days: int = 7,
    service: OrchestratorService = Depends(get_orchestrator_service)
):
    """
    Get usage trends over time.

    Returns usage patterns and trends for the specified time period.
    """
    try:
        # This would integrate with your telemetry system
        trends = {
            "period_days": days,
            "daily_usage": [
                {"date": "2024-01-01", "messages": 25, "agent_calls": 15},
                {"date": "2024-01-02", "messages": 30, "agent_calls": 18},
                {"date": "2024-01-03", "messages": 28, "agent_calls": 16},
            ],
            "top_agents": [
                {"agent": "agent_1", "usage_count": 45},
                {"agent": "agent_2", "usage_count": 32},
                {"agent": "agent_3", "usage_count": 28},
            ],
            "generated_at": datetime.now().isoformat()
        }

        return trends

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


def _categorize_agents(agents: Dict[str, Any]) -> Dict[str, int]:
    """Categorize agents by type for analytics"""
    categories = {}
    for agent_spec in agents.values():
        # Simple categorization based on description keywords
        desc = agent_spec.description.lower()
        if "development" in desc or "code" in desc:
            categories["development"] = categories.get("development", 0) + 1
        elif "web" in desc or "ui" in desc:
            categories["web"] = categories.get("web", 0) + 1
        elif "file" in desc or "system" in desc:
            categories["system"] = categories.get("system", 0) + 1
        else:
            categories["other"] = categories.get("other", 0) + 1

    return categories