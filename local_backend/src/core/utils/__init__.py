"""
Cross-platform utilities for Windows/Mac compatibility.

WHY: Centralize platform-specific handling for maintainability
WHAT: Event loops, commands, paths, environment variables, processes
HOW: Platform detection with appropriate fallbacks
"""

from .event_loop import CrossPlatformEventLoop, platform_loop
from .platform_commands import CrossPlatformCommands
from .cross_platform_paths import CrossPlatformPaths
from .cross_platform_env import CrossPlatformEnv
from .mcp_auth import ensure_remote_auth_args, prepare_remote_bridge_env, BASE_AUTH_DIR

__all__ = [
    'CrossPlatformEventLoop',
    'platform_loop',
    'CrossPlatformCommands',
    'CrossPlatformPaths',
    'CrossPlatformEnv',
    'ensure_remote_auth_args',
    'prepare_remote_bridge_env',
    'BASE_AUTH_DIR',
]
