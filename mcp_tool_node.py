from mcp_client import MCPClientWrapper

# LangGraph tool node wrapper for MCP tools with argument and async support
def mcp_tool_node(tool_name):
    """
    Returns a function suitable for use as a LangGraph tool node, which will call the specified MCP tool.
    The node function accepts *args and **kwargs and forwards them to the MCP tool.
    """
    async def node_fn(*args, **kwargs):
        client = MCPClientWrapper()
        return await client.invoke_tool(tool_name, *args, **kwargs)
    return node_fn 