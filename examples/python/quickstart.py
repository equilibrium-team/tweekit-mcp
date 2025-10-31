"""
Minimal Python quickstart for the TweekIT MCP server.

Run with:
    python examples/python/quickstart.py --file path/to/input.pdf --outfmt txt
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from clients.python.tweekit_client import TweekitClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a document using the TweekIT MCP server.")
    parser.add_argument("--file", type=Path, required=True, help="Path to the document to convert.")
    parser.add_argument("--outfmt", required=True, help="Desired output format (e.g. txt, pdf, png).")
    parser.add_argument("--width", type=int, default=0, help="Optional width for image resizing.")
    parser.add_argument("--height", type=int, default=0, help="Optional height for image resizing.")
    parser.add_argument("--page", type=int, default=1, help="Page to convert for multi-page documents.")
    parser.add_argument("--bgcolor", default="", help="Background color for transparent images (hex RGB).")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with TweekitClient() as tweekit:
        tools = await tweekit.list_tools()
        print("Tools available:", tools)
        result = await tweekit.convert_file(
            path=args.file,
            outfmt=args.outfmt,
            width=args.width,
            height=args.height,
            page=args.page,
            bgcolor=args.bgcolor,
        )
        print("Conversion result:", result)


if __name__ == "__main__":
    asyncio.run(main())
