# MCP Platform Integration Roadmap

This roadmap breaks down the remaining work to package the TweekIT MCP server for the major AI platforms called out by the team. Each section lists the deliverables we need, immediate next actions, and open questions that should be resolved before implementation.

## 1. OpenAI / ChatGPT Plugin
- **Deliverables**
  - Host `.well-known/ai-plugin.json` + OpenAPI schema on `tweekit.com`.
  - Provide REST-facing proxy that maps plugin calls to MCP `tools/list` and `tools/call`.
  - Submit manual install instructions + Plugin Store listing request.
- **Task Checklist**
  - [ ] Deploy `plugin_proxy.py` to Cloud Run (stage + prod) with `TWEEKIT_API_KEY`, `TWEEKIT_API_SECRET`, `PLUGIN_PUBLIC_BASE_URL` env vars and verify `/version`, `/doctype`, `/convert`, and `/.well-known/ai-plugin.json`.
  - [ ] Map staging/production domains (e.g., `staging.mcp.tweekit.io`, `plugin.tweekit.io`) via Cloud Run domain mappings; update DNS/TLS and confirm public URLs.
  - [ ] Run live smoke tests (`uv run python -m pytest tests/test_chatgpt_proxy_live.py`, curl commands from the docs) against stage and prod.
  - [ ] Import the Action in ChatGPT Developer mode and capture Preview screenshots demonstrating `doctype`/`convert` responses.
  - [ ] Compile MCP Pulse / release evidence (logs, screenshots, version info) and attach to the release notes or submission packet.
- **Next Actions**
  1. Draft OpenAPI spec mirroring `version`, `doctype`, and `convert` semantics (owner: Backend).
  2. Implement lightweight proxy (FastAPI or Cloud Functions) that authenticates with TweekIT and forwards requests to the MCP server.
  3. Publish plugin manifest + spec, verify CORS/HTTPS headers, and document self-install workflow with screenshots.
- **Open Questions**
  - Which domain/subdomain will host the manifest? Need DNS + certificate plan.
  - Confirm authentication story (API key headers vs OAuth proxy).

## 2. Anthropic Claude Desktop (.mcpb Bundle)
- **Deliverables**
  - ✅ Ship self-contained `.mcpb` bundle with stdio server + vendored deps (`scripts/build_claude_bundle.py`).
  - ✅ Publish manifest metadata (`claude/manifest.json`) with optional credential fallback.
  - 🔄 Package documentation + onboarding helper (`docs/claude-bundle.md`, `scripts/configure_claude_desktop.py`).
- **Next Actions**
  1. ✅ Automate bundle build + `dxt` validation in CI (see `.github/workflows/ci-claude-bundle`).
  2. Capture fresh macOS + Windows install screenshots using the guided script.
  3. Assemble Anthropic submission packet (manifest, screenshots, logs, changelog) — track via `docs/claude-submission-checklist.md`.
  4. Evaluate bundle signing once Anthropic releases guidance.
- **Open Questions**
  - Any additional runtime targets (Linux) needed? Add `platform_overrides` if required.
  - Do we want nightly builds for internal QA, or only tagged releases?

## 3. Developer Tooling (Cursor, Continue, Others)
- **Deliverables**
  - `Add to Cursor` link + JSON snippet for `.cursor/mcp.json`.
  - Continue Hub submission or shareable block with TweekIT connection info.
  - Coverage of other popular IDE agents (Windsurf, v0, Sourcegraph Cody where applicable).
- **Next Actions**
  1. Draft configuration snippets for Cursor, Continue, and any additional IDE assistants.
  2. Build landing page section or documentation panel with one-click install buttons.
  3. Coordinate with developer-relations to publish in relevant extension marketplaces.
- **Open Questions**
  - Which IDE platforms show strongest demand? Prioritize accordingly.

## 4. SDK Snippets & Quickstarts
- **Deliverables**
  - Python + Node.js examples demonstrating connection + `convert` usage.
  - Optional lightweight `tweekit-mcp-client` wrappers (PyPI/NPM).
  - Planned TypeScript Cloud Run/serverless package (`tweekit-mcp`) delivering the proxy as a container-ready runtime.
  - Documentation updates linking to quickstarts and SDKs.
- **Next Actions**
  1. Use official MCP SDKs to craft runnable scripts (include env var setup + sample file).
  2. Publish packages (if built) with semantic versioning and CI release pipeline.
  3. Start TypeScript implementation targeting Cloud Run (baseline container deploy), with a follow-on serverless template once stable.
  4. Update README + AGENTS guide with quickstart links; add Postman/HTTP examples for OpenAPI spec.
- **Open Questions**
  - Do we bundle sample assets for conversion demos? Need decision on licensing/sample content.

## 7. Web Converter (AI File Format Enabler)
- **Deliverables**
  - ✅ Browser-based file converter addressing AI tool file type limitations for Claude, OpenAI, and other platforms (`examples/web-converter/index.html`).
  - ✅ Dedicated documentation explaining the AI file ingest problem and solution (`examples/web-converter/README.md`).
  - ✅ Integration into main documentation with AI-specific use cases and workflows.
  - ✅ Collapsible API credentials section with saved state management.
  - ✅ TweekIT branding with logo integration.
  - ✅ Feature request/bug reporting contact section.
  - ✅ Focus on legacy file formats (DOC, XLS, PPT) that AI tools consistently reject.
  - 🔄 Optional hosting on tweekit.io for public access (currently runs locally).
- **Task Checklist**
  - [x] Build standalone HTML converter with TweekIT API integration.
  - [x] Rebrand tool to focus on all AI tools (Claude, OpenAI, Gemini, etc.).
  - [x] Add API credential management (localStorage-based, collapsible).
  - [x] Integrate TweekIT logo in header.
  - [x] Add feature request/bug reporting section.
  - [x] Update messaging to focus on legacy binary formats (DOC, XLS, PPT vs DOCX, XLSX, PPTX).
  - [x] Create comprehensive README for the web converter.
  - [x] Update main README with "Solving Claude's File Type Limitations" section.
  - [x] Add web converter to quickstarts documentation.
  - [x] Update INTEGRATION_ROADMAP with web converter deliverable.
  - [ ] Host publicly on tweekit.io/converter or similar URL.
  - [ ] Add analytics/usage tracking (optional).
  - [ ] Create video demo showing AI tool use cases.
- **Next Actions**
  1. Consider hosting the converter publicly for easy access without local setup.
  2. Gather user feedback on the converter UX and conversion success rates.
  3. Add more output format options if Claude expands supported formats.
  4. Create marketing materials (video, screenshots) showing before/after workflows.
- **Open Questions**
  - Should we host this publicly on tweekit.com or keep it as a local tool?
  - Do we want to add batch conversion capabilities?
  - Should we track conversion metrics for product insights?

## Cross-Cutting Requirements
- Ensure MCP server remains API-compliant: document versioning strategy, test suite updates, and backward-compat checks.
- Establish staging environment for manifests/bundles before public release.
- Keep hosted environments on Google Cloud Run (containerized) with downstream processing in ISO/SaaS 70 compliant data centers; document purge guarantees for tier-1 TweekIT miners.
- Add CI checks for manifest schema validation, bundle integrity, SDK linting, and `pytest` automation (proxy, configs, helpers).
- Track MCP Pulse submission prerequisites via `docs/mcp-pulse-checklist.md`: automated test evidence, connector documentation, and distribution artifacts.

## Current Open Tasks
- Review `docs/backlog.md` for issue-ready items covering Grok native support, DeepSeek bridge hardening, IDE onboarding feedback, and SDK packaging.
- Prioritize staging environment setup to unlock E2E testing commitments and MCP Pulse submission.

> **Next Step:** Review the roadmap, assign owners/dates, and prioritize implementation order. Once confirmed, we can start opening tracked issues for each deliverable.

## Future Possible Integrations

### xAI Grok Enablement
- **Deliverables**
  - Documentation for installing via current Grok tooling (browser extension, MCP SuperAssistant, etc.).
  - Roadmap proposal for native Grok support once official API is published.
- **Exploratory Actions**
  1. Investigate Grok’s latest plugin/tool API surface; capture limitations.
  2. Produce interim instructions leveraging cross-platform extensions (e.g., SuperAssistant) if demand materializes.
  3. Track xAI announcements for first-party integration and prep manifest format if announced.
- **Open Questions**
  - Does Grok expose REST or MCP endpoints today? Need confirmation from xAI or community.

### DeepSeek Integration
- **Deliverables**
  - Quickstart doc for DeepSeek users (CLI script or connector config).
  - Optional helper script that bridges DeepSeek API responses to MCP tool calls.
- **Exploratory Actions**
  1. Audit DeepSeek clients for MCP compatibility; capture supported auth flow.
  2. Implement bridging agent (Python) if no native MCP interface exists.
  3. Write deployment guide (Docker + README) for hosting the bridge.
- **Open Questions**
  - What authentication will DeepSeek require for third-party tool calls? Need updated docs.
