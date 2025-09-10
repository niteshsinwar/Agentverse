import pytest
from app.mcp.client import MCPManager


def test_manager_from_config_handles_empty():
    m = MCPManager.from_config({})
    assert m.servers == {}


def test_manager_from_config_new_format():
    cfg = {
        "enabled_servers": [
            {"name": "s1", "command": "echo", "args": ["{}"]},
            {"name": "s2", "command": "echo", "args": ["{}"]},
        ]
    }
    m = MCPManager.from_config(cfg)
    assert set(m.servers.keys()) == {"s1", "s2"}


