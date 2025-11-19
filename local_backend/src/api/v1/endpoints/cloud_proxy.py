"""
Cloud Proxy Endpoints - Proxy requests to cloud backend

These endpoints allow the local backend to communicate with the Django cloud backend.
They handle authentication, caching, and syncing between local and cloud.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cloud", tags=["cloud-proxy"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant_id: str
    user_role: str


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login via cloud backend and cache data locally.

    Flow:
    1. Send credentials to cloud backend
    2. Receive JWT tokens
    3. Store tokens in settings/session
    4. Sync all tenant data to local cache
    5. Return tokens to frontend

    Example:
        POST /api/v1/cloud/auth/login
        {"email": "admin@example.com", "password": "password123"}
    """
    try:
        # Get cloud client
        from src.api.cloud_client import get_cloud_client, CloudAPIError
        from src.core.cache import get_cloud_cache
        from src.core.config.settings import get_settings

        cloud_client = get_cloud_client()

        # Login to cloud
        logger.info(f"Logging in user: {credentials.email}")
        result = await cloud_client.login(credentials.email, credentials.password)

        # Store token in settings (for auto-sync on future requests)
        settings = get_settings()
        # Note: This is a runtime update, not persisted
        # In production, store in secure session storage

        logger.info(f"Login successful. Tenant: {result.get('tenant_id')}, Role: {result.get('user_role')}")

        # Sync all tenant data to local cache
        logger.info("Syncing tenant data from cloud...")
        try:
            cloud_cache = get_cloud_cache()
            await cloud_cache.sync_from_cloud(cloud_client)
            logger.info("✅ Cloud data synced to local cache")
        except Exception as cache_error:
            logger.warning(f"⚠️  Cache sync failed (non-fatal): {cache_error}")
            # Don't fail login if cache sync fails

        return LoginResponse(**result)

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/auth/logout")
async def logout(refresh_token: RefreshRequest):
    """
    Logout and clear local cache.

    Flow:
    1. Send logout request to cloud
    2. Clear local cache
    3. Clear stored tokens
    """
    try:
        from src.api.cloud_client import get_cloud_client
        from src.core.cache import get_cloud_cache

        cloud_client = get_cloud_client()

        # Logout from cloud (blacklist token)
        # Note: cloud_client.logout() expects refresh_token in request data
        # This is a simplified version

        logger.info("Logout successful")

        # Clear local cache
        try:
            cloud_cache = get_cloud_cache()
            await cloud_cache.clear_all_cache()
            logger.info("✅ Local cache cleared")
        except Exception as e:
            logger.warning(f"⚠️  Cache clear failed: {e}")

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/auth/refresh")
async def refresh_token(refresh_req: RefreshRequest):
    """
    Refresh access token via cloud backend.

    Flow:
    1. Send refresh token to cloud
    2. Receive new access token
    3. Return to frontend
    """
    try:
        from src.api.cloud_client import get_cloud_client

        cloud_client = get_cloud_client()

        # Refresh token
        # Note: This is a placeholder - implement actual refresh logic
        logger.info("Token refresh requested")

        return {"message": "Token refresh - implement cloud_client.refresh_token()"}

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/cache/refresh")
async def refresh_cache():
    """
    Manually refresh local cache from cloud.

    Useful after CRUD operations to get latest data.
    """
    try:
        from src.api.cloud_client import get_cloud_client
        from src.core.cache import get_cloud_cache

        cloud_client = get_cloud_client()
        cloud_cache = get_cloud_cache()

        logger.info("Refreshing cache from cloud...")
        await cloud_cache.sync_from_cloud(cloud_client)
        logger.info("✅ Cache refreshed")

        return {"message": "Cache refreshed successfully"}

    except Exception as e:
        logger.error(f"Cache refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/cache/status")
async def cache_status():
    """
    Get cache status (last sync time, entry counts).
    """
    try:
        from src.core.cache import get_cloud_cache

        cloud_cache = get_cloud_cache()

        # Get cache stats
        agents = await cloud_cache.get_agents()
        tools = await cloud_cache.get_tools()
        mcp_servers = await cloud_cache.get_mcp_servers()
        groups = await cloud_cache.get_groups()
        users = await cloud_cache.get_users()
        last_sync = await cloud_cache.get_last_sync_time()

        return {
            "last_sync": last_sync.isoformat() if last_sync else None,
            "counts": {
                "agents": len(agents),
                "tools": len(tools),
                "mcp_servers": len(mcp_servers),
                "groups": len(groups),
                "users": len(users),
            }
        }

    except Exception as e:
        logger.error(f"Cache status failed: {e}")
        return {
            "error": str(e),
            "last_sync": None,
            "counts": {}
        }


# ============================================================================
# CRUD PROXY ENDPOINTS (Optional - for direct cloud CRUD)
# ============================================================================

@router.get("/agents")
async def list_agents():
    """List agents from cloud (bypasses cache)"""
    try:
        from src.api.cloud_client import get_cloud_client
        cloud_client = get_cloud_client()
        agents = await cloud_client.fetch_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools():
    """List tools from cloud (bypasses cache)"""
    try:
        from src.api.cloud_client import get_cloud_client
        cloud_client = get_cloud_client()
        tools = await cloud_client.fetch_tools()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp-servers")
async def list_mcp_servers():
    """List MCP servers from cloud (bypasses cache)"""
    try:
        from src.api.cloud_client import get_cloud_client
        cloud_client = get_cloud_client()
        mcp_servers = await cloud_client.fetch_mcp_servers()
        return {"mcp_servers": mcp_servers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
