# Custom Tools
"""
Custom tools for Development Agent
All functions decorated with @agent_tool will be auto-discovered
"""
from src.core.agents.base_agent import agent_tool
from typing import Dict, List, Any

@agent_tool
def validate_code_syntax(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Validate code syntax for various programming languages
    Args:
        code: The code to validate
        language: Programming language (python, javascript, java, etc.)
    Returns:
        Dictionary with validation results
    """
    # Basic implementation - can be enhanced with actual parsers
    if not code.strip():
        return {"valid": False, "errors": ["Code is empty"]}
    
    # Simple heuristic checks
    errors = []
    if language.lower() == "python":
        if code.count("(") != code.count(")"):
            errors.append("Mismatched parentheses")
        if code.count("{") != code.count("}"):
            errors.append("Mismatched curly braces")
    
    return {"valid": len(errors) == 0, "errors": errors, "language": language}

@agent_tool
def generate_test_template(class_name: str, language: str = "python") -> str:
    """
    Generate a test class template for different languages
    Args:
        class_name: Name of the class to test
        language: Programming language
    Returns:
        Test template code
    """
    templates = {
        "python": f"""import unittest

class Test{class_name}(unittest.TestCase):
    def setUp(self):
        # Setup test fixtures
        pass
    
    def test_{class_name.lower()}_basic(self):
        # Basic test case
        pass
    
    def tearDown(self):
        # Clean up
        pass

if __name__ == '__main__':
    unittest.main()""",
        "java": f"""import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.AfterEach;

public class {class_name}Test {{
    @BeforeEach
    void setUp() {{
        // Setup test fixtures
    }}
    
    @Test
    void test{class_name}Basic() {{
        // Basic test case
    }}
    
    @AfterEach
    void tearDown() {{
        // Clean up
    }}
}}""",
        "javascript": f"""const {{ expect }} = require('chai');
const {class_name} = require('../{class_name.lower()}');

describe('{class_name}', () => {{
    beforeEach(() => {{
        // Setup test fixtures
    }});
    
    it('should work with basic functionality', () => {{
        // Basic test case
    }});
    
    afterEach(() => {{
        // Clean up
    }});
}});"""
    }
    
    return templates.get(language.lower(), f"# Test template for {class_name} in {language}")

@agent_tool
def extract_code_dependencies(code: str, language: str = "python") -> List[str]:
    """
    Extract dependencies/imports from code
    Args:
        code: Code to analyze
        language: Programming language
    Returns:
        List of dependencies found
    """
    dependencies = []
    lines = code.split('\n')
    
    if language.lower() == "python":
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                dependencies.append(line)
    elif language.lower() == "javascript":
        for line in lines:
            line = line.strip()
            if 'require(' in line or 'import ' in line:
                dependencies.append(line)
    elif language.lower() == "java":
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                dependencies.append(line)
    
    return dependencies

# No need to export AVAILABLE_TOOLS - auto-discovery finds @agent_tool functions

