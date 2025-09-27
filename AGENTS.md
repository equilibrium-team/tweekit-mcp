# Repository Guidelines

## Project Structure & Module Organization
- `server.py`: FastMCP server exposing `resource: version` and tools `doctype`, `convert` (proxies TweekIT REST API).
- `test_server.py`: Async smoke test using `fastmcp.Client` against the hosted or local server.
- `pyproject.toml` / `uv.lock`: Python deps managed by `uv` (Python ≥3.10).
- `Dockerfile`: Container build using `uv`. Keep runtime minimal.

## Build, Test, and Development Commands
- Install deps: `uv sync`
- Run locally: `uv run server.py` (override port with `PORT=9090 uv run server.py`).
- Execute tests: `TWEEKIT_APIKEY=... TWEEKIT_APISECRET=... uv run python test_server.py`
- Docker build/run: `docker build -t tweekit-mcp .` then `docker run -e PORT=8080 -p 8080:8080 tweekit-mcp`
- Switch tests to local: edit `test_server.py` and set `mcp_url = "http://localhost:8080/mcp/"`.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4‑space indentation and type hints for public functions.
- Prefer `logging` over `print` in server code; keep log level configurable.
- HTTP: use `httpx.AsyncClient` with explicit timeouts; handle `HTTPStatusError` and `RequestError`.
- Parameters and return types should align with FastMCP primitives (`Image`, `File`) or JSON‑serializable dicts.

## Testing Guidelines
- Tests require env vars `TWEEKIT_APIKEY` and `TWEEKIT_APISECRET`.
- `test_server.py` validates: resource `version` format, `doctype` JSON shape, and `convert` returns `image`/`resource`.
- Keep new tests async and minimal; prefer end‑to‑end calls via `fastmcp.Client`.

## Commit & Pull Request Guidelines
- Commit messages: short, imperative (“Add …”, “Fix …”), no scope tags required (match existing history).
- PRs: include summary, rationale, affected files, and local run instructions; link issues and add screenshots/logs if relevant.
- Keep changes focused; avoid unrelated refactors.

## Security & Configuration Tips
- Never commit credentials; use env vars. Do not log `ApiKey`/`ApiSecret`.
- Validate and sanitize external inputs; enforce reasonable payload sizes and timeouts.

## Architecture Overview
- Thin MCP wrapper over TweekIT REST API (`BASE_URL` in `server.py`).
- Returns binary results via FastMCP `Image`/`File`; all other responses are JSON.
- Stateless by design; no persistent storage in this service.

## Client Compatibility
- Claude: Compatible (tools discoverable via `listTools`).
- ChatGPT: Compatible (provides `search` and `fetch`).
- Cursor: Not targeted (no workspace/file tools exposed).
