# Claude Desktop Bundle Guide

This guide explains how to package and distribute the TweekIT MCP server for Anthropic Claude Desktop using the `.mcpb` bundle format.

## Overview
- The bundle references the hosted streamable HTTP endpoint (`https://mcp.tweekit.io/mcp` by default).
- Users supply their TweekIT credentials through Claude's environment settings when importing the bundle.
- The build script emits `dist/tweekit-claude.mcpb`, which Claude Desktop can install with one click.

## Prerequisites
- Python 3.10+
- Zipfile-compatible environment (built into Python)
- Access to a public TweekIT MCP endpoint

## Update Manifest Metadata
Edit `claude/manifest.json` to ensure:
- `entry_point.url` points at the production MCP server.
- `version`, `description`, and `homepage` reflect the current release.
- Environment variables align with your authentication model (defaults to `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET`).

## Build the Bundle
```bash
python scripts/build_claude_bundle.py \
  --server-url https://mcp.tweekit.io/mcp \
  --version 0.1.0 \
  --output dist/tweekit-claude.mcpb
```

Environment variables `CLAUDE_MCP_SERVER_URL` and `CLAUDE_MCP_VERSION` may also be used to override defaults.

## Verify Contents
```bash
unzip -l dist/tweekit-claude.mcpb
cat dist/manifest.json  # optional spot check
```

## Install in Claude Desktop
1. Open Claude Desktop.
2. Navigate to **Settings → Extensions → Local MCP Servers**.
3. Click **Import Bundle** and select `tweekit-claude.mcpb`.
4. Provide `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET` when prompted.
5. Test by asking Claude to list TweekIT tools or convert a sample document.

## Distribution Notes
- Share the `.mcpb` file via secure download or internal portal.
- Maintain a changelog and update the manifest version with each release.
- Before submission to Anthropic’s directory, capture install screenshots and confirm bundle validation inside Claude’s tooling.
