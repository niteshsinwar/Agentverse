"""
Agent Configuration Validator
Validates agent configurations using the exact same logic as registry.py
"""

import os
import yaml
import json
import importlib.util
import inspect
import ast
from typing import Dict, Any, Optional, List
from pathlib import Path

from .validation_result import ValidationResult, ValidationError, ValidationWarning


class AgentValidator:
    """Validates agent configurations before creation/modification"""

    @staticmethod
    def validate_agent_config(
        name: str,
        description: str,
        emoji: str,
        tools_code: Optional[str] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
        agent_key: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate agent configuration using the same logic as registry.py
        This mirrors the exact validation that happens during agent discovery and building
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        # Validate basic fields (same as registry.py AgentSpec validation)
        AgentValidator._validate_basic_fields(result, name, description, emoji, agent_key)

        # Validate tools code (same as _import_tools_py validation)
        if tools_code:
            AgentValidator._validate_tools_code(result, tools_code)

        # Validate MCP configuration (same as MCPManager.from_config validation)
        if mcp_config:
            AgentValidator._validate_mcp_config(result, mcp_config)

        return result

    @staticmethod
    def validate_agent_folder(agent_folder: str) -> ValidationResult:
        """
        Validate existing agent folder structure
        Uses the exact same logic as discover_agents() in registry.py
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        if not os.path.isdir(agent_folder):
            result.add_error("folder", f"Agent folder does not exist: {agent_folder}", "FOLDER_NOT_EXISTS")
            return result

        # Check for required files (same as registry.py discovery logic)
        agent_yaml_path = os.path.join(agent_folder, "agent.yaml")
        mcp_json_path = os.path.join(agent_folder, "mcp.json")
        tools_py_path = os.path.join(agent_folder, "tools.py")

        if not os.path.exists(agent_yaml_path):
            result.add_error("agent_yaml", "Required file agent.yaml not found", "MISSING_AGENT_YAML")

        if not os.path.exists(mcp_json_path):
            result.add_error("mcp_json", "Required file mcp.json not found", "MISSING_MCP_JSON")

        if not result.valid:
            return result

        # Validate agent.yaml content (same as _load_yaml in registry.py)
        try:
            with open(agent_yaml_path, "r", encoding="utf-8") as f:
                agent_meta = yaml.safe_load(f) or {}

            name = agent_meta.get("name", "")
            description = agent_meta.get("description", "")
            emoji = agent_meta.get("emoji", "🔧")

            AgentValidator._validate_basic_fields(result, name, description, emoji)

        except yaml.YAMLError as e:
            result.add_error("agent_yaml", f"Invalid YAML syntax: {str(e)}", "INVALID_YAML")
        except Exception as e:
            result.add_error("agent_yaml", f"Failed to read agent.yaml: {str(e)}", "READ_ERROR")

        # Validate mcp.json content (same as json.load in registry.py)
        try:
            with open(mcp_json_path, "r", encoding="utf-8") as f:
                mcp_config = json.load(f)

            AgentValidator._validate_mcp_config(result, mcp_config)

        except json.JSONDecodeError as e:
            result.add_error("mcp_json", f"Invalid JSON syntax: {str(e)}", "INVALID_JSON")
        except Exception as e:
            result.add_error("mcp_json", f"Failed to read mcp.json: {str(e)}", "READ_ERROR")

        # Validate tools.py if it exists (same as _import_tools_py validation)
        if os.path.exists(tools_py_path):
            try:
                with open(tools_py_path, "r", encoding="utf-8") as f:
                    tools_code = f.read()
                AgentValidator._validate_tools_code(result, tools_code)
            except Exception as e:
                result.add_error("tools_py", f"Failed to read tools.py: {str(e)}", "READ_ERROR")

        return result

    @staticmethod
    def _validate_basic_fields(result: ValidationResult, name: str, description: str, emoji: str, agent_key: Optional[str] = None):
        """Validate basic agent fields (mirrors AgentSpec validation)"""

        if not name or not name.strip():
            result.add_error("name", "Agent name is required", "MISSING_NAME")
        elif len(name.strip()) < 2:
            result.add_error("name", "Agent name must be at least 2 characters long", "NAME_TOO_SHORT")
        elif len(name.strip()) > 100:
            result.add_error("name", "Agent name must be less than 100 characters", "NAME_TOO_LONG")

        if not description or not description.strip():
            result.add_warning("description", "Agent description is empty", "EMPTY_DESCRIPTION")
        elif len(description.strip()) > 500:
            result.add_warning("description", "Agent description is very long (>500 chars)", "DESCRIPTION_TOO_LONG")

        if not emoji or not emoji.strip():
            result.add_warning("emoji", "No emoji specified, will use default 🔧", "MISSING_EMOJI")

        if agent_key:
            # Validate agent key format (same as registry.py key requirements)
            if not agent_key.replace("_", "").replace("-", "").isalnum():
                result.add_error("agent_key", "Agent key can only contain letters, numbers, underscores, and hyphens", "INVALID_AGENT_KEY")
            if agent_key.startswith("__"):
                result.add_error("agent_key", "Agent key cannot start with double underscore", "INVALID_AGENT_KEY")

    @staticmethod
    def _validate_tools_code(result: ValidationResult, tools_code: str):
        """
        Validate tools.py code using the same logic as _import_tools_py and register_tools_from_module
        """
        if not tools_code.strip():
            return  # Empty tools code is valid

        # Parse Python syntax (same validation as importlib would do)
        try:
            tree = ast.parse(tools_code)
        except SyntaxError as e:
            result.add_error("tools_code", f"Python syntax error: {str(e)}", "SYNTAX_ERROR", {
                "line": e.lineno,
                "offset": e.offset
            })
            return

        # Security validation - check for dangerous imports/calls
        dangerous_imports = ['os', 'subprocess', 'sys', '__import__', 'eval', 'exec', 'open']
        dangerous_calls = ['eval', 'exec', '__import__', 'getattr', 'setattr', 'delattr']

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_imports:
                        result.add_warning("tools_code", f"Potentially dangerous import: {alias.name}", "DANGEROUS_IMPORT", {
                            "import": alias.name,
                            "line": node.lineno
                        })

            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module in dangerous_imports:
                    result.add_warning("tools_code", f"Potentially dangerous import from: {node.module}", "DANGEROUS_IMPORT", {
                        "import": node.module,
                        "line": node.lineno
                    })

            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in dangerous_calls:
                    result.add_warning("tools_code", f"Potentially dangerous function call: {node.func.id}", "DANGEROUS_CALL", {
                        "function": node.func.id,
                        "line": node.lineno
                    })

        # Validate agent tools (same logic as register_tools_from_module)
        tool_functions = []
        function_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_names.add(node.name)

                # Check if function has @agent_tool decorator
                has_agent_tool_decorator = False
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "agent_tool":
                        has_agent_tool_decorator = True
                        break

                if has_agent_tool_decorator:
                    tool_functions.append(node.name)

                    # Validate function signature
                    if len(node.args.args) == 0:
                        result.add_warning("tools_code", f"Tool function '{node.name}' has no parameters", "NO_PARAMETERS", {
                            "function": node.name,
                            "line": node.lineno
                        })

        # Check for @agent_tool import (more flexible pattern matching)
        has_agent_tool_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and ("base_agent" in node.module or "decorators" in node.module):
                    for alias in node.names:
                        if alias.name == "agent_tool":
                            has_agent_tool_import = True
                            break

        if tool_functions and not has_agent_tool_import:
            result.add_warning("tools_code", "Recommended import: from src.core.agents.base_agent import agent_tool", "MISSING_IMPORT", {
                "recommended_import": "from src.core.agents.base_agent import agent_tool"
            })

        if not tool_functions:
            result.add_warning("tools_code", "No @agent_tool decorated functions found", "NO_TOOLS_FOUND")

    @staticmethod
    def _validate_mcp_config(result: ValidationResult, mcp_config: Dict[str, Any]):
        """
        Validate MCP configuration using the same logic as MCPManager.from_config
        Supports both direct server config and mcpServers wrapper format
        """
        if not isinstance(mcp_config, dict):
            result.add_error("mcp_config", "MCP configuration must be a dictionary", "INVALID_TYPE")
            return

        # Empty MCP config is valid
        if not mcp_config:
            return

        # Handle the actual format used by working agents: {"mcpServers": {...}}
        servers_config = mcp_config
        if "mcpServers" in mcp_config:
            servers_config = mcp_config["mcpServers"]
            if not isinstance(servers_config, dict):
                result.add_error("mcp_config", "mcpServers must be a dictionary", "INVALID_TYPE")
                return

        for server_name, server_config in servers_config.items():
            if not isinstance(server_config, dict):
                result.add_error("mcp_config", f"MCP server '{server_name}' configuration must be a dictionary", "INVALID_SERVER_CONFIG")
                continue

            # Validate required fields (same as MCPServerSpec validation)
            command = server_config.get("command", "")
            if not command or not command.strip():
                result.add_error("mcp_config", f"MCP server '{server_name}' missing required 'command' field", "MISSING_COMMAND")

            args = server_config.get("args", [])
            if not isinstance(args, list):
                result.add_error("mcp_config", f"MCP server '{server_name}' 'args' must be a list", "INVALID_ARGS")

            env = server_config.get("env", {})
            if not isinstance(env, dict):
                result.add_error("mcp_config", f"MCP server '{server_name}' 'env' must be a dictionary", "INVALID_ENV")

            timeout = server_config.get("timeout", 30.0)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                result.add_error("mcp_config", f"MCP server '{server_name}' 'timeout' must be a positive number", "INVALID_TIMEOUT")

            # Validate server name format
            if not server_name.replace("_", "").replace("-", "").isalnum():
                result.add_error("mcp_config", f"MCP server name '{server_name}' can only contain letters, numbers, underscores, and hyphens", "INVALID_SERVER_NAME")