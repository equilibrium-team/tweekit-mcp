# Automated Testing Strategy

This repository ships with a pytest-based test suite to validate MCP integrations without calling external services. Contributors should run the tests before submitting changes and add coverage for new connectors or tooling.

## Test Coverage
- **ChatGPT proxy (`plugin_proxy.py`)** – Uses mocked HTTP responses to validate `/version`, `/doctype`, `/convert`, and the manifest route.
- **Claude bundle tooling** – Ensures the bundler embeds metadata, rewrites the endpoint, and packages supporting docs.
- **IDE configs** – Verifies Cursor/Continue JSON files contain the expected schema and secrets placeholders.
- **Python helper client** – Exercises the `TweekitClient` wrapper with a fake MCP client to confirm payload construction and credential handling.
- **Staging E2E (future)** – When live MCP endpoints and credentials are available, extend the suite with opt-in tests (skipped by default) to validate real conversions and bridge scripts.

### Coverage Gaps
- Node.js quickstart currently lacks automated tests; add once an MCP-compatible test harness is available.
- DeepSeek bridge script only has unit-level coverage; add integration tests after staging credentials are provisioned.
- IDE configs validated via JSON checks; consider end-to-end smoke tests using headless environments or recorded sessions when supported by platforms.

Future integrations should add tests under `tests/` to keep parity (e.g., Grok documentation helpers, DeepSeek bridge scripting).

## Running Tests
Install dev dependencies and run pytest:
```bash
uv pip install -r functions/requirements.txt  # existing dependencies (optional for tests)
pip install -e .[dev]
pytest
```

CI pipelines should run `pytest` on every pull request. For MCP Pulse submissions, include the test command and ensure mocks keep the suite hermetic.

## Adding New Tests
1. Place tests in `tests/` using descriptive filenames.
2. Mock external HTTP requests (e.g., `respx`) instead of hitting upstream services.
3. Provide fixtures for environment variables or sample configs as shown in `tests/conftest.py`.
4. Update this guide when introducing new tooling or coverage areas.

## Ownership & Next Steps
- **Owners:** Platform integration maintainers own proxy/bundle test updates; SDK authors own helper coverage.
- **Upcoming Work:** Once staging MCP endpoints are exposed, add opt-in E2E tests for the bridge script and quickstart clients.
- **CI Integration:** Ensure GitHub Actions (or equivalent) runs `pytest` on every pull request and records artifacts for MCP Pulse submissions.
