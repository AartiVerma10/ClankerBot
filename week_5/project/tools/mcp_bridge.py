import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPManager:
    def __init__(self, config, exit_stack):
        self.config = config
        self.exit_stack = exit_stack
        self.servers = {}

    async def connect_all(self):
        mcp_configs = self.config.get("mcp_servers", {})
        for server_name, server_info in mcp_configs.items():
            try:
                env = os.environ.copy()
                # Apply environment overrides if specified
                if "env" in server_info:
                    env.update(server_info["env"])

                server_params = StdioServerParameters(
                    command=server_info["command"],
                    args=server_info.get("args", []),
                    env=env
                )
                
                # Robust connection handling
                transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read, write = transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                self.servers[server_name] = session
                print(f"[MCP] Successfully connected to {server_name}.")
            except Exception as e:
                print(f"[MCP] Failed to connect to {server_name}: {e}")

    async def get_all_tools(self):
        all_tools = []
        for server_name, session in self.servers.items():
            try:
                response = await session.list_tools()
                for tool in response.tools:
                    # DEBUG: Print tool discovery
                    print(f"[DEBUG] Registering tool: {tool.name} from {server_name}")
                    all_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": f"[{server_name} MCP] {tool.description}",
                            "parameters": tool.inputSchema
                        }
                    })
            except Exception as e:
                print(f"[MCP] Tool fetch failed for {server_name}: {e}")
        return all_tools

    async def call_tool(self, name: str, args: dict):
        for server_name, session in self.servers.items():
            try:
                # Attempt to call the tool on the current server
                response = await session.call_tool(name, arguments=args)
                
                # Check if the server returned an explicit error
                if response.isError:
                    return {"error": f"[{server_name}] {response.content}"}
                
                # Extract the text content from the MCP response
                results = []
                for item in response.content:
                    if item.type == "text":
                        results.append(item.text)
                    else:
                        results.append(str(item))
                        
                return {"status": "success", "data": "\n".join(results)}
                
            except Exception:
                # If the tool doesn't exist on this server, it will throw an exception.
                # We catch it and silently continue to check the next server.
                continue
                
        # If the loop finishes without returning, no server had the tool (or they all failed)
        raise Exception(f"Tool '{name}' not found or failed on all connected MCP servers.")