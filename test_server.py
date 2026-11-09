import argparse
import asyncio
import base64
import json
import os
import re
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a TweekIT MCP Streamable HTTP endpoint.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("TWEEKIT_MCP_BASE_URL", "https://mcp.tweekit.io/mcp"),
        help="Target MCP Streamable HTTP endpoint URL.",
    )
    return parser.parse_args()


async def test_server(base_url: str | None = None) -> None:
    mcp_url = (base_url or os.environ.get("TWEEKIT_MCP_BASE_URL", "https://mcp.tweekit.io/mcp")).rstrip("/")
    api_key = os.environ.get("TWEEKIT_API_KEY") or os.environ.get("TWEEKIT_APIKEY")
    api_secret = os.environ.get("TWEEKIT_API_SECRET") or os.environ.get("TWEEKIT_APISECRET")

    if not api_key or not api_secret:
        raise RuntimeError("TWEEKIT_API_KEY/TWEEKIT_API_SECRET env vars are required for smoke tests.")

    # Verify trailing-slash `/mcp/` does NOT emit a 307 redirect or downgrade to http://
    slash_url = f"{mcp_url}/"
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as raw_http:
        init_resp = await raw_http.post(
            slash_url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "ApiKey": api_key,
                "ApiSecret": api_secret,
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "tweekit-smoke-probe", "version": "1.8.1"},
                },
            },
        )
        assert init_resp.status_code == 200, (
            f"Expected 200 OK on trailing-slash {slash_url}, got {init_resp.status_code} "
            f"(Location: {init_resp.headers.get('location')})"
        )
        print(f">>> Trailing-slash initialize {slash_url} returned 200 OK (no redirect).")

    transport = StreamableHttpTransport(
        mcp_url,
        headers={"ApiKey": api_key, "ApiSecret": api_secret},
    )
    async with Client(transport) as client:
        resources = await client.list_resources()
        for resource in resources:
            print(f">>> Resource found: {resource.name}")

        tools = await client.list_tools()
        for tool in tools:
            print(f">>> Tool found: {tool.name}")
            schema_props = (tool.inputSchema or {}).get("properties", {})
            assert "apiKey" not in schema_props and "apiSecret" not in schema_props, (
                f"Tool {tool.name} still exposes credential parameters in inputSchema!"
            )
        tool_names = {t.name for t in tools}

        passed_checks = set()
        required_checks = {"version", "mcp_version", "doctype", "preflight"}

        version = await client.read_resource("config://tweekit-version")
        content = version[0] if isinstance(version, (list, tuple)) and version else version
        ver_str = str(getattr(content, "text", content))
        print(f">>> TweekIT API version: {ver_str}")
        assert re.match(r"^\d+\.\d+\.\d+\.\d+$", ver_str), f"Unexpected version format: {ver_str!r}."
        passed_checks.add("version")

        mcp_version = await client.read_resource("config://tweekit-mcp-version")
        content = mcp_version[0] if isinstance(mcp_version, (list, tuple)) and mcp_version else mcp_version
        mcp_ver_str = str(getattr(content, "text", content))
        print(f">>> TweekIT MCP server version: {mcp_ver_str}")
        assert re.match(r"^\d+\.\d+\.\d+$", mcp_ver_str), f"Unexpected MCP version format: {mcp_ver_str!r}."
        passed_checks.add("mcp_version")

        preflight = await client.call_tool("preflight", {"filename_or_ext": "blueprint.dwg", "target_provider": "claude"})
        pf_data = preflight.data if hasattr(preflight, "data") and preflight.data else preflight.structured_content
        assert isinstance(pf_data, dict) and pf_data.get("recommended_outfmt") == "png"
        passed_checks.add("preflight")

        doctype = await client.call_tool("doctype", {"extension": "*"})
        json.loads(json.dumps(doctype.data))
        print(">>> Doctype tool response is valid JSON")
        passed_checks.add("doctype")

        if "fetch" in tool_names:
            required_checks.add("fetch")
            result = await client.call_tool("fetch", {"url": "https://example.com"})
            data = result.data if hasattr(result, "data") else result
            if result.content or (isinstance(data, dict) and ("text" in data or "status" in data)):
                passed_checks.add("fetch")

        repo_root = Path(__file__).resolve().parent
        smoke_inputs = [
            {"path": repo_root / "test.png", "inext": "png", "outfmt": "webp", "noRasterize": False},
            {"path": repo_root / "test.docx", "inext": "docx", "outfmt": "pdf", "noRasterize": True},
        ]

        for entry in smoke_inputs:
            path = entry["path"]
            if not path.exists():
                continue
            required_checks.add(f"convert:{path.name}")
            encoded_string = base64.b64encode(path.read_bytes()).decode("utf-8")
            convert = await client.call_tool(
                "convert",
                {
                    "blob": encoded_string,
                    "inext": entry["inext"],
                    "outfmt": entry["outfmt"],
                    "noRasterize": entry["noRasterize"],
                },
            )
            if convert.content and convert.content[0].type in {"resource", "image"}:
                print(f">>> Convert tool for {path.name} returned {convert.content[0].type}.")
                passed_checks.add(f"convert:{path.name}")

        if "convert_url" in tool_names:
            required_checks.add("convert_url")
            remote_url = "https://raw.githubusercontent.com/equilibrium-team/tweekit-mcp/main/test.png"
            result = await client.call_tool("convert_url", {"url": remote_url, "outfmt": "webp"})
            if result.content and result.content[0].type in {"resource", "image"}:
                print(f">>> convert_url returned {result.content[0].type} for remote asset.")
                passed_checks.add("convert_url")

        missing_checks = sorted(required_checks - passed_checks)
        if missing_checks:
            raise AssertionError(f"Smoke tests incomplete: {missing_checks}")

        print("PASSED")


if __name__ == "__main__":
    cli_args = _parse_cli()
    asyncio.run(test_server(cli_args.base_url))
