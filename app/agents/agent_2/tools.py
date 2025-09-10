"""
Custom tools for Web & UI Agent
All functions decorated with @agent_tool will be auto-discovered
"""
from app.agents.base_agent import agent_tool
from typing import Dict, Any, Optional
import requests
import time
from urllib.parse import urlparse

@agent_tool
def check_website_status(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Check if a website is accessible and get status information
    Args:
        url: The URL to check
        timeout: Request timeout in seconds
    Returns:
        Dictionary with status information
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = time.time() - start_time
        
        return {
            "url": url,
            "status_code": response.status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "accessible": response.status_code == 200,
            "headers": dict(response.headers),
            "content_length": len(response.content)
        }
    except Exception as e:
        return {
            "url": url,
            "accessible": False,
            "error": str(e),
            "status_code": None
        }

@agent_tool
def validate_url_format(url: str) -> Dict[str, Any]:
    """
    Validate URL format and extract components
    Args:
        url: URL to validate
    Returns:
        Dictionary with validation results and URL components
    """
    try:
        parsed = urlparse(url)
        
        return {
            "valid": bool(parsed.scheme and parsed.netloc),
            "scheme": parsed.scheme,
            "domain": parsed.netloc,
            "path": parsed.path,
            "query": parsed.query,
            "fragment": parsed.fragment,
            "full_url": url
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "full_url": url
        }

@agent_tool
def generate_test_script(test_name: str, url: str, test_type: str = "basic") -> str:
    """
    Generate test script templates for different frameworks
    Args:
        test_name: Name of the test
        url: URL to test
        test_type: Type of test (basic, form, navigation)
    Returns:
        Test script code
    """
    if test_type == "basic":
        return f"""// Basic web test for {test_name}
const {{ test, expect }} = require('@playwright/test');

test('{test_name}', async ({{ page }}) => {{
    // Navigate to the page
    await page.goto('{url}');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Basic checks
    await expect(page).toHaveTitle(/./);
    
    // Take screenshot
    await page.screenshot({{ path: '{test_name.lower().replace(" ", "_")}.png' }});
}});"""
    
    elif test_type == "form":
        return f"""// Form test for {test_name}
const {{ test, expect }} = require('@playwright/test');

test('{test_name}', async ({{ page }}) => {{
    await page.goto('{url}');
    
    // Fill form fields (customize as needed)
    await page.fill('[data-testid="input-field"]', 'test value');
    await page.click('[data-testid="submit-button"]');
    
    // Verify submission
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
}});"""
    
    elif test_type == "navigation":
        return f"""// Navigation test for {test_name}
const {{ test, expect }} = require('@playwright/test');

test('{test_name}', async ({{ page }}) => {{
    await page.goto('{url}');
    
    // Test navigation links
    const links = await page.locator('a[href]').all();
    console.log(`Found ${{links.length}} navigation links`);
    
    // Click first internal link
    if (links.length > 0) {{
        await links[0].click();
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(/./);
    }}
}});"""
    
    return f"# Test script template for {test_name}"

@agent_tool
def extract_page_info(url: str) -> Dict[str, Any]:
    """
    Extract basic information from a webpage
    Args:
        url: URL to analyze
    Returns:
        Dictionary with page information
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        response = requests.get(url, timeout=10)
        html = response.text
        
        # Simple extraction (can be enhanced with BeautifulSoup)
        title = ""
        if "<title>" in html and "</title>" in html:
            title = html.split("<title>")[1].split("</title>")[0].strip()
        
        # Count basic elements
        link_count = html.count('<a href=')
        form_count = html.count('<form')
        button_count = html.count('<button')
        
        return {
            "url": url,
            "title": title,
            "content_length": len(html),
            "link_count": link_count,
            "form_count": form_count,
            "button_count": button_count,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

# No need to export AVAILABLE_TOOLS - auto-discovery finds @agent_tool functions
