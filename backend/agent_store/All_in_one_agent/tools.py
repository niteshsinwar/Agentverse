# file_operations_tool
# Comprehensive file system operations including read, write, list, copy, move, and search

import os
import re
from src.core.agents.base_agent import agent_tool

@agent_tool
def read_file(file_path: str) -> str:
    """Read content from a file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

@agent_tool
def write_file(file_path: str, content: str) -> bool:
    """Write content to a file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

@agent_tool
def list_files(directory: str = '.') -> list:
    """List files in a directory"""
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

@agent_tool
def search_in_files(pattern: str, directory: str = '.') -> list:
    """Search for pattern in files"""
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        results.append(file_path)
            except:
                continue
    return results


# web_scraping_tool
# Extract data from web pages, APIs, and online resources

import requests
from bs4 import BeautifulSoup
import json
from src.core.agents.base_agent import agent_tool

@agent_tool
def fetch_webpage(url: str) -> str:
    """Fetch webpage content"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching webpage: {e}"

@agent_tool
def extract_text(html_content: str) -> str:
    """Extract text from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(strip=True)

@agent_tool
def fetch_api_data(url: str, headers: dict = None) -> dict:
    """Fetch data from REST API"""
    try:
        response = requests.get(url, headers=headers or {}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@agent_tool
def extract_links(html_content: str) -> list:
    """Extract all links from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return [a.get('href') for a in soup.find_all('a', href=True)]


