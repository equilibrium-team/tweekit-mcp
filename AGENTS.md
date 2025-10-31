# Repository Guidelines

## Project Structure & Module Organization
- `server.py` runs the FastMCP streamable HTTP server for local development; keep API helpers here.
- `functions/main.py` exposes the Firebase HTTP entry point and ASGI bridge used in production.
- `functions/requirements.txt` and `functions/packages/` store vendored deps for Firebase; never edit generated wheels by hand.
- `scripts/deploy_firebase.sh` handles vendoring plus `firebase deploy`; review flags before running.
- `scripts/deploy_cloud_run.sh` builds via Cloud Build and deploys to Cloud Run (`stage`/`prod` targets).
- Config roots (`pyproject.toml`, `firebase.json`, `uv.lock`) define Python deps and hosting rewrites.
- `test_server.py` provides async smoke tests with `fastmcp.Client`; set the base URL per environment.
- `tests/` contains pytest suites for proxy, bundles, config files, and client SDK helpers.

## Build, Test, and Development Commands
- Install / sync deps: `uv sync` or `pip install -e .[dev]`.
- Run the MCP server locally: `uv run python server.py` (override with `PORT=9090 …`).
- Smoke test endpoints: `uv run python test_server.py --base-url <URL>`.
- Vendor Firebase deps: `uv pip install -r functions/requirements.txt --target functions/packages` (use `pip` if `uv` unavailable).
- Deploy to Firebase: `bash scripts/deploy_firebase.sh -p <PROJECT_ID> [--skip-vendor]`.
- Deploy to Cloud Run: `bash scripts/deploy_cloud_run.sh <stage|prod> --version <x.y.z>`.
- Full pytest suite (requires API secrets): `TWEEKIT_API_KEY=… TWEEKIT_API_SECRET=… uv run python -m pytest`.

## Coding Style & Naming Conventions
- Python ≥3.10 with PEP 8 defaults: four-space indents, snake_case functions, SCREAMING_SNAKE_CASE env constants.
- Prefer async HTTP flows with `httpx.AsyncClient`; always call `response.raise_for_status()` and log via `logging.getLogger(__name__)`.
- Use docstrings on FastMCP tools/resources and include type hints so FastMCP preserves schema metadata.
- Keep responses FastMCP-friendly (`Image`, `File`, or JSON-serializable payloads) and avoid leaking API credentials in logs.

## Testing Guidelines
- Integration smoke tests live in `test_server.py`; extend with awaited helpers and keep assertions lightweight.
- Pytest suites in `tests/` should follow `test_*` coroutine naming and reuse `fastmcp.Client` fixtures.
- Update `uv.lock` when dependency pins change and rerun pytest plus targeted Cloud Run/Firebase smoke checks.
- After deploying to Firebase Hosting, point `test_server.py --base-url https://<PROJECT_ID>.web.app/mcp` and rerun.

## Commit & Pull Request Guidelines
- Subjects: concise, present tense (~72 chars). Group related changes; call out environment or deploy impacts in bodies.
- Include executed commands (`uv run python test_server.py`, `pytest`, deploy scripts) and attach logs/screenshots for behavior changes.
- Keep diffs focused; avoid unrelated refactors or vendored churn unless accompanied by updated wheels/reports.

## Security & Configuration Tips
- Never commit API credentials. Source `TWEEKIT_API_KEY` / `TWEEKIT_API_SECRET` (and Cloud Run secrets) from env managers.
- Use `firebase login` / `gcloud auth login` locally; leave long-lived tokens out of repo scripts.
- Watch `functions/packages/` size after vendoring; regenerate wheels whenever requirements change.
- Enforce reasonable HTTP timeouts and validate external inputs before proxying to TweekIT.

## Architecture Overview
- Stateless FastMCP wrapper around the TweekIT REST API (`BASE_URL` in `server.py`).
- Returns binary results via FastMCP `Image` / `File`; all other responses are JSON payloads.
- Cloud Run deploy uses `scripts/deploy_cloud_run.sh`; Firebase Hosting rewrite targets `functions/main.py`.

## Client Compatibility
- Claude Desktop / Claude App: compatible via MCP manifest (`claude/manifest.json`).
- ChatGPT MCP, Cursor, Continue: ship configs under `configs/`; follow instructions in `docs/developer-tools.md`.
- Additional integrations (ChatGPT plugin proxy, Grok, DeepSeek) documented in `docs/*.md`.
