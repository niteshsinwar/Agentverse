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

__all__ = [
    'CrossPlatformEventLoop',
    'platform_loop',
    'CrossPlatformCommands',
    'CrossPlatformPaths',
    'CrossPlatformEnv',
]
