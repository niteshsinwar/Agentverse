"""
Settings Management API Endpoints
Handle settings.json management via API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
import os
from pathlib import Path

router = APIRouter()

# Configuration file paths
BACKEND_CONFIG_PATH = Path("config")

# Ensure config directories exist
os.makedirs(BACKEND_CONFIG_PATH, exist_ok=True)


# Request models
class SettingsRequest(BaseModel):
    settings: Dict[str, Any]


# Settings Management Endpoints
@router.get("/")
async def get_settings():
    """Get current settings from settings.json (overrides) and default settings"""
    try:
        # Load default settings from Python settings
        from src.core.config.settings import get_settings
        default_settings = get_settings()

        # Convert to dict
        settings_dict = {}
        for field_name, field_info in default_settings.__fields__.items():
            settings_dict[field_name] = getattr(default_settings, field_name)

        # Load overrides from settings.json if exists
        settings_path = BACKEND_CONFIG_PATH / "settings.json"
        overrides = {}
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                overrides = json.load(f)

        # Merge settings
        final_settings = {**settings_dict, **overrides}

        return {
            "settings": final_settings,
            "overrides": overrides,
            "has_overrides": len(overrides) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")


@router.post("/")
async def update_settings(settings_request: SettingsRequest):
    """Update settings by saving to settings.json (overrides default settings.py)"""
    try:
        settings_path = BACKEND_CONFIG_PATH / "settings.json"

        # Load existing overrides
        existing_overrides = {}
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                existing_overrides = json.load(f)

        # Merge with new settings
        updated_overrides = {**existing_overrides, **settings_request.settings}

        # Save overrides to settings.json
        with open(settings_path, 'w') as f:
            json.dump(updated_overrides, f, indent=2)

        # Refresh settings cache to pick up changes
        from src.core.config.settings import refresh_settings
        refresh_settings()

        return {
            "message": "Settings updated successfully",
            "overrides_count": len(updated_overrides),
            "updated_keys": list(settings_request.settings.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.delete("/")
async def reset_settings():
    """Reset settings by removing settings.json overrides"""
    try:
        settings_path = BACKEND_CONFIG_PATH / "settings.json"

        if settings_path.exists():
            os.remove(settings_path)
            # Refresh settings cache to pick up changes
            from src.core.config.settings import refresh_settings
            refresh_settings()
            return {"message": "Settings reset to defaults successfully"}
        else:
            return {"message": "No settings overrides found, already using defaults"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


@router.get("/validate/")
async def validate_settings():
    """Validate current settings configuration"""
    try:
        from src.core.config.settings import get_settings
        settings = get_settings()

        # Basic validation
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }

        # Check API keys
        if not settings.openai_api_key:
            validation_results["warnings"].append("OpenAI API key not configured")
        if not settings.github_token:
            validation_results["warnings"].append("GitHub token not configured")

        # Check database URL
        if not settings.database_url:
            validation_results["errors"].append("Database URL not configured")
            validation_results["valid"] = False

        # Check file size limits
        if settings.max_upload_size_mb <= 0:
            validation_results["errors"].append("Max upload size must be greater than 0")
            validation_results["valid"] = False

        return validation_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate settings: {str(e)}")


# Configuration Status and Backup
@router.post("/backup/")
async def create_backup():
    """Create a backup of current configuration files"""
    try:
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKEND_CONFIG_PATH / f"backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)

        # Backup configuration files
        files_backed_up = []

        # Backup tools.json
        tools_path = BACKEND_CONFIG_PATH / "tools.json"
        if tools_path.exists():
            shutil.copy2(tools_path, backup_dir / "tools.json")
            files_backed_up.append("tools.json")

        # Backup mcp.json
        mcp_path = BACKEND_CONFIG_PATH / "mcp.json"
        if mcp_path.exists():
            shutil.copy2(mcp_path, backup_dir / "mcp.json")
            files_backed_up.append("mcp.json")

        # Backup settings.json
        settings_path = BACKEND_CONFIG_PATH / "settings.json"
        if settings_path.exists():
            shutil.copy2(settings_path, backup_dir / "settings.json")
            files_backed_up.append("settings.json")

        return {
            "message": "Backup created successfully",
            "backup_path": str(backup_dir),
            "timestamp": timestamp,
            "files_backed_up": files_backed_up
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")


@router.get("/status/")
async def get_config_status():
    """Get status of all configuration files"""
    try:
        status = {
            "tools": {
                "exists": (BACKEND_CONFIG_PATH / "tools.json").exists(),
                "path": str(BACKEND_CONFIG_PATH / "tools.json"),
                "count": 0
            },
            "mcp": {
                "exists": (BACKEND_CONFIG_PATH / "mcp.json").exists(),
                "path": str(BACKEND_CONFIG_PATH / "mcp.json"),
                "count": 0
            },
            "settings": {
                "overrides_exist": (BACKEND_CONFIG_PATH / "settings.json").exists(),
                "overrides_path": str(BACKEND_CONFIG_PATH / "settings.json"),
                "overrides_count": 0
            }
        }

        # Count tools
        if status["tools"]["exists"]:
            with open(BACKEND_CONFIG_PATH / "tools.json", 'r') as f:
                tools = json.load(f)
                status["tools"]["count"] = len(tools)

        # Count MCPs
        if status["mcp"]["exists"]:
            with open(BACKEND_CONFIG_PATH / "mcp.json", 'r') as f:
                mcps = json.load(f)
                status["mcp"]["count"] = len(mcps)

        # Count settings overrides
        if status["settings"]["overrides_exist"]:
            with open(BACKEND_CONFIG_PATH / "settings.json", 'r') as f:
                overrides = json.load(f)
                status["settings"]["overrides_count"] = len(overrides)

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config status: {str(e)}")
