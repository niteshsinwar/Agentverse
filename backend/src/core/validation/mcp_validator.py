"""
MCP Configuration Validator
Validates MCP server configurations using the same logic as mcp/client.py
Leverages cross-platform utilities for command resolution and event loop management
"""

from typing import Dict, Any, List
import asyncio

from .validation_result import ValidationResult
from src.core.utils.platform_commands import CrossPlatformCommands
from src.core.utils.event_loop import platform_loop


class McpValidator:
    """Validates MCP server configurations before creation/modification"""

    @staticmethod
    def validate_mcp_server_config(
        name: str,
        description: str,
        category: str,
        config: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate MCP server configuration using the same logic as MCPServerHandle
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        # Validate basic fields
        McpValidator._validate_basic_fields(result, name, description, category)

        # Validate server configuration
        McpValidator._validate_server_config(result, name, config)

        return result

    @staticmethod
    def validate_mcp_servers_config(mcp_config: Dict[str, Any]) -> ValidationResult:
        """
        Validate entire MCP servers configuration dictionary
        Handles both old and new format (with mcpServers wrapper)
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        if not isinstance(mcp_config, dict):
            result.add_error("mcp_config", "MCP configuration must be a dictionary", "INVALID_TYPE")
            return result

        # Empty config is valid
        if not mcp_config:
            return result

        # Handle format: {"mcpServers": {...}}
        servers_config = mcp_config
        if "mcpServers" in mcp_config:
            servers_config = mcp_config["mcpServers"]
            if not isinstance(servers_config, dict):
                result.add_error("mcpServers", "mcpServers must be a dictionary", "INVALID_MCPSERVERS_TYPE")
                return result

        for server_name, server_config in servers_config.items():
            McpValidator._validate_single_server_in_config(result, server_name, server_config)

        return result

    @staticmethod
    async def validate_mcp_server_connectivity(
        name: str,
        config: Dict[str, Any],
        timeout: float = 10.0
    ) -> ValidationResult:
        """
        Test MCP server startup and protocol communication with timeout.

        Uses asyncio.shield() to protect cleanup from cancellation, avoiding
        "Attempted to exit cancel scope in a different task" errors.
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])
        mcp_manager = None

        async def _validate():
            """Inner validation function that handles its own cleanup"""
            nonlocal mcp_manager
            from src.core.mcp.client import MCPManager
            test_config = {"mcpServers": {name: config}}
            mcp_manager = MCPManager.from_config(test_config)

            if name not in mcp_manager.servers:
                result.add_error("server_creation", f"Failed to create MCP server '{name}' from config", "SERVER_CREATION_FAILED")
                return

            # Discover tools
            tools = await mcp_manager.discover_tools()

            # Check tools discovered
            server_tools = [t for t in tools if t.server_name == name]
            if server_tools:
                result.add_warning("tools", f"✅ Discovered {len(server_tools)} tools", "TOOLS_DISCOVERED")
                for tool in server_tools[:3]:
                    desc = tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
                    result.add_warning("tools", f"  - {tool.name}: {desc}", "TOOL_DETAIL")
            else:
                result.add_warning("tools", "No tools discovered from MCP server", "NO_TOOLS")

            result.add_warning("overall", "✅ Full MCP protocol validation passed", "VALIDATION_SUCCESS")

        try:
            # Run with timeout, but DON'T cancel - just raise TimeoutError
            await asyncio.wait_for(_validate(), timeout=timeout)
        except asyncio.TimeoutError:
            result.add_error("timeout", f"MCP server '{name}' validation timeout after {timeout}s", "VALIDATION_TIMEOUT")
        except Exception as e:
            result.add_error("protocol", f"MCP server validation failed: {str(e)}", "VALIDATION_FAILED")
        finally:
            # CRITICAL: Use shield to protect cleanup from cancellation
            if mcp_manager:
                try:
                    await asyncio.shield(mcp_manager.stop_all())
                except Exception as cleanup_error:
                    # Cleanup errors are non-critical, just log them
                    result.add_warning("cleanup", f"Cleanup warning: {cleanup_error}", "CLEANUP_WARNING")

        return result

    @staticmethod
    def _validate_basic_fields(result: ValidationResult, name: str, description: str, category: str):
        """Validate basic MCP server fields"""

        if not name or not name.strip():
            result.add_error("name", "MCP server name is required", "MISSING_NAME")
        elif len(name.strip()) < 2:
            result.add_error("name", "MCP server name must be at least 2 characters long", "NAME_TOO_SHORT")
        elif len(name.strip()) > 100:
            result.add_error("name", "MCP server name must be less than 100 characters", "NAME_TOO_LONG")

        # Validate server name format
        if name and not name.replace("_", "").replace("-", "").replace(".", "").isalnum():
            result.add_error("name", "MCP server name can only contain letters, numbers, underscores, hyphens, and dots", "INVALID_NAME_FORMAT")

        if not description or not description.strip():
            result.add_warning("description", "MCP server description is empty", "EMPTY_DESCRIPTION")
        elif len(description.strip()) > 500:
            result.add_warning("description", "MCP server description is very long (>500 chars)", "DESCRIPTION_TOO_LONG")

        if not category or not category.strip():
            result.add_warning("category", "MCP server category is empty", "EMPTY_CATEGORY")

    @staticmethod
    def _validate_server_config(result: ValidationResult, server_name: str, config: Dict[str, Any]):
        """
        Validate server configuration structure
        Uses cross-platform command utilities for validation
        """
        if not isinstance(config, dict):
            result.add_error("config", "Server configuration must be a dictionary", "INVALID_CONFIG_TYPE")
            return

        # Validate command (required field)
        command = config.get("command", "")
        if not command or not isinstance(command, str) or not command.strip():
            result.add_error("command", "Command is required and must be a non-empty string", "MISSING_COMMAND")
        else:
            # Use cross-platform command validation
            if not CrossPlatformCommands.validate_command(command):
                result.add_error("command", f"Command '{command}' not found in system PATH", "COMMAND_NOT_FOUND")

            # Check for common command patterns
            command_lower = command.strip().lower()
            if command_lower in ['python', 'python3']:
                result.add_warning("command", "Using bare 'python' command - consider using full path", "BARE_PYTHON_COMMAND")
            elif command_lower == 'node':
                result.add_warning("command", "Using bare 'node' command - consider using full path", "BARE_NODE_COMMAND")

        # Validate args (must be list)
        args = config.get("args", [])
        if args is None:
            args = []
        if not isinstance(args, list):
            result.add_error("args", "Args must be a list", "INVALID_ARGS_TYPE")
        else:
            for i, arg in enumerate(args):
                if not isinstance(arg, str):
                    result.add_error("args", f"Argument {i} must be a string", "INVALID_ARG_TYPE")

        # Validate environment variables (optional)
        env_vars = config.get("env", {})
        if env_vars is None:
            env_vars = {}
        if not isinstance(env_vars, dict):
            result.add_error("env", "Environment variables must be a dictionary", "INVALID_ENV_TYPE")
        else:
            for key, value in env_vars.items():
                if not isinstance(key, str):
                    result.add_error("env", f"Environment variable key must be string: {key}", "INVALID_ENV_KEY")
                if not isinstance(value, str):
                    result.add_error("env", f"Environment variable value must be string: {key}={value}", "INVALID_ENV_VALUE")

        # Validate timeout (optional)
        if "timeout" in config:
            timeout = config.get("timeout")
            if not isinstance(timeout, (int, float)):
                result.add_error("timeout", "Timeout must be a number", "INVALID_TIMEOUT_TYPE")
            elif timeout <= 0:
                result.add_error("timeout", "Timeout must be positive", "INVALID_TIMEOUT_VALUE")
            elif timeout < 5:
                result.add_warning("timeout", "Timeout is very short (<5s), may cause connection issues", "SHORT_TIMEOUT")
            elif timeout > 120:
                result.add_warning("timeout", "Timeout is very long (>120s), may cause delays", "LONG_TIMEOUT")

        # Validate health_check flag (optional)
        if "health_check" in config:
            health_check = config.get("health_check")
            if not isinstance(health_check, bool):
                result.add_error("health_check", "Health check flag must be boolean", "INVALID_HEALTH_CHECK_TYPE")

        # NPX-specific validation (using cross-platform command info)
        if command and command.strip().lower() == "npx":
            if isinstance(args, list):
                normalized_args = [str(arg).strip().lower() for arg in args]
                if "-y" not in normalized_args and "--yes" not in normalized_args:
                    result.add_warning("args", "NPX command should include -y or --yes flag to avoid interactive prompts", "NPX_MISSING_YES")

    @staticmethod
    def _validate_single_server_in_config(result: ValidationResult, server_name: str, server_config: Any):
        """Validate a single server configuration within the MCP config dictionary"""

        if not isinstance(server_config, dict):
            result.add_error(f"servers.{server_name}", f"Server '{server_name}' configuration must be a dictionary", "INVALID_SERVER_CONFIG")
            return

        # Validate server name format
        if not server_name.replace("_", "").replace("-", "").replace(".", "").isalnum():
            result.add_error(f"servers.{server_name}", f"Server name '{server_name}' contains invalid characters", "INVALID_SERVER_NAME")

        # Use the same validation as single server config
        McpValidator._validate_server_config(result, server_name, server_config)

    @staticmethod
    def get_common_mcp_templates() -> List[Dict[str, Any]]:
        """
        Return common MCP server configuration templates
        These are pre-validated configurations for popular MCP servers
        """
        return [
            {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"],
                "env": {}
            },
            {
                "name": "brave_search",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {
                    "BRAVE_API_KEY": "${BRAVE_API_KEY}"
                }
            },
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
                }
            },
            {
                "name": "sqlite",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"],
                "env": {}
            },
            {
                "name": "playwright",
                "command": "npx",
                "args": ["@playwright/mcp@latest"]
            }
        ]
