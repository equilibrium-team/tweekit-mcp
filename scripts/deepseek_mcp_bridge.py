#!/usr/bin/env python3
"""
Bridge script to invoke TweekIT MCP tools inside custom DeepSeek automation.

Example usage:
    python scripts/deepseek_mcp_bridge.py \
        --file sample.pdf \
        --outfmt txt \
        --server https://mcp.tweekit.com/mcp
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any

from fastmcp import Client


def load_file(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


async def convert_document(
    file_path: Path,
    outfmt: str,
    server_url: str,
    api_key: str,
    api_secret: str,
    width: int = 0,
    height: int = 0,
    page: int = 1,
    bgcolor: str = "",
) -> Any:
    payload = {
        "apiKey": api_key,
        "apiSecret": api_secret,
        "inext": file_path.suffix.lstrip(".") or "bin",
        "outfmt": outfmt,
        "blob": load_file(file_path),
        "width": width,
        "height": height,
        "page": page,
        "bgcolor": bgcolor,
    }

    async with Client(server_url) as client:
        result = await client.call_tool("convert", payload)
        if result.is_error:
            raise RuntimeError("TweekIT convert tool returned an error response.")
        if result.data is not None:
            return result.data
        if result.structured_content is not None:
            return result.structured_content
        return [block.model_dump() if hasattr(block, "model_dump") else str(block) for block in result.content]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call the TweekIT convert tool for DeepSeek workflows.")
    parser.add_argument("--file", required=True, type=Path, help="Path to the input document.")
    parser.add_argument("--outfmt", required=True, help="Target output format (e.g. pdf, txt, png).")
    parser.add_argument("--server", default="https://mcp.tweekit.com/mcp", help="TweekIT MCP server URL.")
    parser.add_argument("--api-key", default=None, help="TweekIT API key (overrides env variable).")
    parser.add_argument("--api-secret", default=None, help="TweekIT API secret (overrides env variable).")
    parser.add_argument("--width", type=int, default=0, help="Resize width in pixels (optional).")
    parser.add_argument("--height", type=int, default=0, help="Resize height in pixels (optional).")
    parser.add_argument("--page", type=int, default=1, help="Page number for multi-page inputs.")
    parser.add_argument("--bgcolor", default="", help="Background color for transparent outputs.")
    parser.add_argument("--output", type=Path, help="Optional path to write binary results.")
    return parser.parse_args()


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    api_key = args.api_key or os.getenv("TWEEKIT_API_KEY")
    api_secret = args.api_secret or os.getenv("TWEEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise SystemExit("Missing TweekIT credentials. Provide --api-key/--api-secret or set env vars.")
    return api_key, api_secret


def serialize_output(output: Any) -> dict[str, Any] | list[Any]:
    try:
        from pydantic import BaseModel  # type: ignore

        if isinstance(output, BaseModel):
            return output.model_dump()
    except Exception:
        pass

    if isinstance(output, dict):
        return output
    if isinstance(output, list):
        return output
    return {"result": output}


def maybe_write_file(output: dict[str, Any], target: Path | None) -> None:
    if not target:
        return
    data = output.get("data")
    if not isinstance(data, str):
        raise SystemExit("Tool response did not include base64 `data` field; cannot write to file.")
    binary = base64.b64decode(data)
    target.write_bytes(binary)
    print(f"Wrote converted artifact to {target}", file=sys.stderr)


async def main_async() -> None:
    args = parse_args()
    api_key, api_secret = resolve_credentials(args)
    result = await convert_document(
        file_path=args.file,
        outfmt=args.outfmt,
        server_url=args.server,
        api_key=api_key,
        api_secret=api_secret,
        width=args.width,
        height=args.height,
        page=args.page,
        bgcolor=args.bgcolor,
    )
    payload = serialize_output(result)
    if isinstance(payload, dict):
        maybe_write_file(payload, args.output)
    print(json.dumps(payload, indent=2))


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
