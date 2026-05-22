# TweekIT MCP Backlog

Use this backlog to seed GitHub issues or project tasks. Each item includes a suggested summary, recommended assignee, dependencies, and testing expectations.

## Core Platform Submissions

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Add tool annotations to server.py (`readOnlyHint`/`destructiveHint`) | Backend | None — do first | All tools expose correct annotations in `tools/list` response; required by both Anthropic and OpenAI reviewers |
| Deploy ChatGPT proxy + define CSP to staging + production | Backend + DevOps | Tool annotations; domain + TLS certs | Smoke test `/.well-known/ai-plugin.json`, `/version`, `/doctype`, `/convert`; document in `docs/chatgpt-plugin.md` |
| Submit to OpenAI ChatGPT Apps directory | Platform PM | Proxy deployed; tool annotations; privacy policy | Submission accepted; screenshots of ChatGPT configuration playground |
| Migrate MCPB build from `dxt` → `@anthropic-ai/mcpb` CLI; update manifest to v0.3 | SDK / DevOps | `npm install -g @anthropic-ai/mcpb` | `mcpb validate dist/tweekit-claude.mcpb` passes; CI workflow updated |
| Add `privacy_policies` array to `claude/manifest.json` | SDK | Privacy policy URL published | `mcpb validate` passes; privacy policy accessible at URL |
| Submit to Anthropic Connectors — local MCPB track | Platform PM | MCPB v0.3 bundle; macOS + Windows screenshots | Form submitted; receipt confirmed |
| Submit to Anthropic Connectors — remote MCP track | Platform PM | Tool annotations; OAuth strategy; privacy policy | Form submitted; receipt confirmed |

## Official MCP Registry & Auto-Propagation

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Create `server.json` and publish to Official MCP Registry | SDK / DevOps | `mcp-publisher` CLI installed; PyPI README annotation | Listing confirmed at `registry.modelcontextprotocol.io`; auto-ingested by PulseMCP within ~1 week |
| Add PyPI README annotation (`mcp-name: io.github.equilibrium-team/tweekit-mcp`) | SDK | PyPI package | Annotation visible in `tweekit-mcp` PyPI page README |
| Request GitHub MCP Registry curated inclusion | Platform PM | Official MCP Registry listing | Email sent to `partnerships@github.com`; server appears in VS Code MCP panel |

## Docker & Container Distribution

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Add MCP server LABEL to Dockerfile | DevOps | None | `docker inspect` shows `io.modelcontextprotocol.server.name` label |
| Publish Docker image to Docker Hub (`equilibriumteam/tweekit-mcp`) | DevOps | Dockerfile LABEL | Image publicly pullable; server starts on `PORT` env var |
| Add Docker Hub push to CI release workflow | DevOps | Docker Hub credentials in CI secrets | Image pushed automatically on tagged release |
| Submit PR to `docker/mcp-registry` (Docker MCP Catalog) | Platform PM | Docker image published | PR approved; server appears in Docker Desktop MCP Toolkit |
| Add `smithery.yaml` to repo; submit to Smithery hosted deployment | Backend + DevOps | Docker image; `smithery.yaml` spec | Smithery can start the container; server responds on Smithery-provided URL |
| Submit PR to `stacklok/toolhive-registry` (ToolHive) | Platform PM | Docker image | PR approved; server available in ToolHive |

## Lightweight Directory Submissions

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Submit to PulseMCP (direct URL) | Platform PM | None (or auto via Official Registry) | Server listed at `pulsemcp.com/servers` |
| Add `glama.json` to repo and claim Glama ownership | Platform PM | None | Ownership claimed; quality grade assigned at `glama.ai/mcp/servers` |
| Submit to mcp.so (GitHub issue in chatmcp/mcp-directory) | Platform PM | None | Server listed at `mcp.so` |
| Submit to MCPServe.com (web form) | Platform PM | None | Server listed at `mcpserve.com` |
| Submit to Skills Playground | Platform PM | None | Listed at `skillsplayground.com` |
| Submit to Cursor Directory MCP | Platform PM | None | Listed at `cursor.directory/mcp` |
| Submit to OpenTools Registry | Platform PM | None | Listed at `opentools.com/registry` |
| PR to `punkpeye/awesome-mcp-servers` | Platform PM | None | PR merged |
| PR to `modelcontextprotocol/servers` (official reference list) | Platform PM | None | PR merged |

## Claude Code Plugin Format

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Research Claude Code plugin spec and create `.claude-plugin/plugin.json` | SDK | None | Plugin loads in Claude Code; tools available |
| Submit to Claude Code Plugins Directory (`claude.com/plugins`) | Platform PM | Plugin format complete | Submission received via `clau.de/plugin-directory-submission` |

## Cline & AI-Agent Install

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Create `llms-install.md` for AI-agent-driven installation | DX | None | Cline can autonomously install server by following the file |
| Submit to Cline MCP Marketplace | Platform PM | `llms-install.md`; 400×400px logo | Listed at `github.com/cline/mcp-marketplace` |

## MCPBundles.com

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Submit `.mcpb` bundle to MCPBundles.com | Platform PM | MCPB v0.3 bundle complete | Server listed at `mcpbundles.com` |

## Existing Tasks (Carried Over)

| Summary | Suggested Owner | Dependencies | Acceptance / Tests |
| --- | --- | --- | --- |
| Grok native integration research | Platform PM | xAI roadmap updates | Update `docs/grok-integration.md` with findings; create prototype manifest if spec released |
| DeepSeek bridge hardening | AI Integrations | Live staging MCP endpoint | Add retry/backoff + logging to `scripts/deepseek_mcp_bridge.py`; add staging E2E test when available |
| IDE onboarding feedback loop | DX / Developer Relations | Release configs publicly | Collect Cursor/Continue user feedback; update `docs/developer-tools.md` and configs |
| Package Python helper for PyPI | SDK | Confirm API stability | Publish `tweekit-mcp-client` with semantic versioning; add packaging test in CI |
| Publish Node helper package | SDK | TypeScript helper maturity | Wrap quickstart into NPM module; add example tests |
| Add staging E2E pytest suite | QA / Platform | Staging endpoint + secrets management | Implement opt-in tests using env vars; update `docs/testing.md` coverage section |
| Host web converter on tweekit.io/converter | DevOps / Web | Production deployment | Publicly accessible URL; no local setup required |
| Add analytics to web converter | DX | Hosted web converter | Conversion metrics visible in analytics dashboard |
