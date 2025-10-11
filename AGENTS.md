# Repository Guidelines

## Project Structure & Module Organization
- `server.py` runs the FastMCP streamable HTTP server for local development; keep API helpers here.
- `functions/main.py` wraps the Firebase HTTP entry point and ASGI bridge used in production.
- `functions/requirements.txt` and `functions/packages/` store vendored deps for Firebase; do not edit generated wheels.
- `scripts/deploy_firebase.sh` handles vendoring plus `firebase deploy`; review flags before running.
- `test_server.py` exercises live endpoints with `fastmcp.Client`; adjust the base URL per environment.
- Config roots (`pyproject.toml`, `firebase.json`, `uv.lock`) define Python deps and hosting rewrites.

## Build, Test, and Development Commands
- `uv run python server.py` – start the MCP server on `localhost:8080` using the streamable HTTP transport.
- `uv run python test_server.py` – list tools against the configured endpoint; update the URL if you switch targets.
- `uv pip install -r functions/requirements.txt --target functions/packages` – vendor deps for Firebase (use `pip` if `uv` missing).
- `bash scripts/deploy_firebase.sh -p <PROJECT_ID>` – vendor dependencies (unless `--skip-vendor`) and deploy functions + hosting.
- `pip install -e .[dev] && pytest` – run automated integration tests (proxy, bundle, configs, clients).

## Coding Style & Naming Conventions
- Python 3.10+ with PEP 8 defaults: four-space indents, snake_case functions, SCREAMING_SNAKE_CASE env constants.
- Prefer async HTTP flows with `httpx.AsyncClient`; always surface `response.raise_for_status()` for API calls.
- Use docstrings to describe FastMCP tools; include argument types to retain FastMCP type metadata.
- Keep logging via `logging.getLogger(__name__)` and respect the `LOG_LEVEL` env override.

## Testing Guidelines
- Integration tests live in `test_server.py`; extend with async helpers and awaited assertions.
- Name new test coroutines `test_*` for discovery and reuse `fastmcp.Client` contexts.
- Run suites via `uv run python -m pytest` if you add PyTest tests; pin requirement changes with them.
- After deploying to Firebase, point the client at `https://<PROJECT_ID>.web.app/mcp` and rerun the script.

## Commit & Pull Request Guidelines
- Use concise, present-tense subjects (~72 chars) aligned with current history.
- Group related changes and flag environment impacts in commit bodies.
- PRs must cover scope, executed tests (`uv run python test_server.py`), and linked issues or deploy notes.
- Attach screenshots or logs when behavior changes observable outputs (tool listings, deployment results).
- Include `pytest` output when modifying integration tooling, ensuring the automated suite remains green.

## Security & Configuration Tips
- Never commit API credentials; load `ApiKey`/`ApiSecret` from env vars or secrets managers before invoking tools.
- Keep `FIREBASE_TOKEN` set only in local shells and rely on `firebase login` for interactive auth.
- Watch `functions/packages/` size in PRs; re-run vendoring after dependency bumps to ensure reproducible deploys.
