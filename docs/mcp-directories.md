# MCP Server Directory Reference

A comprehensive reference of all active MCP server directories, registries, and marketplaces as of Q1 2026. Listed in priority order for TweekIT submissions.

---

## Tier 1 — Official & Highest-Leverage

### 1. Official MCP Registry
**URL:** https://registry.modelcontextprotocol.io
**GitHub:** https://github.com/modelcontextprotocol/registry
**Status:** Live (launched September 2025; v0.1 API frozen October 2025)

The canonical open-source registry maintained by Anthropic, PulseMCP, GitHub, and Microsoft. **Publishing here is the single highest-leverage action** — it triggers auto-ingestion into PulseMCP (~1 week), powers VS Code/Copilot one-click installs, and is the ownership proof required for several other registries.

**Submission:**
```bash
# Install CLI
brew install mcp-publisher
# Or download binary from https://github.com/modelcontextprotocol/registry/releases

mcp-publisher init        # generates server.json template
# Authenticate via GitHub OAuth for io.github.* namespace
mcp-publisher publish
```

**Namespace format:** Reverse-DNS — `io.github.equilibrium-team/tweekit-mcp`

**Supported pre-packaged formats:**
- npm: add `mcpName` field to `package.json`
- PyPI: add `mcp-name: io.github.equilibrium-team/tweekit-mcp` to README
- Docker: add `LABEL io.modelcontextprotocol.server.name="..."` to Dockerfile
- MCPB: host on GitHub Releases with SHA-256 hash

---

### 2. Anthropic Connectors Directory
**URL:** https://claude.com/connectors
**Remote submission form:** https://docs.google.com/forms/d/e/1FAIpQLSeafJF2NDI7oYx1r8o0ycivCSVLNq92Mpc1FPxMKSw1CzDkqA/viewform
**Local/MCPB submission form:** https://forms.gle/tyiAZvch1kDADKoP9
**Remote guide:** https://support.claude.com/en/articles/12922490-remote-mcp-server-submission-guide
**Local guide:** https://support.claude.com/en/articles/12922832-local-mcp-server-submission-guide
**FAQ:** https://support.claude.com/en/articles/11596036-anthropic-connectors-directory-faq

Two tracks:

**Track 1 — Remote MCP Server:**
- Must be production/GA; Streamable HTTP transport (SSE not accepted)
- OAuth 2.0 (authorization code flow) if auth required
- OAuth callbacks must whitelist: `http://localhost:6274/oauth/callback` and `https://claude.ai/api/mcp/auth_callback`
- HTTPS/TLS, CORS configured for claude.ai
- Tool results ≤ 25,000 tokens; responses within 300 seconds
- `readOnlyHint`/`destructiveHint` annotations on ALL tools — missing = immediate rejection
- Privacy policy at public HTTPS URL
- 3+ documented usage examples

**Track 2 — Local MCPB Bundle:**
- CLI: `npm install -g @anthropic-ai/mcpb` then `mcpb pack`
- `manifest.json` with `manifest_version: "0.3"` or higher
- `privacy_policies` array in manifest
- Tested cross-platform (macOS + Windows) in clean environment
- 512×512px PNG icon recommended
- 3+ working usage examples in README

Top rejection reasons: missing tool annotations, portability failures (clean-env install breaks), missing privacy policy.

---

### 3. GitHub MCP Registry (VS Code one-click installs)
**URL:** https://code.visualstudio.com/mcp
**Blog:** https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/

GitHub's curated subset of the official registry — tightly integrated with VS Code and GitHub Copilot. Currently ~44 verified partner servers (Notion, Stripe, Playwright, etc.).

**Submission:**
1. Publish to Official MCP Registry (step 1 above).
2. Email `partnerships@github.com` requesting inclusion in the GitHub-curated list.

Users get "Install in VS Code" one-click button. Enterprise customers can configure allowlists pointing to internal registry JSON endpoints.

---

### 4. OpenAI ChatGPT Apps Directory
**URL:** https://developers.openai.com/apps-sdk/
**Submission guide:** https://developers.openai.com/apps-sdk/deploy/submission/
**Status:** Beta

OpenAI adopted MCP in March 2025 (Agents SDK, Responses API, ChatGPT Desktop). The Apps SDK wraps an MCP server with optional UI and content security policies.

**Submission requirements:**
- Verified developer account with Owner role
- Production-hosted endpoint (no localhost)
- Content Security Policy (CSP) for all external data-fetching domains
- Tool hint annotations (`readOnlyHint`/`destructiveHint`) must match actual behavior
- App name, logo, description, company/privacy policy URLs
- Screenshots and test prompts with expected responses
- OAuth credentials if applicable

**Format:** Remote hosted endpoint only (no local/MCPB format accepted).

**Common rejections:** server connection failure, test cases producing wrong results, hint annotation mismatches, undisclosed data types returned.

---

## Tier 2 — High-Volume Aggregators

### 5. PulseMCP
**URL:** https://www.pulsemcp.com/servers
**Submit:** https://www.pulsemcp.com/submit
**Servers:** 10,400+

Daily-updated directory; PulseMCP is a member of the MCP Steering Committee. Publishing to the Official MCP Registry auto-propagates here within ~1 week. Also accepts direct URL submissions.

**Submission:** Submit GitHub repo URL at `/submit`. Choose type: MCP Server or MCP Client.

---

### 6. Glama
**URL:** https://glama.ai/mcp/servers
**Servers:** 19,000+ (as of March 2026)

Comprehensive daily-updated registry with security/quality grades. Assigns a letter grade based on documentation, tools, security practices.

**Submission / ownership claiming:**
```json
// Add glama.json to repo root:
{
  "$schema": "https://glama.ai/schema/glama.json",
  "maintainers": [
    {
      "name": "Equilibrium",
      "email": "support@tweekit.io",
      "url": "https://tweekit.io"
    }
  ]
}
```
Then go to glama.ai and use the "Claim ownership" flow. After merging the file, trigger a sync through the Claim flow again.

---

### 7. mcp.so
**URL:** https://mcp.so
**GitHub:** https://github.com/chatmcp/mcp-directory
**Servers:** 18,400+

Community-driven aggregator with a "Call Ranking" leaderboard based on call volume.

**Submission:** Create a GitHub issue in `chatmcp/mcp-directory` — Issue #1 is the canonical submission thread. Provide: server name, description, features, and connection info.

---

### 8. Smithery
**URL:** https://smithery.ai
**CLI:** `npm install -g @smithery/cli`
**Servers:** 2,880+

Registry + hosting platform. Supports hosted (Smithery runs your Docker container) and pass-through (install locally) modes. Generates OAuth modals so servers don't need to implement auth flows themselves.

**Submission:**
- CLI: `smithery mcp publish <github-url> -n equilibrium-team/tweekit-mcp`
- Web UI: smithery.ai/new (GitHub sign-in required)

**For hosted Docker deployment**, add `smithery.yaml` to repo root:
```yaml
runtime: "container"
build:
  dockerfile: ./Dockerfile
  dockerBuildPath: .
startCommand:
  type: "http"
configSchema:
  type: object
  properties:
    TWEEKIT_API_KEY:
      type: string
      description: "TweekIT API key"
    TWEEKIT_API_SECRET:
      type: string
      description: "TweekIT API secret"
  required: []
```
Container must listen on `$PORT` (Smithery sets it to 8081), expose `/mcp` endpoint with Streamable HTTP, and configure CORS.

---

## Tier 3 — Specialized / Pre-Packaged Directories

### 9. Docker MCP Catalog
**URL:** https://hub.docker.com/mcp
**Docs:** https://docs.docker.com/ai/mcp-catalog-and-toolkit/
**Registry GitHub:** https://github.com/docker/mcp-registry
**Servers:** 300+ verified

Containerized MCP servers available in Docker Desktop's MCP Toolkit. Full provenance, versioning, and SBOM metadata. Enterprise-trusted.

**Requirements:**
- Docker image with `LABEL io.modelcontextprotocol.server.name="io.github.equilibrium-team/tweekit-mcp"` in Dockerfile
- Image publicly accessible on Docker Hub or GHCR

**Submission:** PR to `docker/mcp-registry` per CONTRIBUTING.md. Available in Docker Desktop within 24h after approval.

---

### 10. ToolHive Registry
**URL:** https://toolhive.dev
**Registry GitHub:** https://github.com/stacklok/toolhive-registry
**Docs:** https://docs.stacklok.com/toolhive/

Security-focused MCP server management platform with a dedicated Registry Server (launched December 2025). Used by enterprise teams that require identity/SSO integration.

**Requirements:** Docker container image (primary format). No npm/PyPI direct support.

**Submission:**
1. Fork `stacklok/toolhive-registry`.
2. Add `registry/tweekit-mcp.json` following the `ServerJSON` schema with ToolHive `_meta` extensions.
3. Docker image must be publicly accessible on Docker Hub or GHCR.
4. Do NOT include filesystem paths or volume mounts.
5. Submit PR — evaluated on value/uniqueness, documentation quality, security practices.

---

### 11. MCPBundles.com
**URL:** https://www.mcpbundles.com/
**Bundles:** 670+

Dedicated directory for `.mcpb` bundles. The entire site is organized around Claude Desktop Extensions.

**Submission:** Click "Request Integration" on the site. Requires a completed `.mcpb` bundle (see `docs/claude-submission-checklist.md`).

---

### 12. Cline MCP Marketplace
**URL:** https://github.com/cline/mcp-marketplace
**Submit:** GitHub issue using the marketplace submission template

Cline is an AI coding agent (VS Code extension) with millions of users. Cline autonomously clones, sets up, and configures servers based on documentation.

**Requirements:**
- GitHub repository link
- 400×400px PNG logo
- Brief explanation of TweekIT value for Cline users
- `README.md` (and optionally `llms-install.md`) that an AI agent can follow to install

**Review criteria:** GitHub metrics, developer credibility, project maturity, security. Review takes a few days.

---

## Tier 4 — Lightweight (Submit in One Sprint)

| Directory | URL | Submit | Notes |
|---|---|---|---|
| MCPServe.com | https://mcpserve.com | https://mcpserve.com/submit | Web form: name, description, category, logo |
| Skills Playground | https://skillsplayground.com | https://skillsplayground.com/submit | 8,600+ skills for Claude Code, Cursor, Copilot, Windsurf, Cline |
| Cursor Directory MCP | https://cursor.directory/mcp | Web form on site | Targets Cursor IDE's 250k+ monthly devs |
| OpenTools Registry | https://opentools.com/registry | Web form on site | Curated, task-oriented; production-ready focus |
| awesome-mcp-servers | https://github.com/punkpeye/awesome-mcp-servers | Pull request | Alphabetical order; strict formatting requirements per CONTRIBUTING.md |
| modelcontextprotocol/servers | https://github.com/modelcontextprotocol/servers | Pull request | Official Anthropic reference list; higher bar |
| MCP Server Finder | https://www.mcpserverfinder.com | Contact form | Comprehensive with security/capability details |
| mcp-get | https://mcp-get.com | PR to `michaellatman/mcp-get` | CLI installer; note: not actively maintained as of 2025 |

---

## Meta-Registries (Aggregators of Aggregators)

These are not submission targets but are useful for discovery:

| Tool | URL | Purpose |
|---|---|---|
| Mastra MCP Registry Registry | https://mastra.ai/mcp-registry-registry | npm package `@mastra/mcp-registry-registry` — aggregates multiple registries programmatically |
| MCP Market | https://mcpmarket.com | Aggregator listing Cursor/Claude integrations |
| LobeHub MCP | https://lobehub.com/mcp | Aggregator with MCP server profiles |

---

## Submission Priority Matrix

| Action | Effort | Directories Unlocked |
|---|---|---|
| Add tool annotations to `server.py` | Low | Anthropic (both tracks), OpenAI |
| Publish to Official MCP Registry (`server.json`) | Medium | Official Registry, PulseMCP (auto), VS Code Copilot, GitHub Registry (after email) |
| Publish Docker image + add LABEL | Medium | Docker Catalog, ToolHive, Smithery hosted, Official Registry MCPB/Docker |
| Update MCPB to v0.3 (`mcpb pack`) | Medium | Anthropic local track, MCPBundles.com, Official Registry MCPB format |
| Add `glama.json` + claim ownership | Low | Glama quality grade + ownership panel |
| Submit to mcp.so, PulseMCP, MCPServe | Low | 3 directories, combined ~30k servers |
| Submit to Smithery + add `smithery.yaml` | Medium | Smithery hosted + pass-through |
| Submit to Cline Marketplace | Low | Cline ecosystem (millions of users) |
| Submit to Anthropic remote track | High | claude.com/connectors featured placement |
| Submit to OpenAI Apps SDK | High | ChatGPT Apps directory |

---

## Changelog

- **2026-03-13**: Initial comprehensive directory reference created, covering 20+ active directories as of Q1 2026. Includes Official MCP Registry, Anthropic Connectors (both tracks), OpenAI Apps SDK, GitHub Registry, Smithery, Docker Catalog, ToolHive, MCPBundles.com, Cline Marketplace, and 10+ aggregators.
