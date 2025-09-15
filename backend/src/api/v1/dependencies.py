"""
FastAPI Dependencies
Dependency injection for API endpoints
"""

from fastapi import HTTPException

from src.services.orchestrator_service import OrchestratorService

# Global service instance (managed by server.py)
_orchestrator_service: OrchestratorService = None


def set_orchestrator_service(service: OrchestratorService) -> None:
    """Set the global orchestrator service instance"""
    global _orchestrator_service
    _orchestrator_service = service


def get_orchestrator_service() -> OrchestratorService:
    """
    Dependency to get the orchestrator service.

    This is used by FastAPI's dependency injection system to provide
    the service instance to API endpoints.
    """
    if _orchestrator_service is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized"
        )

    if not _orchestrator_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )

    return _orchestrator_service