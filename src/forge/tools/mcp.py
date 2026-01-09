"""MCP (Model Context Protocol) Tool Integration"""
import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    server: str
    input_schema: dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPToolResult:
    """Result from an MCP tool call."""
    success: bool
    output: Any
    error: str | None = None

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self._tools_cache: list[MCPTool] | None = None
    
    def _run_mcp_cli(self, *args: str, input_json: str | None = None) -> tuple[bool, str]:
        """Run the manus-mcp-cli command."""
        cmd = ["manus-mcp-cli", *args, "--server", self.server_name]
        if input_json:
            cmd.extend(["--input", input_json])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            return False, "MCP command timed out"
        except Exception as e:
            return False, str(e)
    
    def list_tools(self, refresh: bool = False) -> list[MCPTool]:
        """List available tools from the MCP server."""
        if self._tools_cache is not None and not refresh:
            return self._tools_cache
        
        success, output = self._run_mcp_cli("tool", "list")
        if not success:
            logger.error(f"Failed to list MCP tools: {output}")
            return []
        
        try:
            # Parse the output (format depends on manus-mcp-cli)
            tools = []
            # Assuming JSON output
            data = json.loads(output)
            for tool_data in data.get("tools", []):
                tools.append(MCPTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    server=self.server_name,
                    input_schema=tool_data.get("inputSchema", {}),
                ))
            self._tools_cache = tools
            return tools
        except json.JSONDecodeError:
            # Try line-by-line parsing
            tools = []
            for line in output.strip().split("\n"):
                if line.strip():
                    tools.append(MCPTool(
                        name=line.strip(),
                        description="",
                        server=self.server_name,
                    ))
            self._tools_cache = tools
            return tools
    
    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Call an MCP tool with the given arguments."""
        logger.info(f"Calling MCP tool: {tool_name} on server {self.server_name}")
        
        input_json = json.dumps(arguments)
        success, output = self._run_mcp_cli("tool", "call", tool_name, input_json=input_json)
        
        if success:
            try:
                result_data = json.loads(output)
                return MCPToolResult(success=True, output=result_data)
            except json.JSONDecodeError:
                return MCPToolResult(success=True, output=output)
        else:
            return MCPToolResult(success=False, output=None, error=output)
    
    async def call_tool_async(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Async version of call_tool."""
        return await asyncio.to_thread(self.call_tool, tool_name, arguments)


class MCPRegistry:
    """Registry of available MCP servers and their tools."""
    
    # Known MCP servers
    KNOWN_SERVERS = [
        "stripe",
        "notion",
        "canva",
        "gmail",
        "google-calendar",
        "outlook-mail",
        "outlook-calendar",
    ]
    
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
    
    def get_client(self, server_name: str) -> MCPClient:
        """Get or create an MCP client for a server."""
        if server_name not in self._clients:
            self._clients[server_name] = MCPClient(server_name)
        return self._clients[server_name]
    
    def list_all_tools(self) -> dict[str, list[MCPTool]]:
        """List tools from all known servers."""
        all_tools = {}
        for server in self.KNOWN_SERVERS:
            client = self.get_client(server)
            tools = client.list_tools()
            if tools:
                all_tools[server] = tools
        return all_tools
    
    def find_tool(self, tool_name: str) -> tuple[str, MCPTool] | None:
        """Find a tool by name across all servers."""
        for server in self.KNOWN_SERVERS:
            client = self.get_client(server)
            for tool in client.list_tools():
                if tool.name == tool_name:
                    return server, tool
        return None


# Convenience functions
def get_mcp_client(server: str) -> MCPClient:
    """Get an MCP client for a specific server."""
    return MCPClient(server)

def call_mcp_tool(server: str, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
    """Call an MCP tool on a specific server."""
    client = MCPClient(server)
    return client.call_tool(tool_name, arguments)
