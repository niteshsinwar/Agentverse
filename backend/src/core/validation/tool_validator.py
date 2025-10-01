"""
Tool Configuration Validator
Validates tool configurations and Python code using the same logic as agent tool registration
"""

import ast
import inspect
import importlib.util
import sys
import tempfile
import os
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from .validation_result import ValidationResult, ValidationError, ValidationWarning


class ToolValidator:
    """Validates tool configurations and Python code before creation/modification"""

    @staticmethod
    def validate_tool_config(
        name: str,
        description: str,
        category: str,
        code: str,
        functions: List[str]
    ) -> ValidationResult:
        """
        Validate tool configuration using the same logic as agent tool registration
        This mirrors the exact validation that happens during tool discovery and loading
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        # Validate basic fields
        ToolValidator._validate_basic_fields(result, name, description, category, functions)

        # Validate Python code (same as _import_tools_py validation)
        if code.strip():
            ToolValidator._validate_tool_code(result, code, functions)
        else:
            result.add_warning("code", "Tool code is empty", "EMPTY_CODE")

        return result

    @staticmethod
    def validate_tool_code_execution(code: str, function_names: Optional[List[str]] = None) -> ValidationResult:
        """
        Validate tool code by attempting to compile and inspect it
        Uses the same logic as the actual tool loading process
        """
        result = ValidationResult(valid=True, errors=[], warnings=[])

        if not code.strip():
            result.add_warning("code", "Code is empty", "EMPTY_CODE")
            return result

        # Test compilation (same as importlib.util.spec_from_file_location would do)
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.add_error("code", f"Python syntax error: {str(e)}", "SYNTAX_ERROR", {
                "line": e.lineno,
                "offset": e.offset,
                "text": e.text
            })
            return result

        # Test actual code execution in isolation (same as spec.loader.exec_module)
        try:
            ToolValidator._test_code_execution(result, code)
        except Exception as e:
            result.add_error("code", f"Code execution failed: {str(e)}", "EXECUTION_ERROR")

        # Validate function definitions if specified
        if function_names:
            ToolValidator._validate_declared_functions(result, code, function_names)

        return result

    @staticmethod
    def _validate_basic_fields(result: ValidationResult, name: str, description: str, category: str, functions: List[str]):
        """Validate basic tool fields"""

        if not name or not name.strip():
            result.add_error("name", "Tool name is required", "MISSING_NAME")
        elif len(name.strip()) < 2:
            result.add_error("name", "Tool name must be at least 2 characters long", "NAME_TOO_SHORT")
        elif len(name.strip()) > 100:
            result.add_error("name", "Tool name must be less than 100 characters", "NAME_TOO_LONG")

        # Validate tool name format (same as function name validation)
        if name and not name.replace("_", "").isalnum():
            result.add_error("name", "Tool name can only contain letters, numbers, and underscores", "INVALID_NAME_FORMAT")

        if not description or not description.strip():
            result.add_warning("description", "Tool description is empty", "EMPTY_DESCRIPTION")
        elif len(description.strip()) > 1000:
            result.add_warning("description", "Tool description is very long (>1000 chars)", "DESCRIPTION_TOO_LONG")

        if not category or not category.strip():
            result.add_warning("category", "Tool category is empty", "EMPTY_CATEGORY")

        if not functions or not isinstance(functions, list):
            result.add_warning("functions", "No functions specified", "NO_FUNCTIONS")
        elif len(functions) == 0:
            result.add_warning("functions", "Functions list is empty", "EMPTY_FUNCTIONS")

    @staticmethod
    def _validate_tool_code(result: ValidationResult, code: str, declared_functions: List[str]):
        """
        Validate tool code using the same logic as register_tools_from_module
        This includes security checks and function validation
        """

        # Parse code for analysis
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result.add_error("code", f"Python syntax error: {str(e)}", "SYNTAX_ERROR", {
                "line": e.lineno,
                "offset": e.offset
            })
            return

        # Security validation - check for dangerous imports/calls (same as agent validation)
        ToolValidator._validate_code_security(result, tree)

        # Find function definitions and validate against declared functions
        found_functions = {}
        agent_tool_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                found_functions[node.name] = node

                # Check for @agent_tool decorator (same logic as register_tools_from_module)
                has_agent_tool_decorator = False
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "agent_tool":
                        has_agent_tool_decorator = True
                        break

                if has_agent_tool_decorator:
                    agent_tool_functions.append(node.name)

        # Validate declared functions exist in code
        for func_name in declared_functions:
            if func_name not in found_functions:
                result.add_error("functions", f"Declared function '{func_name}' not found in code", "FUNCTION_NOT_FOUND")

        # Check if declared functions have @agent_tool decorator
        for func_name in declared_functions:
            if func_name in found_functions and func_name not in agent_tool_functions:
                result.add_warning("functions", f"Function '{func_name}' missing @agent_tool decorator", "MISSING_DECORATOR")

        # Check for @agent_tool import
        has_agent_tool_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "base_agent" in node.module:
                    for alias in node.names:
                        if alias.name == "agent_tool":
                            has_agent_tool_import = True
                            break

        if agent_tool_functions and not has_agent_tool_import:
            result.add_warning("code", "Recommended import: from src.core.agents.base_agent import agent_tool", "MISSING_IMPORT", {
                "recommended_import": "from src.core.agents.base_agent import agent_tool"
            })

        # Validate function signatures (same checks as register_tools_from_module)
        for func_name, func_node in found_functions.items():
            if func_name in declared_functions:
                ToolValidator._validate_function_signature(result, func_name, func_node)

    @staticmethod
    def _validate_code_security(result: ValidationResult, tree: ast.AST):
        """Validate code for security issues"""

        # Dangerous imports that should be flagged
        dangerous_imports = [
            'os', 'subprocess', 'sys', '__import__', 'eval', 'exec',
            'open', 'file', 'input', 'raw_input', 'compile', 'globals',
            'locals', 'vars', 'dir', 'getattr', 'setattr', 'delattr',
            'hasattr', 'callable', 'isinstance', 'issubclass'
        ]

        # Dangerous function calls
        dangerous_calls = [
            'eval', 'exec', '__import__', 'compile', 'open', 'file',
            'input', 'raw_input', 'getattr', 'setattr', 'delattr'
        ]

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_imports:
                        result.add_warning("code", f"Potentially dangerous import: {alias.name}", "DANGEROUS_IMPORT", {
                            "import": alias.name,
                            "line": node.lineno
                        })

            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module in dangerous_imports or any(danger in node.module for danger in ['os', 'subprocess', 'sys']):
                    result.add_warning("code", f"Potentially dangerous import from: {node.module}", "DANGEROUS_IMPORT", {
                        "import": node.module,
                        "line": node.lineno
                    })

            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                    result.add_warning("code", f"Potentially dangerous function call: {node.func.id}", "DANGEROUS_CALL", {
                        "function": node.func.id,
                        "line": node.lineno
                    })

            # Check for direct attribute access that might be dangerous
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    if node.value.id in ['os', 'sys', 'subprocess'] and node.attr in ['system', 'popen', 'exec']:
                        result.add_warning("code", f"Potentially dangerous attribute access: {node.value.id}.{node.attr}", "DANGEROUS_ATTRIBUTE", {
                            "access": f"{node.value.id}.{node.attr}",
                            "line": node.lineno
                        })

    @staticmethod
    def _validate_function_signature(result: ValidationResult, func_name: str, func_node: ast.FunctionDef):
        """Validate function signature for tool compatibility"""

        # Check if function has parameters
        if len(func_node.args.args) == 0:
            result.add_warning("functions", f"Function '{func_name}' has no parameters", "NO_PARAMETERS", {
                "function": func_name,
                "line": func_node.lineno
            })

        # Check for async functions (tools should generally be sync for simplicity)
        if isinstance(func_node, ast.AsyncFunctionDef):
            result.add_warning("functions", f"Function '{func_name}' is async - may require special handling", "ASYNC_FUNCTION", {
                "function": func_name,
                "line": func_node.lineno
            })

        # Check for *args or **kwargs (potential issues with parameter validation)
        has_varargs = func_node.args.vararg is not None
        has_kwargs = func_node.args.kwarg is not None

        if has_varargs:
            result.add_warning("functions", f"Function '{func_name}' uses *args - parameter validation may be limited", "USES_VARARGS", {
                "function": func_name,
                "line": func_node.lineno
            })

        if has_kwargs:
            result.add_warning("functions", f"Function '{func_name}' uses **kwargs - parameter validation may be limited", "USES_KWARGS", {
                "function": func_name,
                "line": func_node.lineno
            })

    @staticmethod
    def _validate_declared_functions(result: ValidationResult, code: str, function_names: List[str]):
        """Validate that declared function names actually exist in the code"""

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return  # Syntax errors already handled elsewhere

        found_functions = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                found_functions.add(node.name)

        for func_name in function_names:
            if func_name not in found_functions:
                result.add_error("functions", f"Declared function '{func_name}' not found in code", "FUNCTION_NOT_FOUND")

        # Check for functions in code not declared in the list
        undeclared_functions = found_functions - set(function_names)
        if undeclared_functions:
            result.add_warning("functions", f"Code contains undeclared functions: {', '.join(undeclared_functions)}", "UNDECLARED_FUNCTIONS")

    @staticmethod
    def _test_code_execution(result: ValidationResult, code: str):
        """
        Test ACTUAL tool registration using the EXACT same process as agent building
        This matches exactly what registry.py does: importlib -> register_tools_from_module
        """
        try:
            # Test the EXACT same process as agent building
            import tempfile
            import importlib.util
            from src.core.agents.base_agent import BaseAgent

            # Create temporary file with tool code (same as agent discovery)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                # Test actual module loading (EXACT same as registry.py:39-42)
                import time
                module_name = f"test_tool_{int(time.time() * 1000)}"
                spec = importlib.util.spec_from_file_location(module_name, temp_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # This will fail if imports are broken

                # Test actual tool registration (EXACT same as registry.py:106-108)
                test_agent = BaseAgent(agent_id="test_agent")
                test_agent.register_tools_from_module(module)

                # Verify tools were registered
                registered_tools = list(test_agent.tools.keys())
                if registered_tools:
                    result.add_warning("code", f"✅ Successfully registered {len(registered_tools)} tools: {', '.join(registered_tools)}", "REGISTRATION_SUCCESS")
                else:
                    result.add_warning("code", "⚠️ No tools registered - check @agent_tool decorators", "NO_TOOLS_REGISTERED")

            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except ImportError as e:
            result.add_error("code", f"Import error during real tool loading: {str(e)}", "IMPORT_ERROR")
        except Exception as e:
            result.add_error("code", f"Tool registration failed: {str(e)}", "REGISTRATION_ERROR")

    @staticmethod
    def get_tool_code_template() -> str:
        """Return a basic template for tool code"""
        return '''"""
Tool functions for agent
"""

from src.core.agents.base_agent import agent_tool

@agent_tool
def example_function(param1: str, param2: int = 10) -> str:
    """
    Example tool function.

    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2 (optional)

    Returns:
        Description of return value
    """
    return f"Processing {param1} with value {param2}"

@agent_tool
def another_function(data: dict) -> bool:
    """
    Another example tool function.

    Args:
        data: Input data dictionary

    Returns:
        Success status
    """
    # Your implementation here
    return True
'''

    @staticmethod
    def get_common_tool_patterns() -> List[Dict[str, Any]]:
        """Return common tool patterns and examples"""
        return [
            {
                "name": "Data Processing Tool",
                "description": "Template for data processing functions",
                "category": "data",
                "code": '''from src.core.agents.base_agent import agent_tool

@agent_tool
def process_data(data: dict, operation: str = "transform") -> dict:
    """Process data with specified operation."""
    # Implementation here
    return {"processed": True, "operation": operation}''',
                "functions": ["process_data"]
            },
            {
                "name": "API Client Tool",
                "description": "Template for API interaction functions",
                "category": "api",
                "code": '''from src.core.agents.base_agent import agent_tool
import requests

@agent_tool
def api_request(url: str, method: str = "GET", data: dict = None) -> dict:
    """Make API request and return response."""
    # Implementation here
    return {"status": "success", "url": url}''',
                "functions": ["api_request"]
            },
            {
                "name": "File Operations Tool",
                "description": "Template for file handling functions",
                "category": "filesystem",
                "code": '''from src.core.agents.base_agent import agent_tool

@agent_tool
def read_file_content(file_path: str) -> str:
    """Read and return file content."""
    # Implementation here
    return "file content"

@agent_tool
def write_file_content(file_path: str, content: str) -> bool:
    """Write content to file."""
    # Implementation here
    return True''',
                "functions": ["read_file_content", "write_file_content"]
            }
        ]