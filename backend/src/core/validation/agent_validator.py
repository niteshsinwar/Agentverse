"""
Agent Configuration Validator
Validates agent configurations using the exact same logic as registry.py

REFACTORED: Delegates to ToolValidator and McpValidator to eliminate code duplication (DRY principle)
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List

from .validation_result import ValidationResult


class AgentValidator:
    """Validates agent configurations before creation/modification"""

    @staticmethod
    async def validate_agent_config(
        name: str,
        description: str,
        emoji: str,
        tools_code: Optional[str] = None,
        mcp_config: Optional[Dict[str, Any]] = None,
        agent_key: Optional[str] = None,
        llm_config: Optional[Dict[str, str]] = None,
        selected_tools: Optional[List[str]] = None,
        selected_mcps: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate agent configuration by testing COMPLETE agent building process
        This uses the EXACT same logic as registry.py: discover_agents() -> build_agent()
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        # Validate basic fields (same as registry.py AgentSpec validation)
        AgentValidator._validate_basic_fields(result, name, description, emoji, agent_key)

        # DELEGATE to specialized validators (DRY principle)
        # 1. Validate tools code (delegate to ToolValidator)
        if tools_code:
            AgentValidator._validate_tools_code(result, tools_code)

        # 2. Validate MCP config (delegate to McpValidator)
        if mcp_config:
            AgentValidator._validate_mcp_config(result, mcp_config)

        # If validation already failed, don't attempt build
        if not result.valid:
            return result

        # Test COMPLETE agent building process (same as build_agent())
        try:
            import tempfile
            import os
            import yaml
            import json
            from src.core.agents.registry import build_agent, AgentSpec

            # Create temporary agent directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create agent.yaml
                agent_yaml = {
                    "name": name,
                    "description": description,
                    "emoji": emoji,
                    "llm": llm_config or {"provider": "openai", "model": "gpt-4o-mini"}
                }

                with open(os.path.join(temp_dir, "agent.yaml"), 'w') as f:
                    yaml.dump(agent_yaml, f)

                # Create mcp.json (handle both custom and selected MCPs)
                final_mcp_config = mcp_config or {}
                if selected_mcps:
                    # Load existing MCP servers and merge selected ones
                    try:
                        from pathlib import Path
                        mcp_path = Path("config/mcp.json")
                        if mcp_path.exists():
                            with open(mcp_path, 'r') as f:
                                global_mcps = json.load(f)
                                if "mcpServers" in global_mcps:
                                    selected_mcp_config = {
                                        key: value for key, value in global_mcps["mcpServers"].items()
                                        if key in selected_mcps
                                    }
                                    final_mcp_config = {"mcpServers": selected_mcp_config}
                    except Exception as e:
                        result.add_warning("mcp", f"Could not load selected MCPs: {e}", "MCP_LOAD_WARNING")

                with open(os.path.join(temp_dir, "mcp.json"), 'w') as f:
                    json.dump(final_mcp_config, f)

                # Create tools.py (handle both custom and selected tools)
                final_tools_code = tools_code or ""
                if selected_tools:
                    # Load existing tools and merge selected ones
                    try:
                        from pathlib import Path
                        tools_path = Path("config/tools.json")
                        if tools_path.exists():
                            with open(tools_path, 'r') as f:
                                global_tools = json.load(f)
                                selected_tool_codes = []
                                for tool_id in selected_tools:
                                    if tool_id in global_tools:
                                        tool_code = global_tools[tool_id].get("code", "")
                                        if tool_code:
                                            selected_tool_codes.append(f"# Tool: {tool_id}\n{tool_code}\n")

                                if selected_tool_codes:
                                    if final_tools_code:
                                        final_tools_code += "\n\n" + "\n\n".join(selected_tool_codes)
                                    else:
                                        final_tools_code = "\n\n".join(selected_tool_codes)
                    except Exception as e:
                        result.add_warning("tools", f"Could not load selected tools: {e}", "TOOLS_LOAD_WARNING")

                if final_tools_code.strip():
                    with open(os.path.join(temp_dir, "tools.py"), 'w') as f:
                        f.write(final_tools_code)
                else:
                    # Create empty tools.py
                    with open(os.path.join(temp_dir, "tools.py"), 'w') as f:
                        f.write("# Agent tools will be defined here\n")

                # Test ACTUAL agent building (EXACT same as registry.py)
                spec = AgentSpec(
                    key=agent_key or "test_agent",
                    name=name,
                    description=description,
                    emoji=emoji,
                    llm=agent_yaml["llm"],
                    folder=temp_dir,
                    mcp_config=final_mcp_config,
                    tools_module=os.path.join(temp_dir, "tools.py") if final_tools_code.strip() else None
                )

                # This is the CRITICAL test - actual agent building
                agent = await build_agent(spec)

                # Verify agent was built successfully
                result.add_warning("build", f"✅ Agent built successfully: {agent.agent_id}", "BUILD_SUCCESS")
                result.add_warning("build", f"   LLM: {agent.llm_config}", "BUILD_LLM")
                result.add_warning("build", f"   Tools: {len(agent.tools)} registered", "BUILD_TOOLS")

                if agent.mcp and hasattr(agent.mcp, 'servers') and agent.mcp.servers:
                    mcp_count = len(agent.mcp.servers)
                    result.add_warning("build", f"   MCP: {mcp_count} servers connected", "BUILD_MCP")
                else:
                    result.add_warning("build", "   MCP: No servers", "BUILD_NO_MCP")

        except Exception as e:
            result.add_error("build", f"Agent building failed: {str(e)}", "BUILD_FAILED")

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
        Validate tools.py code by delegating to ToolValidator.
        Ensures consistency with tool endpoint validation (DRY principle).
        """
        if not tools_code.strip():
            return  # Empty tools code is valid

        # DELEGATE to ToolValidator (reuse existing validation logic)
        from src.core.validation.tool_validator import ToolValidator

        tool_validation = ToolValidator.validate_tool_code_execution(
            code=tools_code,
            function_names=None  # Auto-discover functions
        )

        # Merge validation results with proper field context
        for error in tool_validation.errors:
            result.add_error(
                "tools_code",
                error.message,
                error.code,
                error.details
            )

        for warning in tool_validation.warnings:
            result.add_warning(
                "tools_code",
                warning.message,
                warning.code,
                warning.details
            )

    @staticmethod
    def _validate_mcp_config(result: ValidationResult, mcp_config: Dict[str, Any]):
        """
        Validate MCP configuration by delegating to McpValidator.
        Ensures consistency with MCP endpoint validation (DRY principle).
        """
        if not isinstance(mcp_config, dict):
            result.add_error("mcp_config", "MCP configuration must be a dictionary", "INVALID_TYPE")
            return

        # Empty MCP config is valid
        if not mcp_config:
            return

        # DELEGATE to McpValidator (reuse existing validation logic)
        from src.core.validation.mcp_validator import McpValidator

        mcp_validation = McpValidator.validate_mcp_servers_config(mcp_config)

        # Merge validation results with proper field context
        for error in mcp_validation.errors:
            result.add_error(
                "mcp_config",
                error.message,
                error.code,
                error.details
            )

        for warning in mcp_validation.warnings:
            result.add_warning(
                "mcp_config",
                warning.message,
                warning.code,
                warning.details
            )
