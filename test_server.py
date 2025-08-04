import asyncio

from fastmcp import Client

import asyncio

from fastmcp import Client

async def test_server():
    # Test the MCP server using streamable-http transport.
    # Use "/sse" endpoint if using sse transport.
    #async with Client("http://localhost:8080/mcp") as client:
    async with Client("https://mcp-server-728625953614.us-west1.run.app/mcp") as client:
        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")


if __name__ == "__main__":
    asyncio.run(test_server())
