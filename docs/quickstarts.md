# TweekIT MCP Quickstarts

These examples help developers call the TweekIT MCP server from Python or Node.js in under five minutes. Update the server URL or authentication values if you run a self-hosted deployment.

## Web Converter (Claude File Format Enabler)

For **non-developers** or anyone wanting a quick browser-based solution to convert files for Claude, use our standalone web converter:

**Location**: `examples/web-converter/index.html`

This tool solves Claude's file type limitations by converting 450+ unsupported formats (legacy DOC, XLS, PPT, PSD, DWG, etc.) into Claude-compatible formats (PDF, PNG, JPEG, WebP).

**Quick Start**:
```bash
cd examples/web-converter
python3 -m http.server 8080
# Open http://localhost:8080
```

Or simply open `index.html` directly in your browser. See [`examples/web-converter/README.md`](../examples/web-converter/README.md) for full documentation.

This is ideal for:
- Claude users who need to convert files before uploading
- Quick one-off conversions without writing code
- Testing TweekIT capabilities before integrating the MCP server

## Python
### Requirements
- Python 3.10+
- `pip install fastmcp`
- Set `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET`

### Run the Example
```bash
python examples/python/quickstart.py \
  --file path/to/input.pdf \
  --outfmt txt
```

The script prints the available tools and outputs the converted payload. For reusable code inside your own projects, import `clients.python.tweekit_client.TweekitClient` and call `convert_file` or `convert_url` directly.

## Node.js
### Requirements
- Node.js 18+
- `npm install @modelcontextprotocol/sdk`
- Set `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET`

### Run the Example
```bash
node examples/node/quickstart.mjs \
  --file path/to/input.pdf \
  --outfmt txt
```

The script lists tools and performs a conversion, returning either binary/base64 data or structured output.

## Packaging Guidance
- Wrap the helper client (`clients/python/tweekit_client.py`) or Node quickstart code in your own services to orchestrate conversions before sending normalized output to agents.
- Add tests that mock the MCP server or run against staging endpoints to ensure backward compatibility with new TweekIT releases.
- To generate SDKs, expand the helpers into publishable packages (PyPI/NPM) and hook into CI for versioned releases.
- Once staging endpoints exist, add end-to-end integration tests that exercise the quickstarts with real credentials, gating them behind environment variables (skip in CI when unset).

## Finding Remote Files with `search`

The `search` MCP tool performs a lightweight DuckDuckGo query and returns result links with titles/snippets. Use it when you need a public document or image to convert on the fly:

1. Call `search` (for example, “sample invoice PDF”).
2. Take one of the returned URLs.
3. Pass that URL to `convert_url` to fetch and normalize the file, or download it yourself and feed it into `convert`.

This keeps a single MCP workflow self‑contained—discover the asset, pull it down, then run the conversion without leaving the agent. The tool is optional but handy for on-demand web sourcing ahead of a conversion task.

> **Why DuckDuckGo?** The HTML endpoint works without API keys and is tolerant of light scraping, which keeps the MCP server dependency-free. If you prefer another provider, replace the request/HTML parsing in `server.py` with your chosen API.
