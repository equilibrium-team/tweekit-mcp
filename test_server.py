import unittest
import asyncio

from fastmcp import Client

class TestMCPServer(unittest.TestCase):
    async def test_server(self):
        # Test the MCP server using streamable-http transport.
        # Use "/sse" endpoint if using sse transport.
        async with Client("http://localhost:8080/mcp") as client:
            # List available tools
            tools = await client.list_tools()
            for tool in tools:
                print(f">>> 🛠️  Tool found: {tool.name}")
            # Call add tool
            print(">>> 🪛  Calling add tool for 1 + 2")
            result = await client.call_tool("add", {"a": 1, "b": 2})
            self.assertEqual(result.data, 3) # Corrected assertion using .data
            print(f"<<< ✅ Result: {result.data}")
            # Call subtract tool
            print(">>> 🪛  Calling subtract tool for 10 - 3")
            result = await client.call_tool("subtract", {"a": 10, "b": 3})
            self.assertEqual(result.data, 7) # Corrected assertion using .data
            print(f"<<< ✅ Result: {result.data}")

    async def test_version_tool(self):
        # Test the version tool.
        async with Client("http://localhost:8080/mcp") as client:
            print(">>> 🪛  Calling version tool")
            result = await client.call_tool("version", {})
            self.assertIsInstance(result.data, str) # Assert that the result is a string
            print(f"<<< ✅ Result: {result.data}")

    # unittest does not support async test methods directly, need to wrap with asyncio.run
    def test_server_sync_wrapper(self):
        asyncio.run(self.test_server())

    def test_version_tool_sync_wrapper(self):
        asyncio.run(self.test_version_tool())

if __name__ == "__main__":
    unittest.main()
