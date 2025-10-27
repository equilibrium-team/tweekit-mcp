# Testing Strategy & Playbook

This document defines the repeatable steps we follow before every significant change or release. It combines automated regression coverage with manual UI walkthroughs so we can validate the TweekIT MCP server across command-line, IDE, and hosted integrations.

## 1. Automated Coverage

### 1.1 Pytest Suite (fast, hermetic)
Runs mocked unit/integration tests for the proxy, Claude bundle tooling, client helpers, and IDE configs.

```bash
uv run python -m pytest
```

### 1.2 File Conversion Sweep (`run_mcp_e2e.py`)
Exercises live conversions against a running MCP server using the sample assets in `tests/assets/`.

```bash
uv run python scripts/run_mcp_e2e.py \
  --server-url http://127.0.0.1:8080/mcp/ \
  --credentials-file .tweekit_credentials \
  --include-convert-url
```

Behaviour:
- Documents (`.doc*`, `.xls*`, `.ppt*`, etc.) ➜ PDF (`noRasterize=True`).
- All other assets ➜ PNG (original dimensions unless `--png-width/--png-height` overrides).
- `--include-convert-url` spins up a temporary HTTP server to feed `convert_url` the same files.
- Outputs a line-by-line pass/fail summary; the script exits non-zero if any conversions fail.

To capture artifacts for visual inspection, add:

```bash
  --output-dir tests/output \
  --credentials-file .tweekit_credentials
```

Credential options:
- Provide `--api-key/--api-secret` on the CLI, or
- Supply `--credentials-file` (JSON or `.env` style). Add `--save-credentials` the first time to persist prompts to `.tweekit_credentials`, or
- Set environment variables (`TWEAKIT_API_KEY`, `TWEAKIT_API_SECRET`).

If the output directory already contains files, the script prompts to clear them (use `--auto-clear-output` to skip the prompt in CI). The repository ignores everything under `tests/assets/`, `tests/output/`, and `.tweekit_credentials`, so sample inputs, generated artifacts, and local secrets never ship with staging/production deploys.

#### Using Staging or Production Endpoints

Override `--server-url` and keep separate credential files per environment. Example:

```bash
uv run python scripts/run_mcp_e2e.py \
  --server-url https://tweekit-mcp-stage-958133016924.us-west1.run.app/mcp \
  --credentials-file .tweekit_stage_credentials \
  --include-convert-url \
  --output-dir tests/output/stage
```

```bash
uv run python scripts/run_mcp_e2e.py \
  --server-url https://mcp.tweekit.com/mcp/ \
  --credentials-file .tweekit_prod_credentials \
  --include-convert-url \
  --output-dir tests/output/prod
```

Add `--save-credentials` the first time you run each command to persist the prompts into the chosen credentials file. Each file remains ignored by git, but make sure to store them securely (e.g., password manager) if you share them between teammates.

### 1.3 Live Smoke (`test_server.py`)
Useful when pointed at staging/production endpoints. It calls each tool, validates binary responses, and reports missing checks.

```bash
uv run python test_server.py --base-url https://mcp.tweekit.com/mcp/
```

### 1.4 Coverage Gaps & TODOs
- Node.js quickstart lacks automated tests; add when MCP clients support offline mocking.
- DeepSeek bridge script only has unit coverage; integrate it once staging secrets exist.
- IDE configs are schema-checked but not exercised end-to-end; consider headless tests if platform tooling emerges.

## 2. Manual UI & Integration Checklist

Run these steps for release candidates, major refactors, or whenever UI/manifest changes land. Capture notes/screenshots for the deploy log.

### 2.1 MCP Inspector (local sanity)
1. Start the server: `uv run python server.py` (ensure `PORT` free).
2. Launch MCP Inspector using `configs/inspector-mcp.json`.
3. Confirm tools/resources appear: `doctype`, `convert`, `convert_url`, `fetch`, `search`, version resources.
4. Invoke `convert` with `tests/assets/Sample Image 3.fff`; confirm image renders.
5. Invoke `convert_url` pointing to the temporary HTTP server from `run_mcp_e2e.py` or a known URL.

### 2.2 Claude Desktop Bundle
1. Build bundle: `uv run python scripts/build_claude_bundle.py --version <x.y.z>`.
2. Import `.mcpb` in Claude Desktop (macOS + Windows smoke).
3. Set env vars inside Claude (`TWEAKIT_API_KEY`, `TWEAKIT_API_SECRET`).
4. Ask Claude to list tools; ensure `convert_url` metadata appears.
5. Request a conversion (DOC ➜ PDF, PNG ➜ PNG) and ensure the returned files open.

### 2.3 ChatGPT MCP (Custom GPT / Tools panel)
1. Configure an MCP server with URL + headers:
   - URL: `https://mcp.tweekit.com/mcp/` (or staging).
   - Headers: `ApiKey`, `ApiSecret`.
2. In a chat, run:
   - `doctype` for `pdf`.
   - `convert` with a base64 PNG sample (short snippet from `tests/assets/test.png` if available).
   - `convert_url` against `https://raw.githubusercontent.com/equilibrium-team/tweekit-mcp/main/test.png`.
3. Verify ChatGPT returns `File` downloads or JSON blocks appropriately.

### 2.4 ChatGPT Plugin Proxy (if deploying `plugin_proxy.py`)
1. Start local proxy: `uv run uvicorn plugin_proxy:app --port 8000`.
2. Curl endpoints: `/version`, `/doctype?ext=pdf`, `/convert`.
3. Visit `/.well-known/ai-plugin.json` and check manifest fields (logo, auth instructions).
4. Optionally expose via ngrok and confirm ChatGPT Action import.

### 2.5 Cursor IDE
1. Merge `configs/cursor-mcp.json` into `~/.cursor/mcp.json` with local/staging URL.
2. Restart Cursor.
3. From command palette: `MCP: List Tools` (expect `convert_url`).
4. Run a conversion of `Operation Class Implementation .doc` ➜ PDF, verify output saved to workspace.

### 2.6 Continue IDE (VS Code / JetBrains)
1. Update `~/.continue/config.json` with the snippet from `docs/developer-tools.md`.
2. Reload Continue.
3. Use the Tools tab to run `convert` on an image and `convert_url` on a remote asset. Confirm response attachments.

### 2.7 Additional Integrations (as needed)
- **MCP Inspector (hosted)** – Repeat step 2.1 using the Cloud Run endpoint before production deploys.
- **FastAPI Proxy ➜ ChatGPT Actions** – After deploying the proxy, run the same curl checks against the staging URL and capture Auth instructions screenshots.
- **Third-party bridges (DeepSeek, Grok, etc.)** – Follow documentation in `docs/deepseek-integration.md` / `docs/grok-integration.md` and note pass/fail outcomes.

## 3. Recording Results

- Track automated runs (pytest + script) in CI or attach terminal logs to the release issue.
- For manual steps, maintain a short checklist in the PR/issue template with pass/fail, environment, date, and tester.
- Raise issues immediately for any failed step; do not proceed to deploy without a resolution or documented waiver.

## 4. Ownership & Future Work

- **Primary owners:** Platform integration maintainers (proxy/bundle/tests) and SDK authors (clients/examples).
- **Next steps:** add opt-in staging E2E pytest markers once credentials and test environments are stable; expand headless IDE tests when upstream tooling matures.
- **CI reminder:** ensure every PR runs `uv run python -m pytest`; consider adding the sweep script to a nightly job against staging to catch conversion regressions early.
