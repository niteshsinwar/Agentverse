"""
Application Settings and Configuration
Professional Pydantic-based configuration management following best practices
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
from functools import lru_cache
from enum import Enum
from pydantic import BaseModel


class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DocumentExtractionSettings(BaseModel):
    """Document extraction configuration"""
    enabled: bool = True
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    max_file_size_mb: int = 15
    ai_analysis_enabled: bool = True
    generate_summary: bool = True
    supported_formats: List[str] = [
        "txt", "csv", "pdf", "docx", "pptx", "jpg", "jpeg", "png", "gif",
        "json", "md", "xlsx", "xls", "rtf", "odt", "odp", "ods",
        "bmp", "tiff", "webp", "svg", "xml", "html", "htm"
    ]


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    This follows industry best practices:
    - Type-safe configuration using Pydantic
    - Environment variable support with .env files
    - Clear documentation for each setting
    - Validation and default values
    """

    # Application Core Settings
    app_name: str = "Agentverse Backend"
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: List[str] = [
        "http://localhost:1420",
        "https://tauri.localhost"
    ]

    # LLM Provider API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    github_token: Optional[str] = None

    # Database Configuration
    database_url: str = "sqlite:///./data/app.db"

    # Document Processing
    max_upload_size_mb: int = 10
    supported_file_formats: List[str] = [
        "txt", "csv", "json", "pdf", "docx", "md","png"
    ]

    # Agent Configuration
    max_agent_iterations: int = 5
    default_temperature: float = 0.2
    default_max_tokens: int = 4096

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: Optional[str] = None
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096
    llm_fallback_provider: Optional[str] = None

    # Security Settings
    secret_key: str = "dev-key-change-in-production"
    session_timeout_hours: int = 24

    # Logging Configuration
    log_level: str = "INFO"
    enable_file_logging: bool = True
    log_file_max_size_mb: int = 10

    # Document Extraction Configuration
    document_extraction: DocumentExtractionSettings = DocumentExtractionSettings()

    # Legacy support for old settings format
    @property
    def logging(self):
        """Backward compatibility for old logging settings"""
        from types import SimpleNamespace
        return SimpleNamespace(
            level=self.log_level,
            session_logs_dir="logs/sessions",
            enable_console_logging=True,
            enable_file_logging=self.enable_file_logging,
            max_file_size=self.log_file_max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backup_count=5
        )

    # Legacy support for old PATHS format
    @property
    def PATHS(self):
        """Backward compatibility for old PATHS settings"""
        return {
            "workspace": "./workspace",
            "logs": "./logs",
            "sessions": "./sessions",
            "documents": "./documents"
        }

    # Legacy support for old MCP format
    @property
    def mcp(self):
        """Backward compatibility for old MCP settings"""
        from types import SimpleNamespace
        return SimpleNamespace(
            timeout=30.0,
            max_retries=3,
            health_check_interval=60.0,
            enable_health_checks=True,
            buffer_size_mb=1,  # 1MB buffer size for large JSON responses
            max_message_size_mb=10  # 10MB max message size limit
        )

    # Legacy support for old LLM format
    @property
    def llm(self):
        """Backward compatibility for old LLM settings"""
        from types import SimpleNamespace
        return SimpleNamespace(
            provider=self.llm_provider,
            model=self.llm_model,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
            fallback_provider=self.llm_fallback_provider
        )

    # Development/Testing Flags
    enable_api_docs: bool = True
    enable_cors: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown environment variables
    )

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

    def get_database_path(self) -> str:
        """Get the database file path"""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return "data/app.db"

    def validate_api_keys(self) -> dict:
        """Validate and return API key status"""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "gemini": bool(self.gemini_api_key),
            "github": bool(self.github_token)
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with JSON override support.

    This function loads base settings from environment and .env files,
    then applies any overrides from config/settings.json if it exists.

    Using lru_cache ensures the settings are loaded once and reused
    throughout the application lifecycle for better performance.
    """
    import json
    import os
    from pathlib import Path

    # Load base settings from environment and .env
    base_settings = Settings()

    # Check for JSON overrides
    settings_override_path = Path("config/settings.json")
    if settings_override_path.exists():
        try:
            with open(settings_override_path, 'r') as f:
                overrides = json.load(f)

            # Create a new settings instance with overrides
            # We need to merge the overrides with the base settings
            settings_dict = {}

            # Get all field values from base settings
            for field_name in base_settings.__fields__:
                settings_dict[field_name] = getattr(base_settings, field_name)

            # Apply overrides
            for key, value in overrides.items():
                if key in base_settings.__fields__:
                    settings_dict[key] = value

            # Create new settings instance with merged values
            return Settings(**settings_dict)

        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"Warning: Failed to load settings overrides: {e}")
            return base_settings

    return base_settings


def refresh_settings():
    """
    Refresh the settings cache.

    This function clears the LRU cache for get_settings(),
    forcing it to reload settings from files on next access.
    Useful when settings.json has been updated via API.
    """
    get_settings.cache_clear()
