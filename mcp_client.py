# mcp_client.py
"""
MCP client that connects to the local MCP server using stdio transport (PythonStdioTransport).
Provides reusable functions/classes for integration.
"""
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

class MCPClientWrapper:
    def __init__(self, server_script="mcp_server.py"):
        self.server_script = server_script
        # Get absolute path to the server script
        server_path = os.path.abspath(server_script)
        
        # MultiServerMCPClient expects a dictionary of server configurations
        self.client = MultiServerMCPClient({
            "local_server": {
                "command": "python",
                "args": [server_path],
                "transport": "stdio",
            }
        })

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