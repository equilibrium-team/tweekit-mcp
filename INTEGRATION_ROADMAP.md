# MCP Platform Integration Roadmap

This roadmap breaks down the remaining work to package the TweekIT MCP server for the major AI platforms called out by the team. Each section lists the deliverables we need, immediate next actions, and open questions that should be resolved before implementation.

---

## 1. OpenAI / ChatGPT (Apps SDK + MCP)

OpenAI adopted MCP natively in March 2025 via its Agents SDK and Responses API. The submission path is now the **OpenAI Apps SDK** — a broader framework that wraps an MCP server with optional UI elements, content security policies, and tool hint annotations. The old-style ChatGPT Plugin format is deprecated; the Apps SDK is the current target.

- **Deliverables**
  - Host `/.well-known/ai-plugin.json` + OpenAPI schema on production domain.
  - Provide REST-facing proxy that maps plugin calls to MCP `tools/list` and `tools/call`.
  - Add `readOnlyHint`/`destructiveHint` annotations to all tool definitions in `server.py` (required by reviewer — missing = rejection).
  - Define a Content Security Policy (CSP) listing all external domains the server fetches from (tweekit.io, DuckDuckGo, etc.).
  - Capture screenshots and test prompts with expected responses for the submission packet.
  - Submit via [OpenAI Apps SDK Developer Dashboard](https://developers.openai.com/apps-sdk/deploy/submission/).

- **Task Checklist**
  - [ ] Add `readOnlyHint`/`destructiveHint` tool annotations to `server.py` for all tools (`doctype`, `convert`, `convert_url`, `search`, `fetch`).
  - [ ] Define Content Security Policy (CSP) covering `tweekit.io`, `dapp.tweekit.io`, `duckduckgo.com`.
  - [ ] Deploy `plugin_proxy.py` to Cloud Run (stage + prod) with `TWEEKIT_API_KEY`, `TWEEKIT_API_SECRET`, `PLUGIN_PUBLIC_BASE_URL` env vars.
  - [ ] Map staging/production domains (`staging.mcp.tweekit.io`, `mcp.tweekit.io`) via Cloud Run domain mappings; update DNS/TLS and confirm public URLs.
  - [ ] Verify `/.well-known/ai-plugin.json`, `/openapi.json`, `/version`, `/doctype`, `/convert` return HTTP 200 on stage.
  - [ ] Import the Action in ChatGPT Developer mode (Settings → Developer → Actions → Add Action → Import from URL); capture Preview screenshots.
  - [ ] Run live smoke tests (`uv run python -m pytest tests/test_chatgpt_proxy_live.py`) against stage and prod.
  - [ ] Compile submission packet (logs, screenshots, version info, test prompts, CSP, privacy policy URL) and submit via OpenAI Developer Dashboard.

- **Next Actions**
  1. Add tool hint annotations to `server.py` — unblocks both OpenAI and Anthropic submissions simultaneously.
  2. Deploy the plugin proxy to staging Cloud Run; smoke-test all endpoints.
  3. Finalize the production domain mapping and TLS certificate.

- **Open Questions**
  - Which domain/subdomain will host the manifest? Need DNS + certificate plan.
  - Confirm authentication story (Bearer token forwarded as `ApiKey` vs OAuth proxy).
  - Should the proxy implement OAuth 2.0 for OpenAI's "Sign in with…" flow, or keep Bearer-only?

---

## 2. Anthropic Claude (Connectors Directory + MCPB Bundle)

Anthropic's Connectors Directory has two submission tracks. TweekIT qualifies for both: a **remote MCP server** track (hosted endpoint, OAuth, Streamable HTTP) and a **local/.mcpb bundle** track (packaged stdio server). The toolchain has been updated — the CLI is now `@anthropic-ai/mcpb` and manifests require `manifest_version: "0.3"` or higher. The older `dxt` CLI and `.dxt` extension still work but are deprecated.

### 2a. Remote MCP Server (claude.com/connectors Track 1)

- **Deliverables**
  - Production Streamable HTTP endpoint: `https://mcp.tweekit.io/mcp` — must be GA (not beta).
  - OAuth 2.0 implementation (authorization code flow) OR confirm acceptable fallback if anonymous/key-based auth is permitted.
  - Tool annotations (`readOnlyHint`/`destructiveHint`) on ALL tools — their absence is listed as a top rejection reason.
  - Privacy policy at a publicly accessible HTTPS URL.
  - Minimum 3 documented usage examples.
  - Dedicated support channel.
  - Submit via [Anthropic Remote MCP Submission Form](https://docs.google.com/forms/d/e/1FAIpQLSeafJF2NDI7oYx1r8o0ycivCSVLNq92Mpc1FPxMKSw1CzDkqA/viewform).

- **Task Checklist (Remote Track)**
  - [ ] Add `readOnlyHint`/`destructiveHint` annotations to all tools in `server.py`.
  - [ ] Verify production endpoint uses Streamable HTTP transport (NOT SSE-only).
  - [ ] Configure OAuth 2.0 callback to whitelist `http://localhost:6274/oauth/callback` and `https://claude.ai/api/mcp/auth_callback` — OR confirm key-based auth path with Anthropic.
  - [ ] Publish privacy policy at a public HTTPS URL; add link to README and `claude/manifest.json`.
  - [ ] Ensure tool results stay under 25,000 tokens and responses return within 300 seconds.
  - [ ] Prepare 3+ documented usage examples with expected Claude responses.
  - [ ] Capture live screenshots of `doctype`/`convert_url` calls in Claude.
  - [ ] Submit via Remote MCP form; track response.

### 2b. Local MCPB Bundle (claude.com/connectors Track 2)

- **Deliverables**
  - ✅ Ship self-contained `.mcpb` bundle with stdio server + vendored deps (`scripts/build_claude_bundle.py`).
  - ✅ Publish manifest metadata (`claude/manifest.json`).
  - 🔄 Update manifest to `manifest_version: "0.3"` or higher and rebuild with `@anthropic-ai/mcpb` CLI.
  - 🔄 Add privacy policy to both `claude/manifest.json` (`privacy_policies` array) and `claude/README.md`.
  - 🔄 Assemble and submit Anthropic submission packet (`docs/claude-submission-checklist.md`).

- **Task Checklist (Local MCPB Track)**
  - [ ] Install `@anthropic-ai/mcpb` CLI: `npm install -g @anthropic-ai/mcpb`.
  - [ ] Update `claude/manifest.json` to `manifest_version: "0.3"` (or latest) and add `privacy_policies` array.
  - [ ] Rebuild bundle: `mcpb pack` (replaces `dxt pack`); output `dist/tweekit-claude.mcpb`.
  - [ ] Validate: `mcpb validate dist/tweekit-claude.mcpb`.
  - [ ] Test install on macOS (double-click `.mcpb` or Claude Desktop → Install Extension…) + capture screenshot.
  - [ ] Test install on Windows — capture screenshot.
  - [ ] Capture `~/Library/Logs/Claude/main.log` (macOS) or `%AppData%/Claude/logs/main.log` snippet.
  - [ ] Update CI workflow (`.github/workflows/build-claude-bundle.yml`) to use `mcpb pack` instead of `dxt pack`.
  - [ ] Aggregate submission packet per `docs/claude-submission-checklist.md`.
  - [ ] Submit via [Anthropic Local MCP Submission Form](https://forms.gle/tyiAZvch1kDADKoP9).

- **Open Questions**
  - Does our production server already return correct CORS headers for `claude.ai`? Verify before remote submission.
  - Do we want nightly CI builds for internal QA, or only tagged releases?
  - Any additional runtime targets (Linux) needed for the local bundle?

---

## 3. Developer Tooling (Cursor, Continue, Codex CLI, Others)

- **Deliverables**
  - `Add to Cursor` link + JSON snippet for `.cursor/mcp.json`. ✅ (config in `configs/cursor-mcp.json`)
  - Continue Hub submission or shareable block. ✅ (config in `configs/continue-mcp.json`)
  - ✅ OpenAI Codex CLI config + easy plugin one-liner (`configs/codex-mcp.yaml`; README quickstart added).
  - Coverage of other popular IDE agents (Windsurf, v0, Sourcegraph Cody where applicable).

- **Codex CLI Details**
  - Config file: `configs/codex-mcp.yaml` → merges into `~/.codex/config.yaml`.
  - Easy plugin one-liner (no config file required): `codex --mcp-server tweekit:https://mcp.tweekit.io/mcp`
  - Install: `npm install -g @openai/codex`
  - README quickstart section: [Quickstart (OpenAI Codex CLI)](#quickstart-openai-codex-cli)

- **Task Checklist**
  - [x] Create `configs/codex-mcp.yaml` for OpenAI Codex CLI.
  - [x] Add Codex CLI quickstart to README (Option A: `--mcp-server` easy plugin; Option B: persistent config).
  - [x] Add Codex CLI section to `docs/developer-tools.md`.
  - [x] Update Client Compatibility table in README to include Codex CLI.
  - [ ] Submit to [Cline MCP Marketplace](https://github.com/cline/mcp-marketplace) via GitHub issue — include logo, GitHub URL, and 3-sentence description of TweekIT value.
  - [ ] Submit to [Skills Playground](https://skillsplayground.com/submit) (8,600+ skills for Claude Code, Cursor, Copilot, Windsurf, Cline).
  - [ ] Create `llms-install.md` (AI-agent-friendly install instructions) to support Cline autonomous setup.
  - [ ] Build landing page section or documentation panel with one-click install buttons.
  - [ ] Coordinate with developer-relations to publish in relevant extension marketplaces.

- **Open Questions**
  - Which IDE platforms show strongest demand? Prioritize accordingly.
  - Codex CLI `--mcp-server` flag syntax — confirm current flag name against latest `@openai/codex` release notes before publishing.

---

## 4. SDK Snippets & Quickstarts

- **Deliverables**
  - Python + Node.js examples demonstrating connection + `convert` usage.
  - Optional lightweight `tweekit-mcp-client` wrappers (PyPI/NPM).
  - Planned TypeScript Cloud Run/serverless package delivering the proxy as a container-ready runtime.
  - Documentation updates linking to quickstarts and SDKs.

- **Next Actions**
  1. Use official MCP SDKs to craft runnable scripts (include env var setup + sample file).
  2. Publish packages (if built) with semantic versioning and CI release pipeline.
  3. Start TypeScript implementation targeting Cloud Run (baseline container deploy).
  4. Update README + AGENTS guide with quickstart links.

---

## 5. MCP Directory Submissions

This section covers all the active registries and directories where TweekIT should be listed. See `docs/mcp-directories.md` for full detail on each directory, requirements, and submission links.

### 5a. Official MCP Registry (`registry.modelcontextprotocol.io`) — PRIORITY

The canonical registry maintained by Anthropic, PulseMCP, GitHub, and Microsoft. PulseMCP ingests it daily; VS Code/Copilot uses it for one-click installs. **Submit here first — it auto-propagates to several other directories.**

- **Task Checklist**
  - [ ] Install `mcp-publisher` CLI (via Homebrew or binary from [mcp-publisher releases](https://github.com/modelcontextprotocol/registry)).
  - [ ] Run `mcp-publisher init` to generate `server.json` template.
  - [ ] Authenticate via GitHub OAuth (for `io.github.equilibrium-team/tweekit-mcp` namespace) OR set up DNS verification for `com.tweekit` namespace.
  - [ ] Add PyPI ownership proof: annotate `tweekit-mcp` README with `mcp-name: io.github.equilibrium-team/tweekit-mcp` (or reverse-DNS ID).
  - [ ] Verify `server.json` schema and run `mcp-publisher publish`.
  - [ ] Confirm listing appears at `registry.modelcontextprotocol.io` within 24h.

### 5b. GitHub MCP Registry (VS Code one-click installs)

GitHub's curated subset of the official registry. Requires a partner request after publishing to the official registry.

- **Task Checklist**
  - [ ] Complete 5a (official registry) first.
  - [ ] Email `partnerships@github.com` requesting inclusion in the GitHub-curated MCP registry.

### 5c. Smithery (`smithery.ai`)

2,880+ servers; supports hosted (Docker) and pass-through (local) modes. For hosted: add `smithery.yaml` and `Dockerfile`.

- **Task Checklist**
  - [ ] Add `smithery.yaml` config to repo root (runtime: container, Streamable HTTP on `$PORT`).
  - [ ] Verify `Dockerfile` runs `uvicorn server:app --host 0.0.0.0 --port $PORT` correctly.
  - [ ] Run `smithery mcp publish <repo-url> -n equilibrium-team/tweekit-mcp` OR submit via `smithery.ai/new`.

### 5d. PulseMCP (`pulsemcp.com`)

10,400+ servers; auto-ingests the official MCP registry weekly. Also accepts direct URL submissions.

- **Task Checklist**
  - [ ] Submit GitHub repo URL at [pulsemcp.com/submit](https://www.pulsemcp.com/submit).
  - [ ] (Bonus) Publishing to Official MCP Registry (5a) causes auto-ingestion within ~1 week.

### 5e. Glama (`glama.ai/mcp/servers`)

19,000+ servers; assigns quality grades. Supports ownership claiming via `glama.json`.

- **Task Checklist**
  - [ ] Add `glama.json` to repo root (see `docs/mcp-directories.md` for schema).
  - [ ] Go through the "Claim ownership" flow at glama.ai after the file is merged.
  - [ ] Review quality grade and address any flagged issues.

### 5f. mcp.so (`mcp.so`)

18,400+ servers; community-driven aggregator. Submit via GitHub issue.

- **Task Checklist**
  - [ ] Create a GitHub issue in `chatmcp/mcp-directory` (see Issue #1 for the submission thread) with server name, description, features, and connection info.

### 5g. Docker MCP Catalog (`hub.docker.com/mcp`)

300+ verified, containerized servers available in Docker Desktop's MCP Toolkit.

- **Task Checklist**
  - [ ] Add `LABEL io.modelcontextprotocol.server.name="io.github.equilibrium-team/tweekit-mcp"` to `Dockerfile`.
  - [ ] Build and push Docker image to Docker Hub or GHCR: `docker push equilibriumteam/tweekit-mcp:latest`.
  - [ ] Submit PR to [docker/mcp-registry](https://github.com/docker/mcp-registry) per contributing guidelines.

### 5h. ToolHive Registry (`toolhive.dev`)

Security-focused MCP server management; Docker-first. Used by security-conscious enterprise teams.

- **Task Checklist**
  - [ ] Fork `stacklok/toolhive-registry`.
  - [ ] Add `registry/tweekit-mcp.json` following the ToolHive `ServerJSON` schema with `_meta` extensions.
  - [ ] Confirm Docker image is publicly accessible on Docker Hub or GHCR.
  - [ ] Submit PR.

### 5i. MCPBundles.com (`mcpbundles.com`)

Dedicated directory for `.mcpb` bundles (670+ entries). Submit after completing the local MCPB track (section 2b).

- **Task Checklist**
  - [ ] Complete local MCPB bundle (section 2b).
  - [ ] Click "Request Integration" on mcpbundles.com to submit the bundle.

### 5j. Lightweight Directory Submissions (lower effort, high reach)

These accept a GitHub repo URL or short web form; complete all in a single sprint.

- **Task Checklist**
  - [ ] [mcp.so](https://mcp.so) — GitHub issue in `chatmcp/mcp-directory`.
  - [ ] [MCPServe.com](https://mcpserve.com/submit) — Web form: name, description, category, logo.
  - [ ] [Skills Playground](https://skillsplayground.com/submit) — Submit URL.
  - [ ] [Cursor Directory MCP](https://cursor.directory/mcp) — Submit listing (Cursor-focused).
  - [ ] [OpenTools Registry](https://opentools.com/registry) — Submit for curated inclusion.
  - [ ] [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) — PR per CONTRIBUTING.md.
  - [ ] [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — PR for reference list.

---

## 6. Pre-Packaged Distribution Formats

Many directories and AI clients now require or strongly prefer pre-packaged distribution artifacts. This section tracks what we need to produce beyond the standard pip/repo install.

### 6a. Docker Image (unblocks Docker Catalog, ToolHive, Smithery hosted, Official Registry)

- **Task Checklist**
  - [ ] Add MCP server namespace `LABEL` to `Dockerfile` (`io.modelcontextprotocol.server.name`).
  - [ ] Confirm image starts correctly with just `PORT` set; listens on `0.0.0.0:$PORT`.
  - [ ] Publish to Docker Hub as `equilibriumteam/tweekit-mcp:<version>` (or GHCR).
  - [ ] Add Docker Hub push step to CI release workflow.
  - [ ] Add `smithery.yaml` and test hosted deployment on Smithery.

### 6b. MCPB Bundle (unblocks Anthropic local track, MCPBundles.com, Official Registry MCPB format)

- **Task Checklist**
  - [ ] Migrate build tooling from `dxt` → `@anthropic-ai/mcpb` CLI.
  - [ ] Update `manifest.json` to `manifest_version: "0.3"`, add `privacy_policies`, add tool annotations.
  - [ ] Update CI workflow output to produce `dist/tweekit-claude.mcpb`.
  - [ ] Host `.mcpb` artifact on GitHub Releases with SHA-256 hash for Official Registry listing.

### 6c. PyPI Package (already published — add MCP namespace annotation)

- **Task Checklist**
  - [x] `tweekit-mcp` published on PyPI.
  - [ ] Add `mcp-name: io.github.equilibrium-team/tweekit-mcp` annotation to PyPI README (`pyproject.toml` long description or `README.md`) for Official MCP Registry ownership proof.

### 6d. Claude Code Plugin Format

Claude Code supports a plugin format that bundles MCP config, slash commands, agent definitions, and skills. This enables listing in the Claude Code Plugins Directory (`claude.com/plugins`).

- **Task Checklist**
  - [ ] Research Claude Code plugin spec (`github.com/anthropics/claude-plugins-official`).
  - [ ] Create `.claude-plugin/plugin.json` with display name, description, category.
  - [ ] Bundle existing MCP config (`.mcp.json`) as part of the plugin.
  - [ ] Add relevant slash commands or agent definitions if applicable.
  - [ ] Submit via [Claude Plugins submission form](https://clau.de/plugin-directory-submission).

---

## 7. Web Converter (AI File Format Enabler)

- **Deliverables**
  - ✅ Browser-based file converter addressing AI tool file type limitations (`examples/web-converter/index.html`).
  - ✅ Dedicated documentation (`examples/web-converter/README.md`).
  - ✅ Integration into main documentation.
  - 🔄 Optional hosting on tweekit.io for public access (currently runs locally).

- **Task Checklist**
  - [x] Build standalone HTML converter with TweekIT API integration.
  - [x] Rebrand tool to focus on all AI tools (Claude, OpenAI, Gemini, etc.).
  - [x] Add API credential management (localStorage-based, collapsible).
  - [x] Integrate TweekIT logo in header.
  - [x] Add feature request/bug reporting section.
  - [x] Create comprehensive README for the web converter.
  - [x] Update main README with "Solving Claude's File Type Limitations" section.
  - [x] Add web converter to quickstarts documentation.
  - [ ] Host publicly on tweekit.io/converter or similar URL.
  - [ ] Add analytics/usage tracking (optional).
  - [ ] Create video demo showing AI tool use cases.

---

## Cross-Cutting Requirements

- **Tool annotations**: Add `readOnlyHint`/`destructiveHint` to all tools in `server.py` — required by both Anthropic and OpenAI reviewers.
- **Privacy policy**: Publish at a public HTTPS URL; add to `claude/manifest.json` and main README.
- **Staging environment**: Required for E2E test evidence needed by Anthropic/OpenAI submission packets.
- **Docker image**: Unlocks 5+ directories simultaneously — high-leverage action.
- **server.json**: Create for Official MCP Registry; triggers auto-propagation to PulseMCP, VS Code, and Glama.
- Maintain MCP spec compliance: versioning strategy, test suite updates, backward-compat checks.
- Keep hosted environments on Google Cloud Run with downstream processing in ISO/SaaS 70 compliant data centers.
- Add CI checks for manifest schema validation, bundle integrity, SDK linting, and `pytest` automation.

## Current Open Tasks

- Add tool annotations (`readOnlyHint`/`destructiveHint`) to `server.py` — unblocks Anthropic + OpenAI submissions.
- Migrate MCPB build from `dxt` → `@anthropic-ai/mcpb` CLI and update `manifest.json` to v0.3.
- Build + publish Docker image — unblocks Docker Catalog, ToolHive, Smithery hosted, Official Registry.
- Create `server.json` and publish to Official MCP Registry — triggers auto-propagation.
- Review `docs/backlog.md` for issue-ready items covering all new directory and pre-packaged targets.

> **Next Step:** Prioritize: (1) tool annotations in server.py, (2) Docker image + smithery.yaml, (3) Official MCP Registry server.json, (4) MCPB v0.3 bundle + Anthropic submission. These four actions unlock the majority of downstream directory listings.

---

## Future Possible Integrations

### xAI Grok Enablement
- **Deliverables**
  - Documentation for installing via current Grok tooling (browser extension, MCP SuperAssistant, etc.).
  - Roadmap proposal for native Grok support once official API is published.
- **Exploratory Actions**
  1. Investigate Grok's latest plugin/tool API surface; capture limitations.
  2. Produce interim instructions leveraging cross-platform extensions (e.g., SuperAssistant).
  3. Track xAI announcements for first-party integration.

### DeepSeek Integration
- **Deliverables**
  - Quickstart doc for DeepSeek users (CLI script or connector config).
  - Optional helper script that bridges DeepSeek API responses to MCP tool calls.
- **Exploratory Actions**
  1. Audit DeepSeek clients for MCP compatibility; capture supported auth flow.
  2. Implement bridging agent (Python) if no native MCP interface exists.
  3. Write deployment guide (Docker + README) for hosting the bridge.
