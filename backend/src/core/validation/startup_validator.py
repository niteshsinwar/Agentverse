"""
Startup Validation System
Comprehensive validation of project structure, imports, and configuration
"""

import os
import sys
import ast
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    ERROR = "ERROR"      # Fatal issues that prevent startup
    WARNING = "WARNING"  # Issues that should be addressed
    INFO = "INFO"       # Informational messages
    SUCCESS = "SUCCESS"  # Validation passed

@dataclass
class ValidationIssue:
    level: ValidationLevel
    module: str
    file: str
    line: Optional[int]
    message: str
    suggestion: Optional[str] = None
    error_type: Optional[str] = None

class StartupValidator:
    """Comprehensive startup validation system"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = project_root / "src"
        self.issues: List[ValidationIssue] = []
        self.modules_found: Set[str] = set()
        self.imports_map: Dict[str, Set[str]] = {}

    def validate_all(self) -> bool:
        """Run all validations and return True if startup should proceed"""
        logger.info("🔍 Starting comprehensive project validation...")

        # 1. Project Structure Validation
        self._validate_project_structure()

        # 2. Python Module Validation
        self._validate_python_modules()

        # 3. Import Dependency Validation
        self._validate_imports()

        # 4. Configuration Validation
        self._validate_configuration()

        # 5. Agent System Validation
        self._validate_agent_system()

        # 6. API Endpoint Validation
        self._validate_api_endpoints()

        # 7. Database Schema Validation
        self._validate_database()

        # Report results
        self._report_results()

        # Return True only if no ERROR level issues
        return not any(issue.level == ValidationLevel.ERROR for issue in self.issues)

    def _validate_project_structure(self):
        """Validate expected project structure exists"""
        logger.info("📁 Validating project structure...")

        required_dirs = [
            "src/core",
            "src/api/v1/endpoints",
            "src/services",
            "src/core/agents",
            "src/core/config",
            "src/core/memory",
            "logs"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    module="project_structure",
                    file=str(full_path),
                    line=None,
                    message=f"Required directory missing: {dir_path}",
                    suggestion=f"Create directory: mkdir -p {dir_path}"
                ))
            else:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.SUCCESS,
                    module="project_structure",
                    file=str(full_path),
                    line=None,
                    message=f"Directory exists: {dir_path}"
                ))

    def _validate_python_modules(self):
        """Validate all Python modules can be imported"""
        logger.info("🐍 Validating Python modules...")

        for py_file in self.src_root.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_path = self._get_module_path(py_file)
            self.modules_found.add(module_path)

            try:
                # Parse AST to check syntax
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                ast.parse(content, filename=str(py_file))

                self.issues.append(ValidationIssue(
                    level=ValidationLevel.SUCCESS,
                    module=module_path,
                    file=str(py_file),
                    line=None,
                    message="Syntax validation passed"
                ))

            except SyntaxError as e:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    module=module_path,
                    file=str(py_file),
                    line=e.lineno,
                    message=f"Syntax error: {e.msg}",
                    error_type="SyntaxError"
                ))
            except Exception as e:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    module=module_path,
                    file=str(py_file),
                    line=None,
                    message=f"Module validation failed: {str(e)}",
                    error_type=type(e).__name__
                ))

    def _validate_imports(self):
        """Validate all imports are resolvable"""
        logger.info("📦 Validating imports...")

        for py_file in self.src_root.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_path = self._get_module_path(py_file)
            imports = self._extract_imports(py_file)
            self.imports_map[module_path] = imports

            for import_stmt in imports:
                if import_stmt.startswith("src."):
                    # Internal import - check if module exists
                    if import_stmt not in self.modules_found:
                        # Check if it's a partial import
                        found = any(mod.startswith(import_stmt) for mod in self.modules_found)
                        if not found:
                            self.issues.append(ValidationIssue(
                                level=ValidationLevel.ERROR,
                                module=module_path,
                                file=str(py_file),
                                line=None,
                                message=f"Import not found: {import_stmt}",
                                suggestion="Check module path or create missing module",
                                error_type="ImportError"
                            ))

    def _validate_configuration(self):
        """Validate configuration settings"""
        logger.info("⚙️ Validating configuration...")

        try:
            from src.core.config.settings import get_settings
            settings = get_settings()

            # Check critical settings
            if not any([settings.openai_api_key, settings.anthropic_api_key, settings.gemini_api_key]):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    module="configuration",
                    file="settings.py",
                    line=None,
                    message="No LLM API keys configured",
                    suggestion="Set at least one API key: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY"
                ))

            # Validate database path
            db_path = Path(settings.get_database_path())
            if not db_path.parent.exists():
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    module="configuration",
                    file="settings.py",
                    line=None,
                    message=f"Database directory missing: {db_path.parent}",
                    suggestion=f"Create directory: mkdir -p {db_path.parent}"
                ))

        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                module="configuration",
                file="settings.py",
                line=None,
                message=f"Configuration load failed: {str(e)}",
                error_type=type(e).__name__
            ))

    def _validate_agent_system(self):
        """Validate agent system integrity"""
        logger.info("🤖 Validating agent system...")

        try:
            from src.core.agents.registry import discover_agents
            agents = discover_agents()

            if not agents:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    module="agent_system",
                    file="registry.py",
                    line=None,
                    message="No agents discovered",
                    suggestion="Ensure agent folders exist in src/core/agents/"
                ))
            else:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.SUCCESS,
                    module="agent_system",
                    file="registry.py",
                    line=None,
                    message=f"Discovered {len(agents)} agents: {list(agents.keys())}"
                ))

            # Validate each agent
            for key, spec in agents.items():
                agent_path = Path(spec.folder)

                # Check required files
                required_files = ["agent.yaml", "mcp.json"]
                for req_file in required_files:
                    file_path = agent_path / req_file
                    if not file_path.exists():
                        self.issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            module="agent_system",
                            file=str(agent_path),
                            line=None,
                            message=f"Agent {key} missing {req_file}",
                            suggestion=f"Create {req_file} in {agent_path}"
                        ))

        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                module="agent_system",
                file="registry.py",
                line=None,
                message=f"Agent system validation failed: {str(e)}",
                error_type=type(e).__name__
            ))

    def _validate_api_endpoints(self):
        """Validate API endpoint definitions"""
        logger.info("🌐 Validating API endpoints...")

        try:
            from src.api.v1 import router

            # Count routes
            route_count = len([route for route in router.routes])

            self.issues.append(ValidationIssue(
                level=ValidationLevel.SUCCESS,
                module="api_system",
                file="v1/__init__.py",
                line=None,
                message=f"API router loaded with {route_count} routes"
            ))

        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                module="api_system",
                file="v1/__init__.py",
                line=None,
                message=f"API validation failed: {str(e)}",
                error_type=type(e).__name__
            ))

    def _validate_database(self):
        """Validate database connectivity and schema"""
        logger.info("🗄️ Validating database...")

        try:
            from src.core.memory import session_store

            # Test basic operations
            groups = session_store.list_groups()

            self.issues.append(ValidationIssue(
                level=ValidationLevel.SUCCESS,
                module="database",
                file="session_store.py",
                line=None,
                message=f"Database connected successfully, {len(groups)} groups found"
            ))

        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                module="database",
                file="session_store.py",
                line=None,
                message=f"Database validation failed: {str(e)}",
                error_type=type(e).__name__
            ))

    def _get_module_path(self, py_file: Path) -> str:
        """Convert file path to module path"""
        rel_path = py_file.relative_to(self.project_root)
        module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        return ".".join(module_parts)

    def _extract_imports(self, py_file: Path) -> Set[str]:
        """Extract all import statements from a Python file"""
        imports = set()
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

        except Exception:
            pass  # Skip files that can't be parsed

        return imports

    def _report_results(self):
        """Report validation results"""
        error_count = sum(1 for issue in self.issues if issue.level == ValidationLevel.ERROR)
        warning_count = sum(1 for issue in self.issues if issue.level == ValidationLevel.WARNING)
        success_count = sum(1 for issue in self.issues if issue.level == ValidationLevel.SUCCESS)

        logger.info(f"\n🎯 Validation Complete:")
        logger.info(f"   ✅ Successes: {success_count}")
        logger.info(f"   ⚠️  Warnings:  {warning_count}")
        logger.info(f"   ❌ Errors:    {error_count}")

        # Report errors and warnings
        for issue in self.issues:
            if issue.level in [ValidationLevel.ERROR, ValidationLevel.WARNING]:
                emoji = "❌" if issue.level == ValidationLevel.ERROR else "⚠️"
                logger.log(
                    logging.ERROR if issue.level == ValidationLevel.ERROR else logging.WARNING,
                    f"{emoji} [{issue.module}] {issue.file}:{issue.line or 'N/A'} - {issue.message}"
                )
                if issue.suggestion:
                    logger.info(f"   💡 Suggestion: {issue.suggestion}")

        if error_count == 0:
            logger.info("🚀 All validations passed - startup can proceed")
        else:
            logger.error(f"🚫 {error_count} critical issues found - startup blocked")

def validate_startup(project_root: Path) -> bool:
    """Main validation entry point"""
    validator = StartupValidator(project_root)
    return validator.validate_all()