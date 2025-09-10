# =========================================
# File: app/mcp/client.py
# Purpose: Production-grade MCP client with proper protocol implementation
# =========================================
from __future__ import annotations
import os
import json
import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
from app.config.settings import settings
from app.telemetry.session_logger import session_logger

logger = logging.getLogger(__name__)

class MCPServerStatus(str, Enum):
    """MCP server status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str

@dataclass
class MCPServerSpec:
    """MCP server specification"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    timeout: float = 30.0
    health_check: bool = True

class MCPServerHandle:
    """Handle for managing MCP server process and communication"""
    
    def __init__(self, name: str, spec: Dict[str, Any]) -> None:
        self.name = name
        self.spec = MCPServerSpec(
            name=name,
            command=spec.get("command", ""),
            args=spec.get("args", []),
            env=spec.get("env", {}),
            timeout=spec.get("timeout", settings.mcp.timeout),
            health_check=spec.get("health_check", True)
        )
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.status = MCPServerStatus.STOPPED
        self.tools_cache: List[MCPTool] = []
        self.last_health_check = 0.0
        self.error_count = 0
        self._lock = asyncio.Lock()
        # Ensure NPX is non-interactive (auto-yes) to avoid hangs
        try:
            if self.spec.command.strip().lower() == "npx":
                normalized = [str(a).strip().lower() for a in self.spec.args]
                if "-y" not in normalized and "--yes" not in normalized:
                    self.spec.args = ["-y", *self.spec.args]
        except Exception:
            pass

    async def start(self) -> bool:
        """Start the MCP server process"""
        async with self._lock:
            if self.status == MCPServerStatus.RUNNING:
                return True
            
            try:
                self.status = MCPServerStatus.STARTING
                logger.info(f"Starting MCP server: {self.name}")
                
                # Prepare environment
                env = os.environ.copy()
                env.update(self.spec.env)
                
                # Expand environment variables in command and args
                command = os.path.expandvars(self.spec.command)
                args = [os.path.expandvars(arg) for arg in self.spec.args]
                
                # Validate command
                if not command:
                    self.status = MCPServerStatus.ERROR
                    logger.error(f"MCP server {self.name} has empty command")
                    return False
                
                # Retry with exponential backoff for robustness
                max_retries = max(1, settings.mcp.max_retries)
                last_error: Optional[Exception] = None
                for attempt in range(1, max_retries + 1):
                    try:
                        # Start process
                        self.proc = await asyncio.create_subprocess_exec(
                            command, *args,
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            env=env
                        )
                        # Perform handshake
                        if await self._handshake():
                            self.status = MCPServerStatus.RUNNING
                            self.error_count = 0
                            logger.info(f"MCP server {self.name} started successfully")
                            return True
                        else:
                            await self.stop()
                            last_error = RuntimeError("Handshake failed")
                            logger.warning(f"MCP server {self.name} handshake failed on attempt {attempt}/{max_retries}")
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Failed to start MCP server {self.name} (attempt {attempt}/{max_retries}): {e}")
                        await self.stop()
                    
                    # Backoff before next attempt
                    if attempt < max_retries:
                        await asyncio.sleep(min(2 ** (attempt - 1), 5))
                
                self.status = MCPServerStatus.ERROR
                self.error_count += 1
                logger.error(f"Failed to start MCP server {self.name} after {max_retries} attempts: {last_error}")
                return False
                
            except Exception as e:
                self.status = MCPServerStatus.ERROR
                self.error_count += 1
                logger.error(f"Failed to start MCP server {self.name}: {e}")
                return False

    async def stop(self) -> None:
        """Stop the MCP server process"""
        async with self._lock:
            if self.proc:
                try:
                    self.proc.terminate()
                    try:
                        await asyncio.wait_for(self.proc.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self.proc.kill()
                        await self.proc.wait()
                except Exception as e:
                    logger.error(f"Error stopping MCP server {self.name}: {e}")
                finally:
                    self.proc = None
                    self.status = MCPServerStatus.STOPPED

    async def _handshake(self) -> bool:
        """Perform MCP handshake and discover tools"""
        if not self.proc:
            return False
        
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "agentic-framework",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send_message(init_request)
            
            # Wait for initialize response
            response = await self._receive_message()
            if not response or response.get("error"):
                logger.error(f"Initialize failed for {self.name}: {response}")
                return False
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self._send_message(initialized_notification)
            
            # Discover tools
            await self._discover_tools()
            
            return True
            
        except Exception as e:
            logger.error(f"Handshake failed for {self.name}: {e}")
            return False

    async def _discover_tools(self) -> None:
        """Discover available tools from the MCP server"""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            await self._send_message(tools_request)
            response = await self._receive_message()
            
            if response and "result" in response and "tools" in response["result"]:
                self.tools_cache = []
                for tool_data in response["result"]["tools"]:
                    tool = MCPTool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description", ""),
                        parameters=tool_data.get("inputSchema", {}),
                        server_name=self.name
                    )
                    self.tools_cache.append(tool)
                
                logger.info(f"Discovered {len(self.tools_cache)} tools for {self.name}")
            
        except Exception as e:
            logger.error(f"Tool discovery failed for {self.name}: {e}")

    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send JSON-RPC message to MCP server"""
        if not self.proc or not self.proc.stdin:
            raise ValueError("MCP server not running")
        
        message_str = json.dumps(message) + "\n"
        self.proc.stdin.write(message_str.encode())
        await self.proc.stdin.drain()

    async def _receive_message(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Receive JSON-RPC message from MCP server"""
        if not self.proc or not self.proc.stdout:
            return None
        
        try:
            # Read lines until a parsable JSON object is found or timeout
            end_time = time.time() + timeout
            while time.time() < end_time:
                line = await asyncio.wait_for(self.proc.stdout.readline(), timeout=max(0.05, end_time - time.time()))
                if not line:
                    # Check if process crashed
                    if self.proc.returncode is not None:
                        logger.error(f"MCP server {self.name} exited with code {self.proc.returncode}")
                        return None
                    continue
                text = line.decode(errors="ignore").strip()
                if not text:
                    continue
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Skip non-JSON noise lines
                    continue
            logger.error(f"Timeout waiting for response from {self.name}")
            return None
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from {self.name}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {self.name}: {e}")
            return None

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if self.status != MCPServerStatus.RUNNING:
            if not await self.start():
                raise RuntimeError(f"MCP server {self.name} is not running")
        
        try:
            max_retries = max(1, settings.mcp.max_retries)
            last_error: Optional[Exception] = None
            for attempt in range(1, max_retries + 1):
                try:
                    call_request = {
                        "jsonrpc": "2.0",
                        "id": int(time.time() * 1000),
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": parameters
                        }
                    }
                    await self._send_message(call_request)
                    response = await self._receive_message()
                    if not response:
                        raise RuntimeError(f"No response from MCP server {self.name}")
                    if "error" in response:
                        error = response["error"]
                        raise RuntimeError(f"MCP error: {error.get('message', 'Unknown error')}")
                    return response.get("result", {})
                except Exception as e:
                    last_error = e
                    logger.warning(f"Tool call '{tool_name}' failed on {self.name} (attempt {attempt}/{max_retries}): {e}")
                    # If process died, try restart before next attempt
                    if self.proc and self.proc.returncode is not None:
                        await self.stop()
                        await self.start()
                    if attempt < max_retries:
                        await asyncio.sleep(min(2 ** (attempt - 1), 5))
            # Out of retries
            raise RuntimeError(f"Tool call '{tool_name}' failed on {self.name} after {max_retries} attempts: {last_error}")
        except Exception as e:
            self.error_count += 1
            logger.error(f"Tool call failed on {self.name}: {e}")
            raise

    async def health_check(self) -> bool:
        """Perform health check on the MCP server"""
        if not self.spec.health_check:
            return True
        
        current_time = time.time()
        if current_time - self.last_health_check < settings.mcp.health_check_interval:
            return self.status == MCPServerStatus.RUNNING
        
        self.last_health_check = current_time
        
        if self.status != MCPServerStatus.RUNNING:
            return await self.start()
        
        # Simple ping test
        try:
            ping_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "ping"
            }
            
            await self._send_message(ping_request)
            response = await asyncio.wait_for(
                self._receive_message(),
                timeout=5.0
            )
            
            return response is not None
            
        except Exception:
            logger.warning(f"Health check failed for {self.name}")
            return False


class MCPManager:
    """Production-grade MCP manager with connection pooling and error handling"""
    
    def __init__(self) -> None:
        self.servers: Dict[str, MCPServerHandle] = {}
        self._health_check_task: Optional[asyncio.Task] = None

    @classmethod
    def from_config(cls, mcp_config: Dict[str, Any]) -> "MCPManager":
        """Create MCP manager from configuration"""
        instance = cls()
        
        # Handle both old and new config formats
        servers_config = mcp_config.get("mcpServers", {})
        if not servers_config:
            servers_config = mcp_config.get("enabled_servers", [])
            if isinstance(servers_config, list):
                # New format: list of server configs
                servers_dict = {}
                for server_config in servers_config:
                    name = server_config.get("name", "")
                    if name:
                        servers_dict[name] = server_config
                servers_config = servers_dict
        
        for name, spec in servers_config.items():
            instance.servers[name] = MCPServerHandle(name, spec)
            logger.info(f"Registered MCP server: {name}")
        
        # Start health check task if enabled
        if settings.mcp.enable_health_checks and instance.servers:
            instance._start_health_check_task()
        
        return instance

    def _start_health_check_task(self) -> None:
        """Start background health check task"""
        if self._health_check_task:
            return
        
        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(settings.mcp.health_check_interval)
                    await self.health_check_all()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health check error: {e}")

        # Only start if there is a running loop (e.g., in app runtime). In sync contexts (like tests), skip.
        try:
            loop = asyncio.get_running_loop()
            self._health_check_task = loop.create_task(health_check_loop())
        except RuntimeError:
            # No running event loop; defer starting until explicitly called under async context
            logger.debug("Skipping health check task start: no running event loop")

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all servers"""
        results = {}
        for name, server in self.servers.items():
            try:
                results[name] = await server.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        return results

    async def start_all(self) -> Dict[str, bool]:
        """Start all MCP servers"""
        results = {}
        for name, server in self.servers.items():
            results[name] = await server.start()
        return results

    async def stop_all(self) -> None:
        """Stop all MCP servers"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        for server in self.servers.values():
            await server.stop()

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """List all available tools across all servers"""
        tools = []
        for server in self.servers.values():
            for tool in server.tools_cache:
                tools.append({
                    "server": tool.server_name,
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                })
        return tools

    def get_server(self, server_name: str) -> Optional[MCPServerHandle]:
        """Get MCP server handle by name"""
        return self.servers.get(server_name)

    async def invoke(self, group_id: str, agent_key: str, server_name: str, tool_name: str, **params) -> Any:
        """Invoke MCP tool with full logging and error handling"""
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server '{server_name}'")
        
        server = self.servers[server_name]
        start_time = time.time()
        
        try:
            # Log MCP call start
            session_logger.log_mcp_call(
                session_id=group_id,
                agent_id=agent_key, 
                server_name=server_name,
                tool_name=tool_name,
                params=params
            )
            
            # Execute the tool call
            result = await server.call_tool(tool_name, params)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful result
            session_logger.log_mcp_call(
                session_id=group_id,
                agent_id=agent_key,
                server_name=server_name,
                tool_name=tool_name,
                params=params,
                duration_ms=duration_ms,
                result=result
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            session_logger.log_mcp_call(
                session_id=group_id,
                agent_id=agent_key,
                server_name=server_name,
                tool_name=tool_name,
                params=params,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            raise


# Global MCP manager - will be initialized when needed
mcp_manager: Optional[MCPManager] = None
