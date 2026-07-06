import os
import json
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.servers = {}
        self.exit_stack = AsyncExitStack()
        
        # Load configuration safely
        self.config = {"mcp_servers": {}}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                print(f"[Warning] {config_path} is empty or invalid JSON. Using default empty config.")

    async def connect_all(self):
        """Connects to all servers defined in config.json"""
        mcp_configs = self.config.get("mcp_servers", {})
        
        for server_name, server_info in mcp_configs.items():
            try:
                # Merge current environment with specific token variables
                env = os.environ.copy()
                
                # Process environment variables from config
                for key, val in server_info.get("env", {}).items():
                    if val == "use_env_var":
                        # Ensure the key exists in our environment (loaded from .env)
                        if key not in env:
                            print(f"[MCP] Warning: {key} not found in .env file")
                    else:
                        # Fallback if hardcoded in config
                        env[key] = val

                # Use explicit command and args for Windows compatibility
                server_params = StdioServerParameters(
                    command=server_info["command"],
                    args=server_info.get("args", []),
                    env=env
                )
                
                # Establish the stdio connection
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read, write = stdio_transport
                
                # Create and initialize the session
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                self.servers[server_name] = session
                print(f"[MCP] Successfully connected to {server_name} server.")
                
            except Exception as e:
                print(f"[MCP] Failed to connect to {server_name}: {str(e)}")

    async def get_all_tools(self):
        """Fetches tools from all connected MCP servers."""
        all_tools = []
        for server_name, session in self.servers.items():
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    # Format to match OpenAI's expected tool schema
                    all_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": f"[{server_name} MCP] {tool.description}",
                            "parameters": tool.inputSchema
                        }
                    })
            except Exception as e:
                print(f"[MCP] Error fetching tools from {server_name}: {str(e)}")
        return all_tools

    async def call_tool(self, tool_name: str, args: dict):
        """Routes a tool call to the correct MCP server."""
        for server_name, session in self.servers.items():
            # Check if this server owns the tool
            response = await session.list_tools()
            if any(t.name == tool_name for t in response.tools):
                try:
                    result = await session.call_tool(tool_name, arguments=args)
                    # Extract the text content from the MCP result
                    if result.content:
                        return {"status": "success", "result": result.content[0].text}
                    return {"status": "success", "result": "Tool executed with no output."}
                except Exception as e:
                    return {"error": f"MCP tool execution failed: {str(e)}"}
                    
        return {"error": f"Tool {tool_name} not found on any connected MCP server."}

    async def cleanup(self):
        """Closes all connections."""
        await self.exit_stack.aclose()