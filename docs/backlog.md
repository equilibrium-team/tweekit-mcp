# TweekIT MCP Backlog

Use this backlog to seed GitHub issues or project tasks. Each item includes a suggested summary, recommended assignee, dependencies, and testing expectations.

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Deploy ChatGPT proxy to staging + production | Backend + DevOps | Finalize domain + TLS certs | Smoke test `/version`, `/doctype`, `/convert` via `pytest` mocks + live curl; document in `docs/chatgpt-plugin.md` |
| Publish `.well-known/ai-plugin.json` + OpenAPI | Backend | ChatGPT proxy deployment | Validate plugin import in ChatGPT UI; attach screenshots for MCP Pulse packet |
| Finalize Claude `.mcpb` pipeline | SDK / DevOps | `scripts/build_claude_bundle.py` | Run build script in CI, upload artifact; manual install verified on macOS + Windows |
| Grok native integration research | Platform PM | xAI roadmap updates | Update `docs/grok-integration.md` with findings; create prototype manifest if spec released |
| DeepSeek bridge hardening | AI Integrations | Live staging MCP endpoint | Add retry/backoff + logging to `scripts/deepseek_mcp_bridge.py`; add staging E2E test when available |
| IDE onboarding feedback loop | DX / Developer Relations | Release configs publically | Collect Cursor/Continue user feedback; update `docs/developer-tools.md` and configs |
| Package Python helper for PyPI | SDK | Confirm API stability | Publish `tweekit-mcp-client` with semantic versioning; add packaging test in CI |
| Publish Node helper package | SDK | TypeScript helper maturity | Wrap quickstart into NPM module; add example tests |
| Add staging E2E pytest suite | QA / Platform | Staging endpoint + secrets management | Implement opt-in tests using env vars; update `docs/testing.md` coverage section |
| CI artifacts for MCP Pulse submission | DevOps | GitHub Actions updates | Workflow uploads bundle manifest, proxy swagger, and pytest report on release |
