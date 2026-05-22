# Developer Tool Integrations

This guide summarizes how to connect the hosted TweekIT MCP server to popular IDE assistants and automation environments. Update the URLs if you run your own deployment (defaults assume `https://mcp.tweekit.io/mcp`).

## Cursor
Cursor reads configuration from `~/.cursor/mcp.json`. Merge the snippet below (also available at `configs/cursor-mcp.json`) into that file or publish it through an “Add to Cursor” link on your docs site.

```json
{
  "mcpServers": {
    "tweekit": {
      "type": "http",
      "url": "https://mcp.tweekit.io/mcp",
      "headers": {
        "ApiKey": "${TWEEKIT_API_KEY}",
        "ApiSecret": "${TWEEKIT_API_SECRET}"
      }
    }
  }
}
```

Steps:
1. Set `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET` in your shell or replace the placeholders with literal values.
2. Restart Cursor; open the command palette and run “List tools” to confirm TweekIT endpoints are reachable.
3. Optional: host the JSON at `https://tweekit.com/cursor-mcp.json` and surface an `<a href="cursor://add-mcp?config=...">Add to Cursor</a>` button.

## Continue (VS Code / JetBrains)
Continue stores MCP servers in `~/.continue/config.json`. Add the following entry under the `mcpServers` key (see `configs/continue-mcp.json` for a ready-to-copy version).

```json
{
  "mcpServers": {
    "tweekit": {
      "type": "streamable-http",
      "url": "https://mcp.tweekit.io/mcp",
      "headers": {
        "ApiKey": "${TWEEKIT_API_KEY}",
        "ApiSecret": "${TWEEKIT_API_SECRET}"
      }
    }
  }
}
```

After saving:
1. Reload the Continue extension.
2. Use the Continue panel → Tools tab to verify `tweekit` shows `version`, `doctype`, `convert`, and `convert_url`.
3. Document any workspace-specific env var requirements in your team README.

## OpenAI Codex CLI

The OpenAI Codex CLI (`@openai/codex`) is a terminal-based AI coding agent that supports MCP servers as first-class plugins. Install it once and TweekIT tools become available in every Codex session.

**Install Codex CLI:**
```bash
npm install -g @openai/codex
```

**Option A — Persistent config** (`~/.codex/config.yaml`):

Merge the block below into your config file (ready-to-copy version at `configs/codex-mcp.yaml`):

```yaml
mcpServers:
  tweekit:
    type: http
    url: https://mcp.tweekit.io/mcp
    headers:
      ApiKey: "${TWEEKIT_API_KEY}"
      ApiSecret: "${TWEEKIT_API_SECRET}"
```

**Option B — One-liner session plugin (easy plugin):**

Pass the server directly on the command line without editing any config file:

```bash
export TWEEKIT_API_KEY=your_key TWEEKIT_API_SECRET=your_secret
codex --mcp-server tweekit:https://mcp.tweekit.io/mcp
```

After connecting, use TweekIT tools directly in Codex:
```
> Use TweekIT to convert this DOC file to PDF
> Check what file formats TweekIT supports (doctype)
> Convert the image at https://example.com/photo.png to WebP at 800x600
```

Steps for persistent config:
1. Set `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET` in your shell (or `.env`).
2. Merge `configs/codex-mcp.yaml` into `~/.codex/config.yaml`.
3. Run `codex` and ask it to list available tools to confirm TweekIT is connected.

## Other IDE Assistants
- **Windsurf / Sourcegraph Cody:** Both accept MCP endpoints through their beta settings; use the same URL and headers.
- **Flowise / LangChain:** Wrap the REST proxy (`plugin_proxy.py`) so low-code pipelines can call `POST /convert`.
- **Custom agents:** Reuse the `scripts/deepseek_mcp_bridge.py` utility or import the helper into your orchestration logic.

## Operational Notes
- Rotate credentials via environment variables or secret managers—avoid hard-coding keys in committed JSON.
- For enterprise environments, serve configuration files from an internal asset host and provide SSO-protected documentation.
- Validate connectivity after each TweekIT deploy; automate with a lightweight MCP health check script if possible.
