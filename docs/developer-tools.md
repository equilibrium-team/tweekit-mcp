# Developer Tool Integrations

This guide summarizes how to connect the hosted TweekIT MCP server to popular IDE assistants and automation environments. Update the URLs if you run your own deployment (defaults assume `https://mcp.tweekit.com/mcp`).

## Cursor
Cursor reads configuration from `~/.cursor/mcp.json`. Merge the snippet below (also available at `configs/cursor-mcp.json`) into that file or publish it through an “Add to Cursor” link on your docs site.

```json
{
  "mcpServers": {
    "tweekit": {
      "type": "http",
      "url": "https://mcp.tweekit.com/mcp",
      "headers": {
        "ApiKey": "${TWEAKIT_API_KEY}",
        "ApiSecret": "${TWEAKIT_API_SECRET}"
      }
    }
  }
}
```

Steps:
1. Set `TWEAKIT_API_KEY`/`TWEAKIT_API_SECRET` in your shell or replace the placeholders with literal values.
2. Restart Cursor; open the command palette and run “List tools” to confirm TweekIT endpoints are reachable.
3. Optional: host the JSON at `https://tweekit.com/cursor-mcp.json` and surface an `<a href="cursor://add-mcp?config=...">Add to Cursor</a>` button.

## Continue (VS Code / JetBrains)
Continue stores MCP servers in `~/.continue/config.json`. Add the following entry under the `mcpServers` key (see `configs/continue-mcp.json` for a ready-to-copy version).

```json
{
  "mcpServers": {
    "tweekit": {
      "type": "streamable-http",
      "url": "https://mcp.tweekit.com/mcp",
      "headers": {
        "ApiKey": "${TWEAKIT_API_KEY}",
        "ApiSecret": "${TWEAKIT_API_SECRET}"
      }
    }
  }
}
```

After saving:
1. Reload the Continue extension.
2. Use the Continue panel → Tools tab to verify `tweekit` shows `version`, `doctype`, and `convert`.
3. Document any workspace-specific env var requirements in your team README.

## Other IDE Assistants
- **Windsurf / Sourcegraph Cody:** Both accept MCP endpoints through their beta settings; use the same URL and headers.
- **Flowise / LangChain:** Wrap the REST proxy (`plugin_proxy.py`) so low-code pipelines can call `POST /convert`.
- **Custom agents:** Reuse the `scripts/deepseek_mcp_bridge.py` utility or import the helper into your orchestration logic.

## Operational Notes
- Rotate credentials via environment variables or secret managers—avoid hard-coding keys in committed JSON.
- For enterprise environments, serve configuration files from an internal asset host and provide SSO-protected documentation.
- Validate connectivity after each TweekIT deploy; automate with a lightweight MCP health check script if possible.
