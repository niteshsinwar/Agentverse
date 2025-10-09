"""
Template tools for a custom AgentVerse agent.

All functions decorated with @agent_tool are auto-discovered and become part of
the agent's capability set. Replace the placeholders below with logic that
talks to your systems, runs scripts, or implements business workflows.
"""

from typing import Any, Dict
from src.core.agents.base_agent import agent_tool


@agent_tool
def hello_world(name: str = "developer") -> str:
    """
    Minimal example tool that can be invoked by your agent.

    Args:
        name: Optional name to greet.
    Returns:
        Friendly greeting string.
    """
    return f"Hello {name}! This is your new template agent ready for customization."


@agent_tool
def create_task_template(title: str, description: str = "") -> Dict[str, Any]:
    """
    Generate a simple dictionary payload that you can adapt for task tracking,
    issue creation, or automation workflows. Extend this function to call your
    internal APIs or trigger scripts.
    """
    return {
        "title": title,
        "description": description or "Add task details here.",
        "status": "draft",
        "owner": "template-agent",
    }
