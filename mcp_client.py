# mcp_client.py
"""
MCP client that connects to the local MCP server using stdio transport (PythonStdioTransport).
Provides reusable functions/classes for integration.
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

class MCPClientWrapper:
    def __init__(self, server_scripts=None):
        if server_scripts is None:
            server_scripts = ["mcp_server.py", "email_mcp_server.py"]
        
        self.server_scripts = server_scripts
        
        # Configure multiple servers
        server_configs = {}
        for i, script in enumerate(server_scripts):
            server_path = os.path.abspath(script)
            server_name = f"server_{i}" if len(server_scripts) > 1 else "local_server"
            
            # Use script name as server identifier for better naming
            if "email" in script:
                server_name = "email_server"
            elif "mcp_server" in script:
                server_name = "main_server"
            
            server_configs[server_name] = {
                "command": "python",
                "args": [server_path],
                "transport": "stdio",
            }
        
        # MultiServerMCPClient expects a dictionary of server configurations
        self.client = MultiServerMCPClient(server_configs)

    async def list_tools(self):
        # Use direct method call instead of context manager
        return await self.client.get_tools()

    async def invoke_tool(self, tool_name, *args, **kwargs):
        # Use direct method call to get tool and invoke it
        tool = await self.client.get_tool(tool_name)
        return await tool(*args, **kwargs)

# Script entry point for manual testing
if __name__ == "__main__":
    async def main():
        wrapper = MCPClientWrapper()
        tools = await wrapper.list_tools()
        print(f"Available tools: {tools}")
    asyncio.run(main()) 