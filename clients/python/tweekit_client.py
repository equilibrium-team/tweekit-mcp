"""
Async & direct Python SDK helpers for the TweekIT MCP server and REST API.

Published by AMPS dba Equilibrium (`tweekit` on PyPI).

Usage (MCP Client — credentials sent via HTTP headers, never in tool arguments):
    from tweekit import TweekitClient
    import asyncio
    from pathlib import Path

    async def main():
        async with TweekitClient() as tweekit:
            await tweekit.list_tools()
            check = await tweekit.preflight("diagram.dwg", target_provider="claude")
            output = await tweekit.convert_file(Path("input.pdf"), outfmt="png")
            print(check, output)

    asyncio.run(main())

Usage (Direct REST Client — no MCP hop required):
    from tweekit import TweekitDirectClient
    import asyncio

    async def main():
        async with TweekitDirectClient() as api:
            info = api.preflight("photo.cr2", target_provider="openai")
            result = await api.convert_url("https://example.com/sample.tiff", outfmt="png")
            print(info, result)

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport, StreamableHttpTransport

import server as _server_mod


class TweekitClient:
    """Async wrapper around the FastMCP Client for TweekIT MCP conversions and tools."""

    def __init__(
        self,
        server_url: str | Path | Any = None,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        self.server_url = server_url if server_url is not None else os.getenv("TWEEKIT_MCP_SERVER", "https://mcp.tweekit.io/mcp")
        self.api_key = api_key or os.getenv("TWEEKIT_API_KEY")
        self.api_secret = api_secret or os.getenv("TWEEKIT_API_SECRET")
        self._client: Client | None = None

    def _build_transport_or_target(self) -> Any:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["ApiKey"] = self.api_key
        if self.api_secret:
            headers["ApiSecret"] = self.api_secret

        if isinstance(self.server_url, str) and self.server_url.startswith(("http://", "https://")):
            if headers:
                return StreamableHttpTransport(self.server_url, headers=headers)
            return self.server_url

        if isinstance(self.server_url, Path) or (
            isinstance(self.server_url, str) and self.server_url.endswith(".py")
        ):
            env = dict(os.environ)
            if self.api_key:
                env["TWEEKIT_API_KEY"] = self.api_key
            if self.api_secret:
                env["TWEEKIT_API_SECRET"] = self.api_secret
            return PythonStdioTransport(
                script_path=self.server_url,
                args=["--transport", "stdio"],
                env=env,
            )

        if (self.api_key or self.api_secret) and (
            os.getenv("TWEEKIT_API_KEY") != self.api_key
            or os.getenv("TWEEKIT_API_SECRET") != self.api_secret
        ):
            raise ValueError(
                "Explicit api_key/api_secret can only be forwarded automatically to http(s) URLs or local .py "
                "script paths. For custom transports, pass credentials via transport headers or environment variables."
            )
        return self.server_url

    async def __aenter__(self) -> "TweekitClient":
        self._client = Client(self._build_transport_or_target())
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

    async def doctype(self, extension: str = "*", *, ext: str | None = None) -> Any:
        self._require_credentials()
        client = self._ensure_client()
        resolved_ext = ext if ext is not None else extension
        payload = {"extension": resolved_ext}
        result = await client.call_tool("doctype", payload)
        if result.is_error:
            raise RuntimeError("TweekIT doctype tool returned an error response.")
        return self._unwrap_result(result)

    async def preflight(self, filename_or_ext: str, target_provider: str = "default") -> Any:
        client = self._ensure_client()
        payload = {
            "filename_or_ext": filename_or_ext,
            "target_provider": target_provider,
        }
        result = await client.call_tool("preflight", payload)
        if result.is_error:
            raise RuntimeError("TweekIT preflight tool returned an error response.")
        return self._unwrap_result(result)

    async def convert_bytes(
        self,
        data: bytes,
        inext: str,
        outfmt: str,
        *,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
    ) -> Any:
        self._require_credentials()
        client = self._ensure_client()
        payload: dict[str, Any] = {
            "inext": inext.lstrip(".") or "bin",
            "outfmt": outfmt,
            "blob": base64.b64encode(data).decode("ascii"),
            "noRasterize": no_rasterize,
            "width": width,
            "height": height,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "page": page,
            "alpha": alpha,
            "bgColor": bgcolor,
        }
        result = await client.call_tool("convert", payload)
        if result.is_error:
            raise RuntimeError("TweekIT convert tool returned an error response.")
        return self._unwrap_result(result)

    async def convert_file(
        self,
        path: Path | str,
        outfmt: str,
        *,
        inext: str | None = None,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
    ) -> Any:
        self._require_credentials()
        file_path = Path(path)
        client = self._ensure_client()
        payload: dict[str, Any] = {
            "inext": (inext or file_path.suffix).lstrip(".") or "bin",
            "outfmt": outfmt,
            "blob": self._encode_file(file_path),
            "width": width,
            "height": height,
            "page": page,
            "bgColor": bgcolor,
        }
        if no_rasterize:
            payload["noRasterize"] = no_rasterize
        if any((x1, y1, x2, y2)):
            payload.update({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
        if not alpha:
            payload["alpha"] = alpha
        result = await client.call_tool("convert", payload)
        if result.is_error:
            raise RuntimeError("TweekIT convert tool returned an error response.")
        return self._unwrap_result(result)

    async def convert_url(
        self,
        url: str,
        outfmt: str,
        *,
        inext: str | None = None,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
        fetch_headers: dict[str, str] | None = None,
    ) -> Any:
        self._require_credentials()
        client = self._ensure_client()
        payload: dict[str, Any] = {
            "url": url,
            "outfmt": outfmt,
            "noRasterize": no_rasterize,
            "width": width,
            "height": height,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "page": page,
            "alpha": alpha,
            "bgColor": bgcolor,
        }
        if inext:
            payload["inext"] = inext
        if fetch_headers:
            payload["fetchHeaders"] = fetch_headers

        result = await client.call_tool("convert_url", payload)
        if result.is_error:
            raise RuntimeError("TweekIT convert_url tool returned an error response.")
        return self._unwrap_result(result)

    async def batch_convert(
        self,
        items: list[dict[str, Any]],
        *,
        concurrency: int = 5,
    ) -> list[Any]:
        """Convert multiple items concurrently (each item may have 'path', 'url', or 'data')."""
        sem = asyncio.Semaphore(max(1, concurrency))

        async def _process(item: dict[str, Any]) -> Any:
            async with sem:
                outfmt = item["outfmt"]
                common = {
                    k: item[k]
                    for k in ("inext", "no_rasterize", "width", "height", "x1", "y1", "x2", "y2", "page", "alpha", "bgcolor")
                    if k in item
                }
                if "url" in item:
                    if "fetch_headers" in item:
                        common["fetch_headers"] = item["fetch_headers"]
                    return await self.convert_url(item["url"], outfmt=outfmt, **common)
                if "data" in item:
                    inext = common.pop("inext", "bin")
                    return await self.convert_bytes(item["data"], inext=inext, outfmt=outfmt, **common)
                if "path" in item:
                    return await self.convert_file(item["path"], outfmt=outfmt, **common)
                raise ValueError("Each batch item must include 'path', 'url', or 'data'.")

        return await asyncio.gather(*(_process(item) for item in items))

    async def delete_document(self, doc_id: str) -> Any:
        self._require_credentials()
        client = self._ensure_client()
        payload = {"docId": doc_id}
        result = await client.call_tool("delete_document", payload)
        if result.is_error:
            raise RuntimeError("TweekIT delete_document tool returned an error response.")
        return self._unwrap_result(result)

    async def fetch(self, url: str) -> Any:
        client = self._ensure_client()
        result = await client.call_tool("fetch", {"url": url})
        if result.is_error:
            raise RuntimeError("TweekIT fetch tool returned an error response.")
        return self._unwrap_result(result)

    async def search(self, query: str, max_results: int = 5) -> Any:
        client = self._ensure_client()
        result = await client.call_tool("search", {"query": query, "max_results": max_results})
        if result.is_error:
            raise RuntimeError("TweekIT search tool returned an error response.")
        return self._unwrap_result(result)

    @staticmethod
    def _unwrap_result(result: Any) -> Any:
        return result.data or result.structured_content or [block.model_dump() for block in result.content]

    def _ensure_client(self) -> Client:
        if self._client is None:
            raise RuntimeError("Client not connected. Use 'async with TweekitClient()'.")
        return self._client

    def _require_credentials(self) -> tuple[str, str]:
        return self._require_key(), self._require_secret()

    def _require_key(self) -> str:
        if not self.api_key:
            raise RuntimeError("Missing TWEEKIT_API_KEY.")
        return self.api_key

    def _require_secret(self) -> str:
        if not self.api_secret:
            raise RuntimeError("Missing TWEEKIT_API_SECRET.")
        return self.api_secret

    @staticmethod
    def _encode_file(path: Path) -> str:
        data = path.read_bytes()
        return base64.b64encode(data).decode("ascii")


class TweekitDirectClient:
    """Direct async Python SDK for TweekIT REST API or On-Premises Miner Renderery (no MCP hop required)."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        *,
        local_miner: bool = False,
    ) -> None:
        self.api_key = api_key or os.getenv("TWEEKIT_API_KEY")
        self.api_secret = api_secret or os.getenv("TWEEKIT_API_SECRET")
        self.local_miner = local_miner
        if base_url:
            self._explicit_base_url: str | None = base_url.rstrip("/") + "/"
        elif local_miner:
            self._explicit_base_url = _server_mod.LOCAL_MINER_BASE_URL
        else:
            self._explicit_base_url = None
        try:
            self.base_url = _server_mod._resolve_api_base_url(self._explicit_base_url)
        except ValueError:
            self.base_url = (
                self._explicit_base_url
                or os.getenv("TWEEKIT_API_BASE_URL")
                or _server_mod.BASE_URL
            ).rstrip("/") + "/"

    async def __aenter__(self) -> "TweekitDirectClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    @staticmethod
    def preflight(filename_or_ext: str, target_provider: str = "default") -> dict[str, Any]:
        """Run instant local AI Hub preflight check and format recommendation."""
        return _server_mod.recommend_ai_format(filename_or_ext, target_provider=target_provider)

    async def version(self) -> str:
        if hasattr(_server_mod, "_version_impl"):
            return await _server_mod._version_impl(base_url=self._explicit_base_url)
        fn = getattr(_server_mod.version, "fn", _server_mod.version)
        return await fn()

    async def doctype(self, extension: str = "*") -> dict[str, Any]:
        key, secret = _server_mod._resolve_credentials(
            self.api_key, self.api_secret, base_url=self._explicit_base_url
        )
        return await _server_mod._doctype_impl(
            apiKey=key,
            apiSecret=secret,
            extension=extension,
            base_url=self._explicit_base_url,
        )

    async def convert_bytes(
        self,
        data: bytes,
        inext: str,
        outfmt: str,
        *,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
    ) -> Any:
        key, secret = _server_mod._resolve_credentials(
            self.api_key, self.api_secret, base_url=self._explicit_base_url
        )
        blob = base64.b64encode(data).decode("ascii")
        return await _server_mod._convert_impl(
            apiKey=key,
            apiSecret=secret,
            inext=_server_mod._normalize_extension(inext) or "bin",
            outfmt=outfmt,
            blob=blob,
            noRasterize=no_rasterize,
            width=width,
            height=height,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            page=page,
            alpha=alpha,
            bgColor=bgcolor,
            base_url=self._explicit_base_url,
        )

    async def convert_file(
        self,
        path: Path | str,
        outfmt: str,
        *,
        output_path: Path | str | None = None,
        inext: str | None = None,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
    ) -> Any:
        key, secret = _server_mod._resolve_credentials(
            self.api_key, self.api_secret, base_url=self._explicit_base_url
        )
        return await _server_mod._convert_file_impl(
            apiKey=key,
            apiSecret=secret,
            file_path=str(path),
            outfmt=outfmt,
            output_path=str(output_path) if output_path else None,
            inext=inext,
            noRasterize=no_rasterize,
            width=width,
            height=height,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            page=page,
            alpha=alpha,
            bgColor=bgcolor,
            enforce_sandbox=False,
            base_url=self._explicit_base_url,
        )

    async def convert_url(
        self,
        url: str,
        outfmt: str,
        *,
        inext: str | None = None,
        no_rasterize: bool = False,
        width: int = 0,
        height: int = 0,
        x1: int = 0,
        y1: int = 0,
        x2: int = 0,
        y2: int = 0,
        page: int = 1,
        alpha: bool = True,
        bgcolor: str = "",
        fetch_headers: dict[str, str] | None = None,
    ) -> Any:
        key, secret = _server_mod._resolve_credentials(
            self.api_key, self.api_secret, base_url=self._explicit_base_url
        )
        return await _server_mod._convert_url_impl(
            apiKey=key,
            apiSecret=secret,
            url=url,
            outfmt=outfmt,
            inext=inext,
            noRasterize=no_rasterize,
            width=width,
            height=height,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            page=page,
            alpha=alpha,
            bgColor=bgcolor,
            fetchHeaders=fetch_headers,
            allow_auth_headers=True,
            base_url=self._explicit_base_url,
        )

    async def delete_document(self, doc_id: str) -> dict[str, Any]:
        key, secret = _server_mod._resolve_credentials(
            self.api_key, self.api_secret, base_url=self._explicit_base_url
        )
        return await _server_mod._delete_document_impl(
            apiKey=key,
            apiSecret=secret,
            docId=doc_id,
            base_url=self._explicit_base_url,
        )


async def _demo() -> None:
    async with TweekitClient() as tweekit:
        print("Available tools:", await tweekit.list_tools())


if __name__ == "__main__":
    asyncio.run(_demo())
