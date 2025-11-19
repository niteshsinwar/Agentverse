"""Utility helpers for managing MCP remote OAuth token stores."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


BASE_AUTH_DIR = Path('.agentverse/mcp_auth').resolve()
BASE_AUTH_DIR.mkdir(parents=True, exist_ok=True)


def _is_remote_bridge(command: str, args: Iterable[str]) -> bool:
    command_lower = (command or '').lower()
    if 'mcp-remote' in command_lower:
        return True
    return any('mcp-remote' in (arg or '').lower() for arg in args)


def requires_oauth(command: str, args: List[str]) -> bool:
    """Check if MCP server requires OAuth authentication (i.e., uses mcp-remote)."""
    return _is_remote_bridge(command, args)


def has_valid_oauth_token(auth_store_path: Path) -> bool:
    """Check if a valid OAuth token exists in the auth store directory.

    mcp-remote stores tokens in a subdirectory structure like:
    {auth_dir}/mcp-remote-{version}/{hash}_tokens.json

    Args:
        auth_store_path: Directory path for the MCP server's auth storage
                        e.g., .agentverse/mcp_auth/jira_work/

    Returns:
        True if valid access_token found, False otherwise
    """
    # Ensure we're working with a directory
    if auth_store_path.is_file():
        # Legacy: might be a file path, check parent directory
        auth_dir = auth_store_path.parent
    else:
        auth_dir = auth_store_path

    if not auth_dir.exists():
        return False

    # Look for mcp-remote-* subdirectories
    for subdir in auth_dir.glob("mcp-remote-*"):
        if not subdir.is_dir():
            continue

        # Look for *_tokens.json files
        for token_file in subdir.glob("*_tokens.json"):
            try:
                content = token_file.read_text().strip()
                if content:
                    token_data = json.loads(content)
                    if token_data.get('access_token'):
                        logger.debug(f"Found valid OAuth token at {token_file}")
                        return True
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Invalid token file at {token_file}: {e}")

    return False


def get_remote_server_url(args: List[str]) -> Optional[str]:
    """Extract remote server URL from mcp-remote args."""
    # URL is typically the last arg after mcp-remote
    # e.g., ["mcp-remote", "https://mcp.atlassian.com/v1/sse"]
    for arg in reversed(args):
        if arg.startswith('http://') or arg.startswith('https://'):
            return arg
    return None


def _default_auth_store_path(server_name: str) -> Path:
    """Get the auth directory for a specific MCP server.

    Returns a directory path like: .agentverse/mcp_auth/{server_name}/
    This ensures each server gets its own isolated auth storage.
    """
    safe = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in (server_name or 'mcp'))
    return (BASE_AUTH_DIR / safe).resolve()


def ensure_remote_auth_args(
    server_name: str,
    spec: Dict[str, any],
    command: str,
    original_args: Iterable[str],
) -> List[str]:
    """Prepare args for mcp-remote and set up auth store path.

    Note: mcp-remote doesn't use --auth-store flag. Instead, it uses
    MCP_REMOTE_CONFIG_DIR environment variable (set in prepare_remote_bridge_env).
    This function just determines the auth store path and stores it in spec.
    """
    args = list(original_args)

    if not _is_remote_bridge(command, args):
        return args

    # Determine auth directory path (one directory per MCP server for isolation)
    configured = spec.get('auth_store')
    if configured:
        auth_dir_path = Path(configured).expanduser().resolve()
    else:
        auth_dir_path = _default_auth_store_path(server_name)

    # Create auth directory structure
    auth_dir_path.mkdir(parents=True, exist_ok=True)

    # Store resolved path for use in prepare_remote_bridge_env
    spec.setdefault('_resolved_auth_store', str(auth_dir_path))
    logger.debug("Using MCP auth directory %s for %s", auth_dir_path, server_name)

    return [str(item) for item in args]


def prepare_remote_bridge_env(auth_store_dir: Path, env: Dict[str, str] | None) -> Dict[str, str]:
    """Prepare environment for mcp-remote with custom auth storage location.

    Uses MCP_REMOTE_CONFIG_DIR to override the default ~/.mcp-auth location.
    Each MCP server gets its own directory for complete token isolation.

    Args:
        auth_store_dir: Directory path for this specific MCP server's auth storage
                       e.g., .agentverse/mcp_auth/jira_work/
        env: Existing environment variables to merge with

    Returns:
        Environment dict with MCP_REMOTE_CONFIG_DIR set

    Note:
        Uses as_posix() for cross-platform compatibility. Node.js (which runs mcp-remote)
        handles forward slashes correctly on all platforms including Windows.
    """
    cleaned = {k: v for k, v in (env or {}).items() if not k.upper().startswith('MCP_REMOTE_')}
    # mcp-remote uses MCP_REMOTE_CONFIG_DIR to override ~/.mcp-auth
    # Set to the server-specific directory for token isolation
    # Use as_posix() to ensure forward slashes work on Windows too
    cleaned['MCP_REMOTE_CONFIG_DIR'] = auth_store_dir.as_posix()
    return cleaned


__all__ = [
    'ensure_remote_auth_args',
    'prepare_remote_bridge_env',
    'BASE_AUTH_DIR',
    'requires_oauth',
    'has_valid_oauth_token',
    'get_remote_server_url'
]
