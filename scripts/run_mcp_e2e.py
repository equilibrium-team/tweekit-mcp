#!/usr/bin/env python3
"""Simple end-to-end runner for the TweekIT MCP server.

This script exercises the publicly-exposed tools against a set of test files:

* Office-style documents (`.doc*`, `.xls*`, `.ppt*`, etc.) are converted to PDF with
  `noRasterize=True` for full fidelity output.
* All other files are converted to PNG, preserving the original dimensions unless
  an explicit size override is provided.
* Optionally serves the same assets over HTTP and calls `convert_url` to validate the
  remote-ingestion path.

Usage:
    uv run python scripts/run_mcp_e2e.py \
        --api-key $TWEEKIT_API_KEY \
        --api-secret $TWEEKIT_API_SECRET \
        --server-url http://127.0.0.1:8080/mcp/

Environment variables `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET` are used as
defaults for the credentials when flags are omitted.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import json
import os
import shutil
import subprocess
import sys
import threading
from getpass import getpass
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

from fastmcp import Client


IMAGE_EXTS = {"png", "jpg", "jpeg", "tif", "tiff", "gif", "bmp", "heic", "heif", "psd", "ai", "fff"}
DOC_TO_PDF_EXTS = {
    "doc",
    "docx",
    "docm",
    "dot",
    "dotm",
    "rtf",
    "odt",
    "xls",
    "xlsx",
    "xlsm",
    "csv",
    "ppt",
    "pptx",
    "pptm",
    "pot",
    "potx",
    "potm",
    "pps",
    "ppsx",
    "ppsm",
    "odp",
}

# fallback extension mapping for files with no suffix or generic extension
@dataclass
class TestResult:
    tool: str
    filename: str
    succeeded: bool
    detail: str


@dataclass
class ConversionSpec:
    outfmt: str
    no_rasterize: bool = False
    width: int = 0
    height: int = 0


def encode_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def sanitize_name(name: str) -> str:
    cleaned = name.strip()
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in cleaned) or "artifact"


def prepare_output_dir(path: Path | None, auto_clear: bool) -> Path | None:
    if path is None:
        return None
    path.mkdir(parents=True, exist_ok=True)
    existing = [p for p in path.iterdir() if p.name != ".gitkeep"]
    if existing:
        if auto_clear:
            clear_directory(existing)
        else:
            try:
                response = input(
                    f"Output directory '{path}' contains {len(existing)} item(s). Clear before continuing? [y/N]: "
                ).strip().lower()
            except EOFError:
                response = ""
            if response in {"y", "yes"}:
                clear_directory(existing)
    return path


def clear_directory(entries: Iterable[Path]) -> None:
    for entry in entries:
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink(missing_ok=True)


def save_response_artifact(
    output_dir: Path | None,
    base_name: str,
    tool: str,
    response,
    default_format: str,
) -> None:
    if output_dir is None:
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_base = sanitize_name(base_name)
    if response.content:
        block = response.content[0]
        raw_bytes, fmt = extract_bytes_and_format(block, default_format)
        if raw_bytes is not None:
            extension = (fmt or default_format or "bin").lstrip(".") or "bin"
            output_path = output_dir / f"{safe_base}__{tool}.{extension}"
            output_path.write_bytes(raw_bytes)
            return
    if response.data is not None:
        output_path = output_dir / f"{safe_base}__{tool}.json"
        output_path.write_text(json.dumps(response.data, indent=2, default=str))


def extract_bytes_and_format(block, default_format: str | None) -> tuple[bytes | None, str | None]:
    fmt = getattr(block, "format", None) or default_format
    raw = getattr(block, "data", None)
    raw_bytes = coerce_to_bytes(raw)
    if raw_bytes is None:
        image_payload = getattr(block, "image", None)
        if image_payload is not None:
            fmt = getattr(image_payload, "format", None) or fmt
            raw_bytes = coerce_to_bytes(getattr(image_payload, "data", None) or getattr(image_payload, "base64", None))
    if raw_bytes is None:
        resource_payload = getattr(block, "resource", None)
        if resource_payload is not None:
            fmt = getattr(resource_payload, "format", None) or fmt
            raw_bytes = coerce_to_bytes(
                getattr(resource_payload, "data", None) or getattr(resource_payload, "base64", None)
            )
    return raw_bytes, fmt


def coerce_to_bytes(value) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        try:
            return base64.b64decode(value, validate=True)
        except Exception:
            return value.encode("utf-8")
    return None


@contextlib.contextmanager
def asset_server(directory: Path):
    """Serve the supplied directory over HTTP for convert_url calls."""

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, *args, **kwargs):  # type: ignore[override]
            return  # suppress noisy logging

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, name="asset-http", daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{httpd.server_port}"
    try:
        yield base_url
    finally:
        httpd.shutdown()
        thread.join(timeout=2)


async def exercise_convert(
    client: Client,
    path: Path,
    api_key: str,
    api_secret: str,
    spec: ConversionSpec,
    inext: str,
    output_dir: Path | None,
) -> TestResult:
    payload = {
        "apiKey": api_key,
        "apiSecret": api_secret,
        "inext": inext,
        "outfmt": spec.outfmt,
        "blob": encode_file(path),
        "noRasterize": spec.no_rasterize,
        "width": spec.width,
        "height": spec.height,
    }
    result = await client.call_tool("convert", payload)
    if result.is_error:
        return TestResult("convert", path.name, False, str(result.error or result.data))
    save_response_artifact(output_dir, path.stem, "convert", result, spec.outfmt)
    info = describe_response(result)
    return TestResult("convert", path.name, True, info)


async def exercise_convert_url(
    client: Client,
    url: str,
    filename: str,
    api_key: str,
    api_secret: str,
    spec: ConversionSpec,
    inext: str,
    output_dir: Path | None,
) -> TestResult:
    payload = {
        "apiKey": api_key,
        "apiSecret": api_secret,
        "url": url,
        "outfmt": spec.outfmt,
        "noRasterize": spec.no_rasterize,
        "width": spec.width,
        "height": spec.height,
    }
    if inext:
        payload["inext"] = inext
    result = await client.call_tool("convert_url", payload)
    if result.is_error:
        return TestResult("convert_url", filename, False, str(result.error or result.data))
    save_response_artifact(output_dir, Path(filename).stem, "convert_url", result, spec.outfmt)
    info = describe_response(result)
    return TestResult("convert_url", filename, True, info)


def describe_response(response) -> str:
    if response.content:
        block = response.content[0]
        block_type = getattr(block, "type", block.__class__.__name__)
        raw_data = getattr(block, "data", None)
        size = len(raw_data) if isinstance(raw_data, (bytes, bytearray)) else None
        size_str = f", {size} bytes" if size is not None else ""
        return f"content={block_type}{size_str}"
    if response.data:
        return f"json={type(response.data).__name__}"
    return "empty response"


def collect_files(directory: Path) -> Iterable[Path]:
    return sorted(p for p in directory.iterdir() if p.is_file() and p.name != ".gitkeep")


async def run_suite(args: argparse.Namespace) -> list[TestResult]:
    api_key, api_secret = resolve_credentials(args)

    files = collect_files(args.asset_dir)
    if not files:
        raise SystemExit(f"No files found in {args.asset_dir}")

    output_dir = prepare_output_dir(args.output_dir, args.auto_clear_output)

    results: list[TestResult] = []
    async with Client(args.server_url) as client:
        for path in files:
            try:
                inext = detect_extension(path)
            except ValueError as exc:
                results.append(TestResult("detect_extension", path.name, False, str(exc)))
                continue
            spec = determine_spec(inext, args)
            if args.outfmt:
                spec.outfmt = args.outfmt
            results.append(await exercise_convert(client, path, api_key, api_secret, spec, inext, output_dir))

        if args.include_convert_url:
            with asset_server(args.asset_dir) as base_url:
                for path in files:
                    encoded_name = quote(path.name)
                    url = f"{base_url}/{encoded_name}"
                    try:
                        inext = detect_extension(path)
                    except ValueError as exc:
                        results.append(TestResult("detect_extension", path.name, False, str(exc)))
                        continue
                    spec = determine_spec(inext, args)
                    if args.outfmt:
                        spec.outfmt = args.outfmt
                    results.append(
                        await exercise_convert_url(
                            client,
                            url=url,
                            filename=path.name,
                            api_key=api_key,
                            api_secret=api_secret,
                            spec=spec,
                            inext=inext,
                            output_dir=output_dir,
                        )
                    )

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run E2E checks against the TweekIT MCP server.")
    parser.add_argument("--server-url", default=os.getenv("TWEEKIT_MCP_BASE_URL", "http://127.0.0.1:8080/mcp/"))
    parser.add_argument("--api-key")
    parser.add_argument("--api-secret")
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=Path(".tweekit_credentials"),
        help="Path to a local credentials file (.env or JSON).",
    )
    parser.add_argument("--asset-dir", type=Path, default=Path("tests/assets"))
    parser.add_argument("--outfmt", help="Force a single output format for all files (default auto-detect).")
    parser.add_argument("--include-convert-url", action="store_true", help="Also call convert_url via a temporary HTTP server.")
    parser.add_argument("--png-width", type=int, default=0, help="Width (pixels) for PNG conversions; default 0 keeps original width.")
    parser.add_argument("--png-height", type=int, default=0, help="Optional height (pixels) for PNG conversions; default 0 keeps original height.")
    parser.add_argument("--output-dir", type=Path, help="Directory to save converted artifacts for manual inspection.")
    parser.add_argument(
        "--auto-clear-output",
        action="store_true",
        help="Automatically clear the output directory without prompting (useful for CI).",
    )
    parser.add_argument(
        "--save-credentials",
        action="store_true",
        help="Persist prompted credentials to --credentials-file for future runs.",
    )
    return parser.parse_args()


def determine_spec(ext: str, args: argparse.Namespace) -> ConversionSpec:
    if ext in DOC_TO_PDF_EXTS:
        return ConversionSpec(outfmt="pdf", no_rasterize=True)
    # Default: image-style conversion to PNG at requested size
    width = max(args.png_width, 0)
    height = max(args.png_height, 0)
    return ConversionSpec(outfmt="png", width=width, height=height)


def detect_extension(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext:
        return ext
    metadata_ext = extract_extension_from_metadata(path)
    if metadata_ext:
        return metadata_ext
    raise ValueError(
        f"Unable to determine file extension for '{path.name}'. Please rename the file to include a valid extension."
    )


def extract_extension_from_metadata(path: Path) -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["mdls", "-raw", "-name", "kMDItemContentTypeTree", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    data = result.stdout.strip()
    if not data:
        return None

    # mdls output example: (
    #   "public.jpeg",
    #   "public.image",
    #   "public.data"
    # )
    candidates: list[str] = []
    for line in data.splitlines():
        line = line.strip().strip(",")
        if line.startswith("(") or line.endswith(")") or not line:
            continue
        token = line.strip('"')
        if token and token != "public.data":
            candidates.append(token)

    for uti in candidates:
        if "." in uti:
            ext = uti.split(".")[-1].lower()
            if ext:
                return ext
    return None


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    api_key = args.api_key or os.getenv("TWEEKIT_API_KEY")
    api_secret = args.api_secret or os.getenv("TWEEKIT_API_SECRET")

    if (not api_key or not api_secret) and args.credentials_file:
        file_key, file_secret = load_credentials_from_file(args.credentials_file)
        api_key = api_key or file_key
        api_secret = api_secret or file_secret

    if not api_key:
        api_key = prompt_value("Enter TWEEKIT_API_KEY: ")
    if not api_secret:
        api_secret = prompt_value("Enter TWEEKIT_API_SECRET: ", secret=True)

    if args.save_credentials and args.credentials_file:
        save_credentials(args.credentials_file, api_key, api_secret)

    if not api_key or not api_secret:
        raise SystemExit("Unable to resolve TweekIT credentials. Provide via CLI, env vars, or credentials file.")

    return api_key, api_secret


def load_credentials_from_file(path: Path) -> tuple[str | None, str | None]:
    try:
        if not path.exists():
            return None, None
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None, None

    text = text.strip()
    if not text:
        return None, None

    # JSON with fields {"apiKey": "...", "apiSecret": "..."}
    if text.startswith("{"):
        try:
            data = json.loads(text)
            return data.get("apiKey"), data.get("apiSecret")
        except Exception:
            return None, None

    # Simple KEY=VALUE format (.env)
    key = None
    secret = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip().lower()
        value = value.strip().strip('"').strip("'")
        if name in {"tweekit_api_key", "apikey", "api_key"}:
            key = value
        elif name in {"tweekit_api_secret", "apisecret", "api_secret"}:
            secret = value
    return key, secret


def save_credentials(path: Path, api_key: str, api_secret: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            "# Auto-generated by run_mcp_e2e.py\n"
            f"TWEEKIT_API_KEY={api_key}\n"
            f"TWEEKIT_API_SECRET={api_secret}\n"
        )
        path.write_text(content, encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    except Exception as exc:
        print(f"Warning: failed to save credentials to {path}: {exc}")


def prompt_value(prompt: str, *, secret: bool = False) -> str:
    try:
        if secret:
            return getpass(prompt).strip()
        return input(prompt).strip()
    except EOFError:
        return ""


def print_summary(results: list[TestResult]) -> None:
    successes = sum(1 for r in results if r.succeeded)
    failures = [r for r in results if not r.succeeded]
    print(f"\nCompleted {len(results)} checks: {successes} succeeded, {len(failures)} failed.")
    for res in results:
        status = "✅" if res.succeeded else "❌"
        print(f"  {status} {res.tool:<11} {res.filename}: {res.detail}")
    if failures:
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    results = asyncio.run(run_suite(args))
    print_summary(results)


if __name__ == "__main__":
    main()
