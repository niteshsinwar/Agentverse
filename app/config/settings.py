# =========================================
# File: app/config/settings.py
# Purpose: Production-grade centralized configuration management
# =========================================
from __future__ import annotations
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "data/app.db"
    journal_mode: str = "WAL"
    timeout: int = 30
    
    @property
    def full_path(self) -> str:
        """Get absolute database path"""
        return os.path.abspath(self.path)

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout: float = 30.0
    fallback_provider: Optional[str] = None

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    session_logs_dir: str = "logs/sessions"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_file_logging: bool = True
    enable_console_logging: bool = True

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 6360
    workers: int = 1
    reload: bool = False
    debug: bool = False

@dataclass
class MCPConfig:
    """MCP servers configuration"""
    timeout: float = 30.0
    max_retries: int = 3
    enable_health_checks: bool = True
    health_check_interval: int = 300  # 5 minutes

@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_cors: bool = True
    allowed_origins: list = field(default_factory=lambda: ["*"])
    enable_api_key_auth: bool = False
    api_key_header: str = "X-API-Key"
    session_timeout: int = 3600  # 1 hour

@dataclass
class PathsConfig:
    """Path configuration"""
    workspace: str = "./workspace"
    logs: str = "./logs"
    sessions: str = "./sessions"
    documents: str = "./documents"
    
    def __post_init__(self):
        """Create directories if they don't exist"""
        for path in [self.workspace, self.logs, self.sessions, self.documents]:
            Path(path).mkdir(parents=True, exist_ok=True)

class Settings:
    """Production-grade centralized configuration management"""
    
    def __init__(self, config_file: Optional[str] = None) -> None:
        # Do not use a default config.yaml; rely on app/config and env by default
        self.config_file = config_file if config_file is not None else os.environ.get("APP_CONFIG_FILE")
        self._raw_config = self._load_yaml(self.config_file)
        
        # Initialize configuration sections
        self._init_app_config()
        self._init_database_config()
        self._init_llm_config()
        self._init_logging_config()
        self._init_server_config()
        self._init_mcp_config()
        self._init_security_config()
        self._init_paths_config()
        self._load_secrets()
        
        # Validate configuration
        self._validate_config()
    
    def _init_app_config(self):
        """Initialize application configuration"""
        app_config = self._get(["app"], {})
        self.APP_NAME = app_config.get("name", "Agentic Multi-Agent Framework")
        self.APP_VERSION = app_config.get("version", "1.0.0")
        self.APP_ENV = Environment(app_config.get("env", "development"))
        self.APP_DEBUG = app_config.get("debug", self.APP_ENV == Environment.DEVELOPMENT)
        self.BASE_URL = app_config.get("base_url", "http://localhost:6360")
    
    def _init_database_config(self):
        """Initialize database configuration"""
        db_config = self._get(["database"], {})
        self.database = DatabaseConfig(
            path=db_config.get("path", "data/app.db"),
            journal_mode=db_config.get("journal_mode", "WAL"),
            timeout=db_config.get("timeout", 30)
        )
        
        # Backward compatibility
        self.DB_PATH = self.database.full_path
    
    def _init_llm_config(self):
        """Initialize LLM configuration"""
        llm_config = self._get(["llm"], {})
        self.llm = LLMConfig(
            provider=llm_config.get("provider", "openai"),
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=float(llm_config.get("temperature", 0.2)),
            max_tokens=int(llm_config.get("max_tokens", 4096)),
            timeout=float(llm_config.get("timeout", 30.0)),
            fallback_provider=llm_config.get("fallback_provider")
        )
        
        # Backward compatibility
        self.LLM_PROVIDER = self.llm.provider
        self.LLM_MODEL = self.llm.model
        self.LLM_TEMPERATURE = self.llm.temperature
        self.LLM_MAX_TOKENS = self.llm.max_tokens
    
    def _init_logging_config(self):
        """Initialize logging configuration"""
        logging_config = self._get(["logging"], {})
        self.logging = LoggingConfig(
            level=logging_config.get("level", "INFO"),
            format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            session_logs_dir=logging_config.get("session_logs_dir", "logs/sessions"),
            max_file_size=logging_config.get("max_file_size", 10 * 1024 * 1024),
            backup_count=logging_config.get("backup_count", 5),
            enable_file_logging=logging_config.get("enable_file_logging", True),
            enable_console_logging=logging_config.get("enable_console_logging", True)
        )
    
    def _init_server_config(self):
        """Initialize server configuration"""
        server_config = self._get(["server"], {})
        self.server = ServerConfig(
            host=server_config.get("host", "0.0.0.0"),
            port=int(server_config.get("port", 6360)),
            workers=int(server_config.get("workers", 1)),
            reload=server_config.get("reload", self.APP_ENV == Environment.DEVELOPMENT),
            debug=server_config.get("debug", self.APP_DEBUG)
        )
    
    def _init_mcp_config(self):
        """Initialize MCP configuration"""
        mcp_config = self._get(["mcp"], {})
        self.mcp = MCPConfig(
            timeout=float(mcp_config.get("timeout", 30.0)),
            max_retries=int(mcp_config.get("max_retries", 3)),
            enable_health_checks=mcp_config.get("enable_health_checks", True),
            health_check_interval=int(mcp_config.get("health_check_interval", 300))
        )
    
    def _init_security_config(self):
        """Initialize security configuration"""
        security_config = self._get(["security"], {})
        self.security = SecurityConfig(
            enable_cors=security_config.get("enable_cors", True),
            allowed_origins=security_config.get("allowed_origins", ["*"]),
            enable_api_key_auth=security_config.get("enable_api_key_auth", False),
            api_key_header=security_config.get("api_key_header", "X-API-Key"),
            session_timeout=int(security_config.get("session_timeout", 3600))
        )
    
    def _init_paths_config(self):
        """Initialize paths configuration"""
        paths_config = self._get(["paths"], {})
        self.paths = PathsConfig(
            workspace=paths_config.get("workspace", "./workspace"),
            logs=paths_config.get("logs", "./logs"),
            sessions=paths_config.get("sessions", "./sessions"),
            documents=paths_config.get("documents", "./documents")
        )
        
        # Backward compatibility
        self.PATHS = {
            "workspace": self.paths.workspace,
            "logs": self.paths.logs,
            "sessions": self.paths.sessions,
            "documents": self.paths.documents
        }
    
    def _load_secrets(self):
        """Load secrets from environment variables"""
        # LLM API Keys
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        self.CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")  # Alternative name
        
        # Service tokens
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        
        # Application secrets
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        self.API_KEY = os.getenv("API_KEY")
    
    def _validate_config(self):
        """Validate configuration for common issues"""
        warnings = []
        errors = []
        
        # Check for required API keys based on LLM provider (relax in development/testing)
        if self.APP_ENV in (Environment.PRODUCTION, Environment.STAGING):
            if self.llm.provider == "openai" and not self.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY environment variable required for OpenAI provider")
            elif self.llm.provider == "gemini" and not self.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY environment variable required for Gemini provider")
            elif self.llm.provider == "claude" and not (self.ANTHROPIC_API_KEY or self.CLAUDE_API_KEY):
                errors.append("ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable required for Claude provider")
        
        # Check production settings
        if self.APP_ENV == Environment.PRODUCTION:
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                warnings.append("Using default SECRET_KEY in production")
            if self.APP_DEBUG:
                warnings.append("Debug mode enabled in production")
        
        # Log warnings and raise errors
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
        
        if errors:
            error_msg = "Configuration errors:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ValueError(error_msg)
    
    def _load_yaml(self, path: Optional[str]) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not path:
            # No external config file specified; use defaults and env
            return {}
        config_path = Path(path)
        if not config_path.exists():
            # Silently ignore missing file when not explicitly required
            return {}
        
        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {path}")
                return config
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config file {path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading config file {path}: {e}")
            return {}
    
    def _get(self, keys: list[str], default: Any = None) -> Any:
        """Get nested configuration value"""
        current = self._raw_config
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for a specific provider"""
        provider = provider or self.llm.provider
        
        base_config = {
            "provider": provider,
            "model": self.llm.model,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "timeout": self.llm.timeout
        }
        
        # Add provider-specific API key
        if provider == "openai":
            base_config["api_key"] = self.OPENAI_API_KEY
        elif provider == "gemini":
            base_config["api_key"] = self.GEMINI_API_KEY
        elif provider == "claude":
            base_config["api_key"] = self.ANTHROPIC_API_KEY or self.CLAUDE_API_KEY
        
        return base_config
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            "app": {
                "name": self.APP_NAME,
                "version": self.APP_VERSION,
                "env": self.APP_ENV.value,
                "debug": self.APP_DEBUG,
                "base_url": self.BASE_URL
            },
            "database": {
                "path": self.database.path,
                "journal_mode": self.database.journal_mode,
                "timeout": self.database.timeout
            },
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                "fallback_provider": self.llm.fallback_provider
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
                "reload": self.server.reload,
                "debug": self.server.debug
            },
            "logging": {
                "level": self.logging.level,
                "session_logs_dir": self.logging.session_logs_dir,
                "enable_file_logging": self.logging.enable_file_logging
            },
            "paths": {
                "workspace": self.paths.workspace,
                "logs": self.paths.logs,
                "sessions": self.paths.sessions,
                "documents": self.paths.documents
            }
        }
    
    def reload(self):
        """Reload configuration from file"""
        self.__init__(self.config_file)
        logger.info("Configuration reloaded")

# Global settings instance
settings = Settings()
