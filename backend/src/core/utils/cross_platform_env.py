"""
Cross-Platform Environment Variable Handling

WHY: Windows and Mac have different env var expansion syntax
WHAT: Unified environment variable handling
HOW: os.path.expandvars with syntax normalization
"""

import os
import re
from typing import Dict, Any


class CrossPlatformEnv:
    """
    Unified environment variable handling.

    Supports both ${VAR} (Unix) and %VAR% (Windows) syntax.
    """

    @staticmethod
    def expand_vars(text: str) -> str:
        """
        Expand environment variables in text.

        WHY: Support both Unix and Windows syntax
        WHAT: Convert %VAR% to ${VAR}, then expand
        HOW: Regex replacement + os.path.expandvars

        Args:
            text: String with environment variables

        Returns:
            String with expanded variables

        Examples:
            "${HOME}/data" → "/Users/name/data" (Mac)
            "%USERPROFILE%\\data" → "C:\\Users\\name\\data" (Windows)
        """
        # Convert Windows %VAR% to Unix ${VAR}
        text = re.sub(r'%(\w+)%', r'${\1}', text)

        # Expand with os.path.expandvars (works everywhere)
        return os.path.expandvars(text)

    @staticmethod
    def get_env(key: str, default: str = None) -> str:
        """
        Get environment variable.

        WHY: Centralized env var access
        WHAT: Get env var with optional default
        HOW: os.environ.get

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)

    @staticmethod
    def set_env(key: str, value: str) -> None:
        """
        Set environment variable.

        WHY: Runtime environment modification
        WHAT: Set env var in current process
        HOW: os.environ assignment

        Args:
            key: Environment variable name
            value: Value to set
        """
        os.environ[key] = value

    @staticmethod
    def expand_env_in_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand all environment variables in config dict.

        WHY: Process entire config at once
        WHAT: Recursively expand env vars in dict
        HOW: Walk dict tree, expand strings

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with expanded environment variables

        Example:
            {
                "token": "${GITHUB_TOKEN}",
                "path": "%USERPROFILE%",
                "nested": {"var": "${HOME}"}
            }
            →
            {
                "token": "ghp_actual_token",
                "path": "C:\\Users\\Name",
                "nested": {"var": "/Users/name"}
            }
        """
        result = {}
        for key, value in config.items():
            if isinstance(value, str):
                result[key] = CrossPlatformEnv.expand_vars(value)
            elif isinstance(value, dict):
                result[key] = CrossPlatformEnv.expand_env_in_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    CrossPlatformEnv.expand_vars(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
