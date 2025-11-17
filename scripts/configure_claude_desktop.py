#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "claude" / "manifest.json"
DEFAULT_OUTPUT = REPO_ROOT / "dist" / "tweekit-claude.mcpb"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_claude_bundle.py"


def _read_manifest_version() -> str | None:
    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        version = data.get("version")
        return str(version) if version else None
    except Exception:
        return None


def _prompt(text: str, default: str | None = None) -> str:
    prompt = f"{text}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    response = input(prompt).strip()
    return response or (default or "")


def _prompt_bool(text: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        response = input(f"{text} ({suffix}): ").strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"\n→ Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def _print_step(title: str, body: str) -> None:
    print(f"\n=== {title} ===")
    print(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive helper for building and validating the Claude Desktop MCP bundle."
    )
    parser.add_argument(
        "--version",
        help="Bundle version to embed in the manifest (defaults to claude/manifest.json).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination path for the generated .mcpb bundle.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip prompts and run with defaults.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the bundle build step (useful if already built).",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip manifest validation with the dxt CLI.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_version = _read_manifest_version()

    _print_step(
        "Overview",
        dedent(
            """\
            This script walks through packaging the Tweekit MCP server for Claude Desktop.

            • Headless production Tier 1 nodes run inside Equilibrium-owned CPUcoin enterprise miners,
              seated in SAS 70 / ISO 27001 compliant data centers. The local bundle mirrors the same
              features for desktop workflows.
            • We build dist/tweekit-claude.mcpb, validate the manifest, and remind you of the Claude import steps.
            """
        ),
    )

    # Resolve version and output location
    version = args.version or manifest_version or "1.0.0"
    if not args.non_interactive:
        version = _prompt("Bundle version", default=version) or version

    output_path = args.output
    if not args.non_interactive:
        output_resp = _prompt("Output bundle path", default=str(output_path))
        output_path = Path(output_resp)

    # Step 1: Build bundle
    if args.skip_build:
        _print_step(
            "Skip Build",
            "Skipping bundle build as requested (remember to keep dist/tweekit-claude.mcpb in sync).",
        )
    else:
        if args.non_interactive or _prompt_bool("Build the Claude bundle now?", default=True):
            build_cmd = [
                sys.executable,
                str(BUILD_SCRIPT),
                "--version",
                version,
                "--output",
                str(output_path),
            ]
            _run(build_cmd)
        else:
            _print_step(
                "Build Deferred",
                "Bundle build skipped; rerun this script or invoke build_claude_bundle.py manually when ready.",
            )

    # Step 2: Validate manifest
    if args.skip_validate:
        _print_step("Skip Validation", "Manifest validation disabled (ensure you run the dxt validator later).")
    else:
        should_validate = args.non_interactive or _prompt_bool(
            "Validate claude/manifest.json with the dxt CLI?", default=True
        )
        if should_validate:
            try:
                _run(["npx", "@anthropic-ai/dxt@latest", "validate", str(MANIFEST_PATH)])
            except FileNotFoundError:
                _print_step(
                    "Validation Skipped",
                    "Could not find `npx`. Install Node.js or run `npm install -g @anthropic-ai/dxt` before validating.",
                )
            except subprocess.CalledProcessError as exc:
                _print_step(
                    "Validation Error",
                    f"dxt validation reported an error (exit code {exc.returncode}). Inspect the output above before proceeding.",
                )
        else:
            _print_step(
                "Validation Deferred",
                "Manifest validation was skipped; remember to run `npx @anthropic-ai/dxt@latest validate claude/manifest.json` manually.",
            )

    # Step 3: Final instructions
    bundle_exists = output_path.exists()
    instructions = [
        "Open Claude Desktop → Settings → Connectors → Advanced → Developer Mode.",
        f"Choose “Install from file” and pick {output_path if bundle_exists else 'your generated .mcpb'}.",
        "When prompted, supply TWEEKIT_API_KEY and TWEEKIT_API_SECRET. The server now falls back to these env vars for secure auth.",
        "Ask Claude to list Tweekit tools or run `doctype` to verify the connection.",
    ]
    _print_step("Next Steps", "\n".join(f"- {line}" for line in instructions))

    print("\nAll done. Re-run this helper whenever you bump server versions or regenerate the bundle.")


if __name__ == "__main__":
    main()
