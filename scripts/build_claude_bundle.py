#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = REPO_ROOT / "claude" / "manifest.json"
README_PATH = REPO_ROOT / "claude" / "README.md"
SERVER_SOURCE = REPO_ROOT / "server.py"

# Keep dependency pins in sync with uv.lock / pyproject.toml.
REQUIRED_DEPENDENCIES = [
    "fastmcp==2.12.4",
    "httpx==0.28.1",
    "fastapi==0.119.0",
]


def _vendor_dependencies(target_dir: Path) -> None:
    """Install runtime dependencies for the bundled MCP server."""
    target_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ensurepip",
            "--upgrade",
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-warn-script-location",
        "--target",
        str(target_dir),
        *REQUIRED_DEPENDENCIES,
    ]
    subprocess.run(cmd, check=True)


def _stage_server_files(server_dir: Path) -> None:
    """Copy the MCP server entry point into the bundle."""
    server_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SERVER_SOURCE, server_dir / "server.py")


def _write_manifest(manifest: dict[str, object], destination: Path) -> None:
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _zip_directory(source: Path, destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as bundle:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            bundle.write(path, arcname=str(path.relative_to(source)))


def build_bundle(
    manifest_path: Path,
    output_path: Path,
    version: str | None,
) -> Path:
    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    if version:
        manifest["version"] = version

    with tempfile.TemporaryDirectory(prefix="claude_bundle_") as tmpdir:
        bundle_root = Path(tmpdir) / "bundle"
        bundle_root.mkdir(parents=True, exist_ok=True)

        _write_manifest(manifest, bundle_root / "manifest.json")

        if README_PATH.exists():
            shutil.copy2(README_PATH, bundle_root / "README.md")

        _stage_server_files(bundle_root / "server")
        _vendor_dependencies(bundle_root / "python")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        _zip_directory(bundle_root, output_path)

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
        "--version",
        default=None,
        help="Override the manifest version string.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle_path = build_bundle(
        manifest_path=args.manifest,
        output_path=args.output,
        version=args.version,
    )
    print(f"Bundle written to {bundle_path}")


if __name__ == "__main__":
    main()
