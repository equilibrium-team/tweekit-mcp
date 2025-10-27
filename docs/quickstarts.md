# TweekIT MCP Quickstarts

These examples help developers call the TweekIT MCP server from Python or Node.js in under five minutes. Update the server URL or authentication values if you run a self-hosted deployment.

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
