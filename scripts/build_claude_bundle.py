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
    "certifi>=2026.10.19",
    "fastmcp>=3.0.0",
    "httpx>=0.28.1",
    "fastapi>=0.115.0",
]

BOOTSTRAP_SCRIPT = '''#!/usr/bin/env python3
"""ABI-resilient bootstrap launcher for the TweekIT Claude Desktop (.mcpb) bundle."""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_PYTHON = BUNDLE_ROOT / "python"
SERVER_IMPL = BUNDLE_ROOT / "server" / "tweekit_server.py"


def _can_use_current_interpreter() -> bool:
    for p in (str(SERVER_IMPL.parent), str(BUNDLED_PYTHON)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import pydantic_core._pydantic_core  # noqa: F401
        import fastmcp  # noqa: F401
        return True
    except Exception:
        return False


def _detect_bundled_abi_versions() -> list[str]:
    versions: list[str] = []
    pc_dir = BUNDLED_PYTHON / "pydantic_core"
    if not pc_dir.is_dir():
        return versions
    for artifact in pc_dir.iterdir():
        match = re.search(r"cpython-(\\d)(\\d+)-", artifact.name)
        if match:
            ver = f"{match.group(1)}.{match.group(2)}"
            if ver not in versions:
                versions.append(ver)
    return versions


def _find_matching_python(version: str) -> str | None:
    candidates = [
        f"/opt/homebrew/bin/python{version}",
        f"/opt/homebrew/opt/python@{version}/bin/python{version}",
        f"/usr/local/bin/python{version}",
        shutil.which(f"python{version}"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _find_uv_or_tool_fallback() -> tuple[str, list[str]] | None:
    home = Path.home()
    for tool_bin in (str(home / ".local" / "bin" / "tweekit-mcp"), shutil.which("tweekit-mcp")):
        if tool_bin and os.path.isfile(tool_bin) and os.access(tool_bin, os.X_OK):
            return tool_bin, [tool_bin, *sys.argv[1:]]

    for uvx_bin in (
        str(home / ".local" / "bin" / "uvx"),
        "/opt/homebrew/bin/uvx",
        "/usr/local/bin/uvx",
        shutil.which("uvx"),
    ):
        if uvx_bin and os.path.isfile(uvx_bin) and os.access(uvx_bin, os.X_OK):
            return uvx_bin, [uvx_bin, "--from", "tweekit", "tweekit-mcp", *sys.argv[1:]]
    return None


def main() -> None:
    if os.environ.get("TWEEKIT_BOOTSTRAP_REEXEC") != "1":
        if _can_use_current_interpreter():
            import tweekit_server
            tweekit_server.main()
            return

        env = os.environ.copy()
        env["TWEEKIT_BOOTSTRAP_REEXEC"] = "1"
        env["PYTHONPATH"] = str(BUNDLED_PYTHON)

        for ver in _detect_bundled_abi_versions():
            py_bin = _find_matching_python(ver)
            if py_bin:
                os.execve(py_bin, [py_bin, str(SERVER_IMPL), *sys.argv[1:]], env)

        fallback = _find_uv_or_tool_fallback()
        if fallback:
            exe, argv = fallback
            env.pop("PYTHONPATH", None)
            os.execve(exe, argv, env)

    for p in (str(SERVER_IMPL.parent), str(BUNDLED_PYTHON)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import tweekit_server
    tweekit_server.main()


if __name__ == "__main__":
    main()
'''


def _vendor_dependencies(target_dir: Path) -> None:
    """Install runtime dependencies for the bundled MCP server."""
    target_dir.mkdir(parents=True, exist_ok=True)
    uv_bin = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    if Path(uv_bin).is_file():
        cmd = [
            uv_bin,
            "pip",
            "install",
            "--python",
            sys.executable,
            "--upgrade",
            "--target",
            str(target_dir),
            *REQUIRED_DEPENDENCIES,
        ]
        subprocess.run(cmd, check=True)
        return

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
    """Stage the ABI-resilient server.py entry point and tweekit_server.py implementation."""
    server_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SERVER_SOURCE, server_dir / "tweekit_server.py")
    entry_path = server_dir / "server.py"
    entry_path.write_text(BOOTSTRAP_SCRIPT, encoding="utf-8")
    entry_path.chmod(0o755)


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
