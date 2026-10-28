#!/usr/bin/env python3
"""
Utility for keeping the TweekIT MCP version in sync across metadata files.

Usage examples:
  python scripts/bump_version.py --set 1.7.0
  python scripts/bump_version.py --bump-build
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
VERSION_FILE = REPO_ROOT / "VERSION"

TARGET_FILES = [
    REPO_ROOT / "pyproject.toml",
    REPO_ROOT / "server.py",
    REPO_ROOT / "server.json",
    REPO_ROOT / "claude" / "manifest.json",
    REPO_ROOT / "README.md",
    REPO_ROOT / "uv.lock",
]


def detect_current_version() -> str:
    """Read the canonical version from pyproject.toml."""
    if not PYPROJECT.exists():
        raise SystemExit("pyproject.toml not found; cannot determine current version.")
    text = PYPROJECT.read_text()
    match = re.search(r'^version\s*=\s*"(?P<ver>[^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit("Unable to locate version string in pyproject.toml")
    return match.group("ver").strip()


def format_build(major: int, minor: int, build: int) -> str:
    """Return standard X.Y.Z semantic version string."""
    return f"{major}.{minor}.{build}"


def parse_version(version: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Version '{version}' must follow semantic versioning pattern X.Y.Z")
    major, minor, build = map(int, match.groups())
    return major, minor, build


def write_version_file(version: str) -> None:
    VERSION_FILE.write_text(f"{version}\n")


def update_file(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text()
    updated = text

    if path.name == "uv.lock":
        # Targeted replace: only update tweekit-mcp's own version entry in the
        # lock file. A naive str.replace on the whole file would corrupt unrelated
        # package version strings that happen to share the same version number.
        updated = re.sub(
            r'(name\s*=\s*"tweekit(?:-mcp)?"[^\[]*?version\s*=\s*")[^"]+(")',
            rf'\g<1>{new}\2',
            updated,
            flags=re.DOTALL,
        )
    elif path.name == "server.py":
        updated = re.sub(r'SERVER_VERSION\s*=\s*"[^"]+"', f'SERVER_VERSION = "{new}"', updated)
    else:
        replacements = {
            old: new,
            f"v{old}": f"v{new}",
        }
        for needle, repl in replacements.items():
            updated = updated.replace(needle, repl)

    if updated != text:
        path.write_text(updated)
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronise version strings across the repo.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--set", dest="set_version", help="Explicit version to apply (e.g., 1.6.01)")
    group.add_argument(
        "--bump-build",
        action="store_true",
        help="Increment the build component (major.minor.XX).",
    )
    args = parser.parse_args()

    current = detect_current_version()
    if args.set_version:
        new_version = args.set_version.strip()
        # Validate format
        major, minor, build = parse_version(new_version)
        new_version = format_build(major, minor, build)
    else:
        major, minor, build = parse_version(current)
        build += 1
        new_version = format_build(major, minor, build)

    if new_version == current:
        print(f"Version already {new_version}; nothing to do.")
        return 0

    write_version_file(new_version)

    touched = []
    for file_path in TARGET_FILES:
        if update_file(file_path, current, new_version):
            touched.append(file_path.relative_to(REPO_ROOT))

    if not touched:
        print("Warning: no files were updated. Check that the old version string exists.")
    else:
        print("Updated version strings in:")
        for path in touched:
            print(f"  - {path}")

    print(f"VERSION file set to {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
