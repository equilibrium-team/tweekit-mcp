# Automated Testing Strategy

This repository ships with a pytest-based test suite to validate MCP integrations without calling external services. Contributors should run the tests before submitting changes and add coverage for new connectors or tooling.

## Test Coverage
- **ChatGPT proxy (`plugin_proxy.py`)** – Uses mocked HTTP responses to validate `/version`, `/doctype`, `/convert`, and the manifest route.
- **Claude bundle tooling** – Ensures the bundler embeds metadata, rewrites the endpoint, and packages supporting docs.
- **IDE configs** – Verifies Cursor/Continue JSON files contain the expected schema and secrets placeholders.
- **Python helper client** – Exercises the `TweekitClient` wrapper with a fake MCP client to confirm payload construction and credential handling.

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
