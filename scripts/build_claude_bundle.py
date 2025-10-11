#!/usr/bin/env python3
"""
Build a Claude Desktop MCP bundle (.mcpb) for the TweekIT server.

Usage:
    python scripts/build_claude_bundle.py \
        --server-url https://mcp.tweekit.com/mcp \
        --version 0.1.0 \
        --output dist/tweekit-claude.mcpb
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "claude" / "manifest.json"
README_PATH = REPO_ROOT / "claude" / "README.md"


def build_bundle(
    manifest_path: Path,
    output_path: Path,
    server_url: str | None,
    version: str | None,
) -> Path:
    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    manifest.setdefault("metadata", {})
    built_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest["metadata"]["built_at"] = built_at

    if server_url:
        manifest.setdefault("entry_point", {})
        manifest["entry_point"]["url"] = server_url

    if version:
        manifest["version"] = version

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as bundle:
        bundle.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        if README_PATH.exists():
            bundle.write(README_PATH, arcname="README.md")

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the TweekIT Claude Desktop MCP bundle.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to the manifest JSON template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "dist" / "tweekit-claude.mcpb",
        help="Output path for the generated bundle (.mcpb).",
    )
    parser.add_argument(
        "--server-url",
        default=os.getenv("CLAUDE_MCP_SERVER_URL"),
        help="Override the MCP server URL embedded in the manifest.",
    )
    parser.add_argument(
        "--version",
        default=os.getenv("CLAUDE_MCP_VERSION"),
        help="Override the manifest version string.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle_path = build_bundle(
        manifest_path=args.manifest,
        output_path=args.output,
        server_url=args.server_url,
        version=args.version,
    )
    print(f"Bundle written to {bundle_path}")


if __name__ == "__main__":
    main()
