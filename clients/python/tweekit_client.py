"""
Async helper for calling the TweekIT MCP server from Python.

Usage:
    from clients.python.tweekit_client import TweekitClient
    import asyncio, pathlib

    async def main():
        async with TweekitClient() as tweekit:
            await tweekit.list_tools()
            output = await tweekit.convert_file(pathlib.Path("input.pdf"), outfmt="txt")
            print(output)

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
from typing import Any

from fastmcp import Client


class TweekitClient:
    """Thin wrapper around the fastmcp Client for TweekIT conversions."""

    def __init__(
        self,
        server_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        self.server_url = server_url or os.getenv("TWEEKIT_MCP_SERVER", "https://mcp.tweekit.com/mcp")
        self.api_key = api_key or os.getenv("TWEAKIT_API_KEY")
        self.api_secret = api_secret or os.getenv("TWEAKIT_API_SECRET")
        self._client: Client | None = None

    async def __aenter__(self) -> "TweekitClient":
        self._client = Client(self.server_url)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if self._client is not None:
            await self._client.__aexit__(exc_type, exc, tb)
        self._client = None

    async def list_tools(self) -> list[str]:
        client = self._ensure_client()
        tools = await client.list_tools()
        return [tool.name for tool in tools]

    async def doctype(self, ext: str) -> Any:
        client = self._ensure_client()
        payload = {
            "ext": ext,
            "apiKey": self._require_key(),
            "apiSecret": self._require_secret(),
        }
        result = await client.call_tool("doctype", payload)
        if result.is_error:
            raise RuntimeError("TweekIT doctype tool returned an error response.")
        return result.data or result.structured_content or [block.model_dump() for block in result.content]

    async def convert_file(
        self,
        path: Path,
        outfmt: str,
        *,
        width: int = 0,
        height: int = 0,
        page: int = 1,
        bgcolor: str = "",
    ) -> Any:
        client = self._ensure_client()
        payload = {
            "apiKey": self._require_key(),
            "apiSecret": self._require_secret(),
            "inext": path.suffix.lstrip(".") or "bin",
            "outfmt": outfmt,
            "blob": self._encode_file(path),
            "width": width,
            "height": height,
            "page": page,
            "bgcolor": bgcolor,
        }
        result = await client.call_tool("convert", payload)
        if result.is_error:
            raise RuntimeError("TweekIT convert tool returned an error response.")
        return result.data or result.structured_content or [block.model_dump() for block in result.content]

    def _ensure_client(self) -> Client:
        if self._client is None:
            raise RuntimeError("Client not connected. Use 'async with TweekitClient()'.")
        return self._client

    def _require_key(self) -> str:
        if not self.api_key:
            raise RuntimeError("Missing TWEAKIT_API_KEY.")
        return self.api_key

    def _require_secret(self) -> str:
        if not self.api_secret:
            raise RuntimeError("Missing TWEAKIT_API_SECRET.")
        return self.api_secret

    @staticmethod
    def _encode_file(path: Path) -> str:
        data = path.read_bytes()
        return base64.b64encode(data).decode("ascii")


async def _demo() -> None:
    async with TweekitClient() as tweekit:
        print("Available tools:", await tweekit.list_tools())


if __name__ == "__main__":
    asyncio.run(_demo())
