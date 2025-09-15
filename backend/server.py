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

# Global services (properly managed through dependency injection)
orchestrator_service: OrchestratorService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    global orchestrator_service

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

    except Exception as e:
        print(f"❌ Backend Server: Startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield

    # Shutdown
    print("🛑 Backend Server: Shutting down...")
    if orchestrator_service:
        await orchestrator_service.cleanup()
    orchestrator_service = None


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
        reload=True,  # Only for development
        access_log=True
    )