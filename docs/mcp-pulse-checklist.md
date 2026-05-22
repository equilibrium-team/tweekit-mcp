# MCP Directory Submission Checklist

Use this checklist when preparing TweekIT MCP for submission to registries and community directories. The landscape has expanded significantly — prioritize the Official MCP Registry first, as it auto-propagates to PulseMCP, VS Code/Copilot, and Glama.

See `docs/mcp-directories.md` for full detail on each directory including submission URLs, requirements, and formats.

---

## Pre-flight Requirements (Blocks All Submissions)

These items must be completed before any directory submission:

- [ ] **Tool annotations**: Add `readOnlyHint`/`destructiveHint` to all tools in `server.py` (required by Anthropic and OpenAI reviewers; also improves quality scores on Glama/PulseMCP).
- [ ] **Privacy policy**: Published at a public HTTPS URL.
- [x] **Live MCP endpoint**: `https://mcp.tweekit.io/mcp` with healthy `/mcp` transport.
- [x] **PyPI package**: `tweekit-mcp` published on PyPI.
- [x] **Public documentation**: Integration guides, security notes, quickstarts.
- [x] **Versioned changelog**: MCP releases tracked with bundle + proxy updates.

---

## Tier 1: Official & High-Leverage Registries

### Official MCP Registry (`registry.modelcontextprotocol.io`)

The canonical registry. Publishing here auto-propagates to PulseMCP (~1 week) and powers VS Code one-click installs. Do this first.

- [ ] Install `mcp-publisher` CLI.
- [ ] Run `mcp-publisher init` → create `server.json`.
- [ ] Add PyPI ownership proof: annotate `tweekit-mcp` README with `mcp-name: io.github.equilibrium-team/tweekit-mcp`.
- [ ] Authenticate via GitHub OAuth (`io.github.equilibrium-team` namespace).
- [ ] Run `mcp-publisher publish`.
- [ ] Confirm listing at `registry.modelcontextprotocol.io`.

### GitHub MCP Registry (VS Code one-click install panel)

Partner-curated subset of the official registry. Requires email after official registry listing.

- [ ] Complete Official MCP Registry (above) first.
- [ ] Email `partnerships@github.com` requesting GitHub-curated inclusion.

### Anthropic Connectors Directory (`claude.com/connectors`)

Two-track submission (remote + local bundle). See `docs/claude-submission-checklist.md` for full checklist.

- [ ] Add tool annotations (pre-flight above).
- [ ] Complete remote track submission.
- [ ] Complete local MCPB bundle submission.

### OpenAI ChatGPT Apps Directory (`developers.openai.com/apps-sdk`)

Remote-hosted only (no local format). See `INTEGRATION_ROADMAP.md` Section 1 for full checklist.

- [ ] Add tool annotations (pre-flight above).
- [ ] Define Content Security Policy.
- [ ] Deploy plugin proxy to production.
- [ ] Submit via OpenAI Developer Dashboard.

---

## Tier 2: High-Volume Aggregators

### PulseMCP (`pulsemcp.com/submit`) — 10,400+ servers

- [ ] Submit GitHub repo URL at pulsemcp.com/submit.
- [ ] (Auto-propagates from Official MCP Registry after ~1 week.)

### Glama (`glama.ai/mcp/servers`) — 19,000+ servers

- [ ] Add `glama.json` to repo root with maintainer info.
- [ ] Go through "Claim ownership" flow at glama.ai.
- [ ] Review quality grade; address any flagged issues.

### mcp.so (`mcp.so`) — 18,400+ servers

- [ ] Create GitHub issue in `chatmcp/mcp-directory` (submission thread is Issue #1).

### Smithery (`smithery.ai`) — 2,880+ servers, hosted deployments

- [ ] Add `smithery.yaml` to repo root.
- [ ] Verify `Dockerfile` exposes server on `$PORT`.
- [ ] Submit via `smithery mcp publish` CLI or `smithery.ai/new`.

---

## Tier 3: Specialized Directories

### Docker MCP Catalog (`hub.docker.com/mcp`) — containerized servers

- [ ] Add `LABEL io.modelcontextprotocol.server.name="..."` to `Dockerfile`.
- [ ] Push image to Docker Hub: `equilibriumteam/tweekit-mcp`.
- [ ] Submit PR to `docker/mcp-registry`.

### ToolHive Registry (`toolhive.dev`) — security-focused, Docker-first

- [ ] Fork `stacklok/toolhive-registry`.
- [ ] Add `registry/tweekit-mcp.json`.
- [ ] Submit PR.

### MCPBundles.com (`mcpbundles.com`) — `.mcpb` bundles

- [ ] Complete local MCPB bundle (see Claude submission checklist).
- [ ] Submit via "Request Integration" on mcpbundles.com.

### Cline MCP Marketplace (`github.com/cline/mcp-marketplace`)

- [ ] Submit GitHub issue with logo, repo URL, and description.
- [ ] Ensure `README.md` supports autonomous AI-agent install.
- [ ] Optionally add `llms-install.md` for complex setup steps.

---

## Tier 4: Lightweight Submissions (One Sprint)

Complete all of these in a single session — each requires only a URL or short form.

- [ ] MCPServe.com: web form at mcpserve.com/submit.
- [ ] Skills Playground: submit at skillsplayground.com/submit.
- [ ] Cursor Directory MCP: submit at cursor.directory/mcp.
- [ ] OpenTools Registry: submit at opentools.com/registry.
- [ ] awesome-mcp-servers: PR per CONTRIBUTING.md.
- [ ] modelcontextprotocol/servers: PR for official reference list.

---

## Automated Testing Evidence

Required for Anthropic and OpenAI submission packets; recommended for quality grades on Glama/PulseMCP.

- [x] `pytest` suite covering proxy, bundle packaging, config files, and MCP tools (`tests/`).
- [x] CI pipeline executes `pip install -e .[dev] && pytest`.
- [ ] Staging E2E tests passing (staged in `scripts/run_mcp_e2e.py`; run manually before submission).
- [ ] Full E2E test script (`scripts/run_full_e2e_test.py`) validated against production.

---

## Operational Requirements

- [x] Secrets management strategy for API keys/secrets.
- [x] Monitoring/alerting for hosted MCP endpoint.
- [x] Rollback plan for proxy/bundle deployments.
- [x] Hosting uptime SLA communicated in docs.

---

## Submission Packet Assets (per platform)

| Asset | Anthropic Remote | Anthropic Local | OpenAI | Official Registry |
|---|---|---|---|---|
| Live endpoint URL | ✅ required | n/a | ✅ required | ✅ required |
| `.mcpb` bundle | n/a | ✅ required | n/a | optional |
| Tool annotations | ✅ required | ✅ required | ✅ required | recommended |
| Privacy policy URL | ✅ required | ✅ required | ✅ required | recommended |
| Screenshots | ✅ required | ✅ required | ✅ required | n/a |
| `server.json` | n/a | n/a | n/a | ✅ required |
| `glama.json` | n/a | n/a | n/a | Glama only |
| Docker image | n/a | n/a | n/a | optional |

---

## Changelog

- **2026-03-13**: Major revision. Reset to actual completion state. Added Official MCP Registry, GitHub Registry, OpenAI Apps SDK, Smithery, Docker Catalog, ToolHive, MCPBundles.com, Cline Marketplace, and Tier 4 lightweight submissions. Added pre-flight requirements for tool annotations and privacy policy. Reflects research into current directory landscape as of Q1 2026.
