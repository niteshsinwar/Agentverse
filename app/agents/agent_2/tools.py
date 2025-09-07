"""
Custom tools for UI Testing Agent
"""

def take_screenshot(url: str, filename: str = None) -> str:
    """Take a screenshot of a webpage"""
    # Implementation would go here
    return f"Screenshot taken for {url}"

def validate_element_exists(selector: str) -> bool:
    """Check if an element exists on the page"""
    # Implementation would go here
    return True

def get_page_title() -> str:
    """Get the current page title"""
    # Implementation would go here
    return "Page Title"

# Export available tools
AVAILABLE_TOOLS = {
    "take_screenshot": take_screenshot,
    "validate_element_exists": validate_element_exists,
    "get_page_title": get_page_title
}
