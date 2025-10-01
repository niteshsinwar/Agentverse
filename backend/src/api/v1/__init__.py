"""
API v1 Router
Consolidates all API endpoints for version 1
"""

from fastapi import APIRouter

from .endpoints import groups, agents, chat, logs, tools, mcp, settings, validation

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
    logs.router,
    prefix="/logs",
    tags=["logs"]
)

# Configuration Management (split from config.py)
router.include_router(
    tools.router,
    prefix="/config/tools",
    tags=["tools"]
)

router.include_router(
    mcp.router,
    prefix="/config/mcp",
    tags=["mcp"]
)

router.include_router(
    settings.router,
    prefix="/config/settings",
    tags=["settings"]
)

router.include_router(
    validation.router,
    prefix="/config/validate",
    tags=["validation"]
)
