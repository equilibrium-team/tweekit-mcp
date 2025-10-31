# TweekIT Claude Bundle

This bundle configures Claude Desktop to connect to the hosted TweekIT MCP server via the streamable HTTP transport. Update the manifest before shipping to ensure the server URL and metadata are accurate.

## Files
- `manifest.json` – bundle manifest consumed by Claude Desktop.
- `README.md` – quick reference for operators.

## Customization Checklist
1. Replace `entry_point.url` with the production MCP endpoint (defaults to `https://mcp.tweekit.com/mcp`).
2. Confirm the required environment variables match your authentication model.
3. Bump the `version` and update the changelog when shipping edits.

## Packaging
Use `python scripts/build_claude_bundle.py` (see docs) to produce `dist/tweekit-claude.mcpb`. Distribute that file to Claude Desktop users for one-click installation.
