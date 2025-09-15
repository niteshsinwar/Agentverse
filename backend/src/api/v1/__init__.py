"""
API v1 Router
Consolidates all API endpoints for version 1
"""

from fastapi import APIRouter

from .endpoints import groups, agents, chat, analytics, project, config

# Create the main API router
router = APIRouter()

# Include endpoint routers
router.include_router(
    groups.router,
    prefix="/groups",
    tags=["groups"]
)

router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"]
)

router.include_router(
    chat.router,
    tags=["chat"]
)

router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

router.include_router(
    project.router,
    prefix="/project",
    tags=["project"]
)

router.include_router(
    config.router,
    prefix="/config",
    tags=["config"]
)
