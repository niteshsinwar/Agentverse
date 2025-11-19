#!/usr/bin/env python3

"""
Professional FastAPI Server Entry Point
Agentverse Backend

This is the main application entry point following FastAPI best practices:
- Clean separation of concerns
- Professional error handling
- Proper dependency injection
- Scalable architecture
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path for clean imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from src.api.v1 import router as api_v1_router
from src.core.config.settings import get_settings
from src.services.orchestrator_service import OrchestratorService
from src.api.v1.dependencies import set_orchestrator_service
from src.core.validation.startup_validator import validate_startup
from src.core.telemetry.session_logger import session_logger, EventType, LogLevel

# Cloud integration imports
from src.api.cloud_client import (
    CloudConfig, initialize_cloud_client, shutdown_cloud_client, get_cloud_client
)
from src.core.cache import initialize_cloud_cache, shutdown_cloud_cache, get_cloud_cache

# Global services (properly managed through dependency injection)
orchestrator_service: OrchestratorService = None
config_watcher = None  # File watcher for hot-reload

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    global orchestrator_service, config_watcher

    print("🚀 Backend Server: Starting up...")

    try:
        # 🔍 COMPREHENSIVE STARTUP VALIDATION
        print("🔍 Running comprehensive startup validation...")
        project_root = Path(__file__).parent

        if not validate_startup(project_root):
            print("🚫 Startup validation failed - blocking server start")
            session_logger.log_event(
                session_id="startup",
                event_type=EventType.ERROR_OCCURRED,
                level=LogLevel.CRITICAL,
                message="Startup validation failed - server blocked"
            )
            raise RuntimeError("Startup validation failed")

        print("✅ Startup validation passed")
        session_logger.log_event(
            session_id="startup",
            event_type=EventType.SYSTEM_EVENT,
            level=LogLevel.INFO,
            message="Startup validation completed successfully"
        )

        # Initialize cloud integration (if enabled)
        settings = get_settings()
        if settings.cloud_enabled:
            print("☁️  Cloud integration enabled - initializing...")

            try:
                # Initialize cloud API client
                cloud_config = CloudConfig(
                    base_url=settings.cloud_base_url,
                    api_version=settings.cloud_api_version,
                    timeout=settings.cloud_timeout,
                    max_retries=settings.cloud_max_retries
                )
                initialize_cloud_client(cloud_config)
                print(f"✅ Cloud client initialized: {settings.cloud_base_url}")

                # Initialize local cache
                await initialize_cloud_cache(
                    cache_dir=settings.cache_dir,
                    ttl=settings.cache_ttl
                )
                print(f"✅ Local cache initialized: {settings.cache_dir}")

                # Sync tenant data from cloud (if token available)
                if settings.cloud_token:
                    print("🔄 Syncing tenant data from cloud...")
                    cloud_client = get_cloud_client()
                    cloud_cache = get_cloud_cache()

                    # Set token
                    from src.api.cloud_client import AuthToken
                    from datetime import datetime, timedelta
                    cloud_client.token = AuthToken(
                        access_token=settings.cloud_token,
                        refresh_token="",  # Will be set after login
                        expires_at=datetime.utcnow() + timedelta(hours=24)
                    )

                    # Sync data
                    await cloud_cache.sync_from_cloud(cloud_client)
                    print("✅ Cloud data synced successfully")
                else:
                    print("⚠️  No cloud token - skipping data sync (login required)")

            except Exception as e:
                print(f"⚠️  Cloud initialization failed: {e}")
                print("   Continuing without cloud integration...")
                # Don't fail startup if cloud is unavailable
        else:
            print("ℹ️  Cloud integration disabled (cloud_enabled=False)")

        # Initialize core services
        orchestrator_service = OrchestratorService()
        await orchestrator_service.initialize()

        # Set up dependency injection
        set_orchestrator_service(orchestrator_service)

        agents_count = len(orchestrator_service.list_available_agents())
        print(f"✅ Backend Server: Initialized with {agents_count} agents")

        # Check API keys
        settings = get_settings()
        api_status = {
            'OPENAI_API_KEY': '✅' if settings.openai_api_key else '❌',
            'GEMINI_API_KEY': '✅' if settings.gemini_api_key else '❌',
            'ANTHROPIC_API_KEY': '✅' if settings.anthropic_api_key else '❌',
            'GITHUB_TOKEN': '✅' if settings.github_token else '❌'
        }
        print(f"🔑 API Keys: {api_status}")

        # Start configuration file watcher for hot-reload
        try:
            from src.core.config.file_watcher import start_config_watcher
            config_watcher = start_config_watcher(
                Path(__file__).parent,
                {
                    'config/settings.json': orchestrator_service.reload_settings,
                    'config/tools.json': orchestrator_service.reload_tools,
                    'config/mcp.json': orchestrator_service.reload_mcp,
                    'agent_store': orchestrator_service.refresh_agents
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to start config watcher (hot-reload disabled): {e}")

    except Exception as e:
        print(f"❌ Backend Server: Startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield

    # Shutdown
    print("🛑 Backend Server: Shutting down...")

    # Stop config watcher
    if config_watcher:
        try:
            from src.core.config.file_watcher import stop_config_watcher
            stop_config_watcher(config_watcher)
        except Exception as e:
            print(f"⚠️ Failed to stop config watcher: {e}")

    # Cleanup orchestrator
    if orchestrator_service:
        await orchestrator_service.cleanup()
    orchestrator_service = None

    # Shutdown cloud integration
    settings = get_settings()
    if settings.cloud_enabled:
        try:
            shutdown_cloud_cache()
            await shutdown_cloud_client()
            print("✅ Cloud integration shut down")
        except Exception as e:
            print(f"⚠️ Failed to shutdown cloud integration: {e}")


def create_app() -> FastAPI:
    """Application factory pattern"""
    settings = get_settings()

    app = FastAPI(
        title="Agentverse API",
        description="Professional REST API for the Agentverse - your multiverse of intelligent agents",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(
        api_v1_router,
        prefix="/api/v1"
    )

    return app


def get_orchestrator_service() -> OrchestratorService:
    """Dependency injection for orchestrator service"""
    return orchestrator_service


# Create application instance
app = create_app()


@app.get("/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "service": "agentverse-backend",
        "version": "1.0.0",
        "orchestrator_ready": orchestrator_service is not None
    }


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Only for development - watches source code
        reload_excludes=[
            # Exclude user config files - these use hot-reload via file watcher
            "*/config/settings.json",
            "*/config/tools.json",
            "*/config/mcp.json",
            "*/agent_store",
            "*/agent_store/*",
            "*/agent_store/**/*",
            # Exclude data and log files
            "*/data",
            "*/data/*",
            "*/logs",
            "*/logs/*",
            "*/documents",
            "*/documents/*",
            "*.db",
            "*.db-journal"
        ],
        access_log=True
    )