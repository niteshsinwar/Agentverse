"""
MCP OAuth Manager
Handles OAuth flow for remote MCP servers (mcp-remote)
"""

import asyncio
import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from src.core.utils.mcp_auth import (
    requires_oauth,
    has_valid_oauth_token,
    get_remote_server_url,
    BASE_AUTH_DIR
)

logger = logging.getLogger(__name__)


class OAuthFlowTimeout(Exception):
    """Raised when OAuth flow times out"""
    pass


class OAuthFlowError(Exception):
    """Raised when OAuth flow fails"""
    pass


class MCPOAuthManager:
    """Manages OAuth authentication for remote MCP servers"""

    def __init__(self):
        self.active_flows: Dict[str, Dict[str, Any]] = {}

    def needs_oauth(self, server_name: str, command: str, args: list) -> bool:
        """Check if server requires OAuth and doesn't have valid token"""
        if not requires_oauth(command, args):
            return False

        # Get auth store path
        auth_store = self._get_auth_store_path(server_name)
        return not has_valid_oauth_token(auth_store)

    def _get_auth_store_path(self, server_name: str) -> Path:
        """Get auth store path for server"""
        safe_name = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in server_name)
        return BASE_AUTH_DIR / f"{safe_name}-auth.json"

    async def initiate_oauth_flow(
        self,
        server_name: str,
        command: str,
        args: list,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Initiate OAuth flow for mcp-remote server.

        This runs mcp-remote with a simple test connection that will trigger
        OAuth flow if no valid token exists. mcp-remote will open browser.

        Returns:
            {
                "success": bool,
                "auth_store": str,
                "message": str,
                "token_info": {...} (if successful)
            }
        """
        auth_store = self._get_auth_store_path(server_name)
        remote_url = get_remote_server_url(args)

        logger.info(f"🔐 Initiating OAuth flow for '{server_name}' -> {remote_url}")

        # Prepare args with --auth-store
        oauth_args = list(args)
        if '--auth-store' not in oauth_args:
            oauth_args.extend(['--auth-store', str(auth_store)])

        # Build command
        full_command = [command] + oauth_args

        # Create auth store directory but NOT the file
        # Let mcp-remote create it during OAuth flow
        auth_store.parent.mkdir(parents=True, exist_ok=True)

        # Delete existing empty/invalid auth file to force fresh OAuth
        if auth_store.exists() and not has_valid_oauth_token(auth_store):
            logger.info(f"Removing invalid auth file: {auth_store}")
            auth_store.unlink()

        # Store initial state
        flow_id = f"{server_name}_{int(time.time())}"
        self.active_flows[flow_id] = {
            'server_name': server_name,
            'auth_store': str(auth_store),
            'started_at': time.time(),
            'status': 'initializing'
        }

        try:
            # Start mcp-remote process with stdin/stdout pipes
            # Send an initialize message to trigger OAuth
            logger.info(f"🚀 Starting mcp-remote process: {' '.join(full_command)}")

            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**env} if env else None
            )

            self.active_flows[flow_id]['process'] = process
            self.active_flows[flow_id]['status'] = 'waiting_for_auth'

            # Send an initialize request to trigger server connection and OAuth
            # This will cause mcp-remote to connect to the server, which will
            # trigger OAuth flow if no valid token exists
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "agentverse",
                        "version": "1.0.0"
                    }
                }
            }

            # Send the initialize message
            init_json = json.dumps(init_request) + "\n"
            process.stdin.write(init_json.encode())
            await process.stdin.drain()

            # Wait a moment for initialize response
            await asyncio.sleep(2)

            # Now send a tools/list request which will trigger OAuth if needed
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            tools_json = json.dumps(tools_request) + "\n"
            process.stdin.write(tools_json.encode())
            await process.stdin.drain()

            # Monitor auth store for token
            result = await self._wait_for_token(
                flow_id=flow_id,
                auth_store=auth_store,
                process=process,
                timeout=timeout
            )

            # Terminate process after getting token
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

            return result

        except Exception as e:
            logger.error(f"❌ OAuth flow failed for '{server_name}': {e}")
            if flow_id in self.active_flows:
                del self.active_flows[flow_id]
            raise OAuthFlowError(f"OAuth flow failed: {str(e)}")

    async def _wait_for_token(
        self,
        flow_id: str,
        auth_store: Path,
        process: asyncio.subprocess.Process,
        timeout: float
    ) -> Dict[str, Any]:
        """
        Wait for OAuth token to appear in auth store.
        Monitors both the file and process output.
        """
        start_time = time.time()
        check_interval = 1.0  # Check every second
        stderr_output = []

        logger.info(f"⏳ Waiting for OAuth token in {auth_store}")
        logger.info(f"🌐 Browser should open automatically for authentication")

        # Create a task to read stderr
        async def read_stderr():
            while True:
                try:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode().strip()
                    if decoded:  # Only log non-empty lines
                        stderr_output.append(decoded)
                        # Print to console for debugging
                        print(f"[mcp-remote] {decoded}")
                        logger.info(f"mcp-remote: {decoded}")
                except Exception as e:
                    logger.debug(f"Error reading stderr: {e}")
                    break

        stderr_task = asyncio.create_task(read_stderr())

        try:
            while time.time() - start_time < timeout:
                # Check if process died unexpectedly
                if process.returncode is not None:
                    # Process ended - check if we got a token anyway
                    if has_valid_oauth_token(auth_store):
                        # Got token before process died - that's OK!
                        break
                    else:
                        # Process died without token - that's an error
                        await stderr_task
                        error_msg = "\n".join(stderr_output[-10:])  # Last 10 lines
                        raise OAuthFlowError(
                            f"mcp-remote process terminated without completing OAuth.\n"
                            f"Last output:\n{error_msg}"
                        )

                # Check auth store for token
                if has_valid_oauth_token(auth_store):
                    token_data = json.loads(auth_store.read_text())

                    logger.info(f"✅ OAuth token received for '{self.active_flows[flow_id]['server_name']}'")

                    self.active_flows[flow_id]['status'] = 'completed'
                    self.active_flows[flow_id]['completed_at'] = time.time()

                    return {
                        'success': True,
                        'auth_store': str(auth_store),
                        'message': 'OAuth authentication successful',
                        'token_info': {
                            'has_access_token': bool(token_data.get('access_token')),
                            'has_refresh_token': bool(token_data.get('refresh_token')),
                            'expires_at': token_data.get('expires_at')
                        }
                    }

                # Wait before next check
                await asyncio.sleep(check_interval)

            # Timeout
            await stderr_task
            error_msg = "\n".join(stderr_output[-10:])  # Last 10 lines
            raise OAuthFlowTimeout(
                f"OAuth flow timed out after {timeout}s. "
                f"Browser authentication may not have been completed.\n"
                f"Last output:\n{error_msg}"
            )

        finally:
            stderr_task.cancel()
            try:
                await stderr_task
            except asyncio.CancelledError:
                pass

    def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active OAuth flow"""
        return self.active_flows.get(flow_id)

    def cleanup_flow(self, flow_id: str):
        """Clean up an OAuth flow"""
        if flow_id in self.active_flows:
            flow = self.active_flows[flow_id]
            if 'process' in flow:
                try:
                    flow['process'].terminate()
                except:
                    pass
            del self.active_flows[flow_id]


# Global instance
oauth_manager = MCPOAuthManager()
