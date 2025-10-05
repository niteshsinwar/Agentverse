"""
Cross-Platform Path Handling

WHY: Windows uses backslashes, Mac uses forward slashes
WHAT: Unified path handling with pathlib.Path
HOW: Path objects work identically on all platforms
"""

from pathlib import Path
from typing import Union
import os


class CrossPlatformPaths:
    """
    Unified path handling for Windows/Mac.

    ALWAYS use pathlib.Path, NEVER string concatenation!
    """

    # Base directories (relative to backend root)
    AGENT_STORE = Path("agent_store")
    CONFIG_DIR = Path("config")
    DOCUMENTS_DIR = Path("documents")
    DATA_DIR = Path("data")
    LOGS_DIR = Path("logs")

    @staticmethod
    def get_agent_path(agent_key: str) -> Path:
        """
        Get agent directory path.

        WHY: Centralized agent path logic
        WHAT: Returns Path to agent_store/{agent_key}
        HOW: Path concatenation (works on Windows + Mac)

        Args:
            agent_key: Agent identifier

        Returns:
            Path to agent directory
        """
        return CrossPlatformPaths.AGENT_STORE / agent_key

    @staticmethod
    def get_agent_yaml(agent_key: str) -> Path:
        """Get agent.yaml path."""
        return CrossPlatformPaths.get_agent_path(agent_key) / "agent.yaml"

    @staticmethod
    def get_agent_tools(agent_key: str) -> Path:
        """Get tools.py path."""
        return CrossPlatformPaths.get_agent_path(agent_key) / "tools.py"

    @staticmethod
    def get_agent_mcp(agent_key: str) -> Path:
        """Get mcp.json path."""
        return CrossPlatformPaths.get_agent_path(agent_key) / "mcp.json"

    @staticmethod
    def get_global_tools_config() -> Path:
        """Get global tools.json path."""
        return CrossPlatformPaths.CONFIG_DIR / "tools.json"

    @staticmethod
    def get_global_mcp_config() -> Path:
        """Get global mcp.json path."""
        return CrossPlatformPaths.CONFIG_DIR / "mcp.json"

    @staticmethod
    def get_settings_path() -> Path:
        """Get settings.json path."""
        return CrossPlatformPaths.CONFIG_DIR / "settings.json"

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """
        Create directory if it doesn't exist.

        WHY: Safe directory creation
        WHAT: Create directory with parents
        HOW: mkdir with parents=True, exist_ok=True

        Args:
            path: Directory path (string or Path)

        Returns:
            Path object to directory
        """
        path_obj = Path(path) if isinstance(path, str) else path
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    @staticmethod
    def normalize_path(path_str: str) -> Path:
        """
        Normalize path string to Path object.

        WHY: Handle mixed path separators
        WHAT: Convert string to Path (handles both \\ and /)
        HOW: Path constructor normalizes automatically

        Args:
            path_str: Path as string (any separator)

        Returns:
            Normalized Path object
        """
        return Path(path_str)

    @staticmethod
    def get_absolute_path(path: Union[str, Path]) -> Path:
        """
        Get absolute path.

        WHY: Resolve relative paths to absolute
        WHAT: Convert to absolute path
        HOW: Path.resolve()

        Args:
            path: Relative or absolute path

        Returns:
            Absolute Path object
        """
        path_obj = Path(path) if isinstance(path, str) else path
        return path_obj.resolve()

    @staticmethod
    def path_exists(path: Union[str, Path]) -> bool:
        """Check if path exists."""
        path_obj = Path(path) if isinstance(path, str) else path
        return path_obj.exists()

    @staticmethod
    def is_file(path: Union[str, Path]) -> bool:
        """Check if path is a file."""
        path_obj = Path(path) if isinstance(path, str) else path
        return path_obj.is_file()

    @staticmethod
    def is_directory(path: Union[str, Path]) -> bool:
        """Check if path is a directory."""
        path_obj = Path(path) if isinstance(path, str) else path
        return path_obj.is_dir()
