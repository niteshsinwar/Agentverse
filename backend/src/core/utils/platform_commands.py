"""
Cross-Platform Command Resolution

WHY: Windows needs .cmd/.exe extensions, Mac doesn't
WHAT: Resolves command names for current platform
HOW: Platform detection + command mapping
"""

import sys
import shutil
from typing import List, Tuple, Set
import logging

logger = logging.getLogger(__name__)


class CrossPlatformCommands:
    """
    Resolves commands for Windows/Mac compatibility.

    Windows: npx → npx.cmd, uvx → uvx.exe
    Mac: npx → npx, uvx → uvx (no change)
    """

    # Command categories
    NODE_COMMANDS: Set[str] = {'npx', 'npm', 'node', 'yarn', 'pnpm', 'pnpx'}
    PYTHON_COMMANDS: Set[str] = {'uvx', 'uv', 'python', 'python3', 'pip', 'pipx'}

    @staticmethod
    def resolve_command(command: str) -> str:
        """
        Resolve command to FULL PATH for reliable MCP server execution.

        WHY: MCP SDK subprocess may not inherit full PATH
        WHAT: Use shutil.which() to get absolute path
        HOW: Fall back to platform-specific extensions if not found

        Args:
            command: Command name (e.g., "npx", "uvx")

        Returns:
            Full path to executable (e.g., "/usr/local/bin/npx", "C:\\...\\npx.cmd")
        """
        # Try to find full path first (works on all platforms)
        full_path = shutil.which(command)
        if full_path:
            logger.debug(f"Resolved command with full path: {command} → {full_path}")
            return full_path

        # Fallback for Windows: try with extensions
        if sys.platform == 'win32':
            cmd_lower = command.lower().strip()

            # Remove existing extensions for normalization
            if cmd_lower.endswith('.cmd'):
                cmd_lower = cmd_lower[:-4]
            elif cmd_lower.endswith('.exe'):
                cmd_lower = cmd_lower[:-4]

            # Node.js ecosystem
            if cmd_lower in CrossPlatformCommands.NODE_COMMANDS:
                result = f"{cmd_lower}.cmd"
                logger.debug(f"Resolved Node command: {command} → {result}")
                return result

            # Python ecosystem
            if cmd_lower in CrossPlatformCommands.PYTHON_COMMANDS:
                result = f"{cmd_lower}.exe"
                logger.debug(f"Resolved Python command: {command} → {result}")
                return result

        # Unknown command, return as-is
        logger.warning(f"Could not resolve full path for: {command}")
        return command

    @staticmethod
    def resolve_command_with_args(
        command: str,
        args: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Resolve command and ensure proper arguments.

        WHY: Windows npx needs -y flag to avoid interactive prompts
        WHAT: Resolve command + add platform-specific args
        HOW: Check command type and platform

        Args:
            command: Command name
            args: Command arguments

        Returns:
            Tuple of (resolved_command, resolved_args)
        """
        resolved_cmd = CrossPlatformCommands.resolve_command(command)
        resolved_args = list(args)  # Copy args

        # Windows: Ensure npx has -y flag (auto-yes to avoid hangs)
        if sys.platform == 'win32' and 'npx' in command.lower():
            if '-y' not in resolved_args and '--yes' not in resolved_args:
                resolved_args = ['-y'] + resolved_args
                logger.debug(f"Added -y flag to npx command")

        return resolved_cmd, resolved_args

    @staticmethod
    def find_executable(command: str) -> str:
        """
        Find executable in PATH with platform resolution.

        WHY: Verify command exists before execution
        WHAT: Search PATH for resolved command
        HOW: Use shutil.which with platform-resolved name

        Args:
            command: Command name

        Returns:
            Full path to executable

        Raises:
            FileNotFoundError: If command not found in PATH
        """
        resolved = CrossPlatformCommands.resolve_command(command)

        # Try to find in PATH
        path = shutil.which(resolved)
        if path:
            logger.debug(f"Found executable: {resolved} at {path}")
            return path

        # Not found - provide helpful error
        cmd_lower = command.lower()
        if cmd_lower in CrossPlatformCommands.NODE_COMMANDS:
            raise FileNotFoundError(
                f"Node.js command '{command}' not found (tried: {resolved}). "
                f"Install with: npm install -g {command}"
            )
        elif cmd_lower in CrossPlatformCommands.PYTHON_COMMANDS:
            raise FileNotFoundError(
                f"Python command '{command}' not found (tried: {resolved}). "
                f"Install with: pip install {command}"
            )
        else:
            raise FileNotFoundError(
                f"Command '{command}' not found (tried: {resolved}). "
                f"Make sure it's installed and in PATH."
            )

    @staticmethod
    def validate_command(command: str) -> bool:
        """
        Validate that command is available.

        WHY: Early detection of missing dependencies
        WHAT: Check if command exists in PATH
        HOW: Use find_executable with exception handling

        Args:
            command: Command name to validate

        Returns:
            True if command is available, False otherwise
        """
        try:
            CrossPlatformCommands.find_executable(command)
            return True
        except FileNotFoundError:
            return False
