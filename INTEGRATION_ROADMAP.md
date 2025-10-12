# MCP Platform Integration Roadmap

This roadmap breaks down the remaining work to package the TweekIT MCP server for the major AI platforms called out by the team. Each section lists the deliverables we need, immediate next actions, and open questions that should be resolved before implementation.

## 1. OpenAI / ChatGPT Plugin
- **Deliverables**
  - Host `.well-known/ai-plugin.json` + OpenAPI schema on `tweekit.com`.
  - Provide REST-facing proxy that maps plugin calls to MCP `tools/list` and `tools/call`.
  - Submit manual install instructions + Plugin Store listing request.
- **Next Actions**
  1. Draft OpenAPI spec mirroring `version`, `doctype`, and `convert` semantics (owner: Backend).
  2. Implement lightweight proxy (FastAPI or Cloud Functions) that authenticates with TweekIT and forwards requests to the MCP server.
  3. Publish plugin manifest + spec, verify CORS/HTTPS headers, and document self-install workflow with screenshots.
- **Open Questions**
  - Which domain/subdomain will host the manifest? Need DNS + certificate plan.
  - Confirm authentication story (API key headers vs OAuth proxy).

## 2. Anthropic Claude Desktop (.mcpb Bundle)
- **Deliverables**
  - Create `.mcpb` bundle with packaged Python runtime or config pointing to remote MCP server.
  - Provide metadata (`manifest.json`) describing the tools and required environment variables.
  - Submission packet for Anthropic’s extension directory.
- **Next Actions**
  1. Prototype bundle using Anthropic’s reference template; test install on macOS/Windows.
  2. Decide whether to embed server binaries or rely on remote HTTPS endpoint.
  3. Write install/uninstall guide and collect logs/screenshots for submission.
- **Open Questions**
  - Do we need offline conversion support (requires bundling TweekIT engine) or is remote-only acceptable?

## 3. xAI Grok Enablement
- **Deliverables**
  - Documentation for installing via current Grok tooling (browser extension, MCP SuperAssistant, etc.).
  - Roadmap proposal for native Grok support once official API is published.
- **Next Actions**
  1. Investigate Grok’s latest plugin/tool API surface; capture limitations.
  2. Produce interim instructions leveraging cross-platform extensions (e.g., SuperAssistant).
  3. Track xAI announcements for first-party integration and prep manifest format if announced.
- **Open Questions**
  - Does Grok expose REST or MCP endpoints today? Need confirmation from xAI or community.

## 4. DeepSeek Integration
- **Deliverables**
  - Quickstart doc for DeepSeek users (CLI script or connector config).
  - Optional helper script that bridges DeepSeek API responses to MCP tool calls.
- **Next Actions**
  1. Audit DeepSeek clients for MCP compatibility; capture supported auth flow.
  2. Implement bridging agent (Python) if no native MCP interface exists.
  3. Write deployment guide (Docker + README) for hosting the bridge.
- **Open Questions**
  - What authentication will DeepSeek require for third-party tool calls? Need updated docs.

## 5. Developer Tooling (Cursor, Continue, Others)
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

## 6. SDK Snippets & Quickstarts
- **Deliverables**
  - Python + Node.js examples demonstrating connection + `convert` usage.
  - Optional lightweight `tweekit-mcp-client` wrappers (PyPI/NPM).
  - Documentation updates linking to quickstarts and SDKs.
- **Next Actions**
  1. Use official MCP SDKs to craft runnable scripts (include env var setup + sample file).
  2. Publish packages (if built) with semantic versioning and CI release pipeline.
  3. Update README + AGENTS guide with quickstart links; add Postman/HTTP examples for OpenAPI spec.
- **Open Questions**
  - Do we bundle sample assets for conversion demos? Need decision on licensing/sample content.

## Cross-Cutting Requirements
- Ensure MCP server remains API-compliant: document versioning strategy, test suite updates, and backward-compat checks.
- Establish staging environment for manifests/bundles before public release.
- Add CI checks for manifest schema validation, bundle integrity, SDK linting, and `pytest` automation (proxy, configs, helpers).
- Track MCP Pulse submission prerequisites via `docs/mcp-pulse-checklist.md`: automated test evidence, connector documentation, and distribution artifacts.

## Current Open Tasks
- Review `docs/backlog.md` for issue-ready items covering Grok native support, DeepSeek bridge hardening, IDE onboarding feedback, and SDK packaging.
- Prioritize staging environment setup to unlock E2E testing commitments and MCP Pulse submission.

> **Next Step:** Review the roadmap, assign owners/dates, and prioritize implementation order. Once confirmed, we can start opening tracked issues for each deliverable.
