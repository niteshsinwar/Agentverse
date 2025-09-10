"""
Custom tools for [Agent Name]
All functions decorated with @agent_tool will be auto-discovered
"""
from app.agents.base_agent import agent_tool
from typing import Dict, Any, List, Optional

@agent_tool
def example_tool(input_text: str, option: str = "default") -> Dict[str, Any]:
    """
    Example tool that demonstrates the standard pattern
    Args:
        input_text: The text to process
        option: Processing option with default value
    Returns:
        Dictionary with processed results
    """
    # Your tool implementation here
    result = f"Processed '{input_text}' with option '{option}'"
    
    return {
        "success": True,
        "result": result,
        "input": input_text,
        "option_used": option
    }

@agent_tool
def another_example_tool(data: List[str]) -> str:
    """
    Another example tool showing different return type
    Args:
        data: List of strings to process
    Returns:
        Processed string result
    """
    if not data:
        return "No data provided"
    
    return f"Processed {len(data)} items: {', '.join(data[:3])}{'...' if len(data) > 3 else ''}"

# Add your custom tools here following the same pattern:
# 1. Decorate with @agent_tool
# 2. Add type hints for parameters and return value  
# 3. Include clear docstring with Args and Returns
# 4. Handle edge cases gracefully

# No need to export anything - auto-discovery finds @agent_tool functions