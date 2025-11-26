import asyncio
import os
import re
import json
import base64
from pathlib import Path

from fastmcp import Client

# Test the MCP server using streamable-http transport.
# Use "/sse" endpoint if using sse transport.

MCP_URL = os.environ.get("TWEEKIT_MCP_BASE_URL", "https://mcp.tweekit.io/mcp")
API_KEY = (
    os.environ.get("TWEEKIT_API_KEY")
    or os.environ.get("TWEEKIT_APIKEY")
)
API_SECRET = (
    os.environ.get("TWEEKIT_API_SECRET")
    or os.environ.get("TWEEKIT_APISECRET")
)

async def test_server():

    if not API_KEY or not API_SECRET:
        raise RuntimeError(
            "TWEEKIT_API_KEY/TWEEKIT_API_SECRET env vars are required for smoke tests."
        )

    async with Client(MCP_URL) as client:
        # List available resources
        resources = await client.list_resources()
        for resource in resources:
            print(f">>> 📦  Resource found: {resource.name}")

        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")
        tool_names = {t.name for t in tools}

        passed_checks = set()
        required_checks = {"version", "mcp_version", "doctype"}

        # Call the version resource (no parameters)
        try:
            version = await client.read_resource("config://tweekit-version")

            # Normalize the returned value to a string.
            content = version[0] if isinstance(version, (list, tuple)) and version else version
            ver_str = getattr(content, "text", content)
            ver_str = str(ver_str)

            print(f">>> 🔖 TweekIT API version: {ver_str}")
            # Assert the version matches the pattern ^\d+\.\d+\.\d+\.\d+$
            assert re.match(r"^\d+\.\d+\.\d+\.\d+$", ver_str), f"Unexpected version format: {ver_str!r}."
            passed_checks.add("version")
        except Exception as e:
            print(f">>> ⚠️ Failed to call version resource: {e}")

        # Call the MCP server version resource
        try:
            mcp_version = await client.read_resource("config://tweekit-mcp-version")

            content = mcp_version[0] if isinstance(mcp_version, (list, tuple)) and mcp_version else mcp_version
            ver_str = getattr(content, "text", content)
            ver_str = str(ver_str)

            print(f">>> 🔖 TweekIT MCP server version: {ver_str}")
            assert re.match(r"^\d+\.\d+\.\d+$", ver_str), f"Unexpected MCP version format: {ver_str!r}."
            passed_checks.add("mcp_version")
        except Exception as e:
            print(f">>> ⚠️ Failed to call MCP version resource: {e}")

        # Call the doctype tool with parameters, including apikey and apisecret from environment variables
        try:
            params = {
                "apiKey": API_KEY,
                "apiSecret": API_SECRET,
                "extension": "*"
            }
            doctype = await client.call_tool("doctype", params)
            try:
                json.loads(json.dumps(doctype.data))  # Ensure the response is valid JSON
                print(f">>> ✅ Doctype tool response is valid JSON")
                passed_checks.add("doctype")
            except json.JSONDecodeError:
                assert False, f">>> ⚠️ Doctype tool response is not valid JSON."
        except Exception as e:
            print(f">>> ⚠️ Failed to call doctype tool: {e}")

        # Optional: Call the search tool if present
        if "search" in tool_names:
            required_checks.add("search")
            try:
                params = {"query": "tweekit site:tweekit.io", "max_results": 3}
                result = await client.call_tool("search", params)
                data = result.data if hasattr(result, "data") else result
                if isinstance(data, dict) and "results" in data:
                    print(f">>> ✅ Search tool returned {len(data['results'])} results")
                    passed_checks.add("search")
                else:
                    print(f">>> ⚠️ Search tool returned unexpected payload: {data}")
            except Exception as e:
                print(f">>> ⚠️ Failed to call search tool: {e}")

        # Optional: Call the fetch tool if present
        if "fetch" in tool_names:
            required_checks.add("fetch")
            try:
                params = {"url": "https://example.com"}
                result = await client.call_tool("fetch", params)
                # fetch may return File/Image or JSON; accept any non-error
                if result.content:
                    print(f">>> ✅ Fetch tool returned binary content")
                    passed_checks.add("fetch")
                else:
                    data = result.data if hasattr(result, "data") else result
                    if isinstance(data, dict) and ("text" in data or "status" in data):
                        print(f">>> ✅ Fetch tool returned text content: status={data.get('status')}")
                        passed_checks.add("fetch")
                    elif isinstance(data, dict) and "error" in data:
                        print(f">>> ⚠️ Fetch tool error: {data['error']}")
                    else:
                        print(f">>> ⚠️ Fetch tool unexpected response: {data}")
            except Exception as e:
                print(f">>> ⚠️ Failed to call fetch tool: {e}")

        # Convert known sample documents to validate binary responses
        sample_root = Path(__file__).resolve().parent.parent
        sample_files = [
            {
                "path": sample_root / "test.png",
                "inext": "png",
                "outfmt": "webp",
                "noRasterize": False,
            },
            {
                "path": sample_root / "test.docx",
                "inext": "docx",
                "outfmt": "pdf",
                "noRasterize": True,
            },
        ]

        for sample in sample_files:
            path = sample["path"]
            if not path.exists():
                print(f">>> ⚠️ Sample file missing: {path}")
                continue

            required_checks.add(f"convert:{path.name}")

            encoded_string = base64.b64encode(path.read_bytes()).decode("utf-8")
            params = {
                "apiKey": API_KEY,
                "apiSecret": API_SECRET,
                "blob": encoded_string,
                "inext": sample["inext"],
                "outfmt": sample["outfmt"],
                "noRasterize": sample["noRasterize"],
            }

            print(f">>> 🔖 Calling convert tool for {path.name}.")
            convert = await client.call_tool("convert", params)
            if convert.content:
                content = convert.content
                part = content[0]
                if part.type in {"resource", "image"}:
                    print(f">>> ✅ Convert tool for {path.name} returned {part.type}.")
                    passed_checks.add(f"convert:{path.name}")
                elif part.type == "text":
                    print(f">>> ⚠️ Convert tool rejected request: {part.text}")
                else:
                    assert False, f">>> ⚠️ Unexpected content type for {path.name}: {part.type!r}"
            elif convert.data and "error" in convert.data:
                print(f">>> ⚠️ Convert tool returned an error for {path.name}: {convert.data['error']}")
            else:
                assert False, f">>> ⚠️ Convert tool for {path.name} returned an unexpected response: data={convert.data}, content={convert.content}"

        if "convert_url" in tool_names:
            required_checks.add("convert_url")
            remote_url = "https://raw.githubusercontent.com/equilibrium-team/tweekit-mcp/main/test.png"
            try:
                params = {
                    "apiKey": API_KEY,
                    "apiSecret": API_SECRET,
                    "url": remote_url,
                    "outfmt": "webp",
                }
                result = await client.call_tool("convert_url", params)
                if result.content:
                    part = result.content[0]
                    if part.type in {"resource", "image"}:
                        print(f">>> ✅ convert_url returned {part.type} for remote asset.")
                        passed_checks.add("convert_url")
                    else:
                        print(f">>> ⚠️ convert_url unexpected content type: {part.type}")
                elif result.data and "error" in result.data:
                    print(f">>> ⚠️ convert_url returned error: {result.data['error']}")
                else:
                    print(f">>> ⚠️ convert_url unexpected response: data={result.data}, content={result.content}")
            except Exception as e:
                print(f">>> ⚠️ Failed to call convert_url tool: {e}")

        missing_checks = sorted(required_checks - passed_checks)
        if missing_checks:
            print(f"FAILED: missing checks -> {missing_checks}")
            raise AssertionError(f"Smoke tests incomplete: {missing_checks}")

        print("PASSED")

if __name__ == "__main__":
    asyncio.run(test_server())
