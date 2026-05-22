# Claude Desktop + Connectors Submission Checklist

Use this checklist when preparing TweekIT MCP for Anthropic's Connectors Directory. There are two tracks: **Remote MCP Server** (hosted endpoint) and **Local MCPB Bundle** (packaged stdio server). Both require tool annotations and a privacy policy. Complete tool annotations first — they are listed as the top rejection reason for both tracks.

> **Toolchain note:** The CLI is now `@anthropic-ai/mcpb` (not `dxt`). Install with `npm install -g @anthropic-ai/mcpb`. The `.dxt` extension still works but `.mcpb` is required for new submissions. Manifests must be `manifest_version: "0.3"` or higher.

---

## Pre-flight: Tool Annotations (Blocks Both Tracks)

Anthropic reviewers reject submissions immediately if tools are missing `readOnlyHint` or `destructiveHint` annotations.

- [ ] Add `readOnlyHint: true` to `doctype`, `search`, `fetch`, `version` tools in `server.py`.
- [ ] Add `readOnlyHint: false, destructiveHint: false` to `convert` and `convert_url` (they transform data but don't modify external state).
- [ ] Verify annotations are exposed in `tools/list` response from the live MCP endpoint.

---

## Track 1: Remote MCP Server

**Submission form:** https://docs.google.com/forms/d/e/1FAIpQLSeafJF2NDI7oYx1r8o0ycivCSVLNq92Mpc1FPxMKSw1CzDkqA/viewform
**Guide:** https://support.claude.com/en/articles/12922490-remote-mcp-server-submission-guide

### Transport & Hosting
- [ ] Confirm `https://mcp.tweekit.io/mcp` is in production/GA (not beta or demo).
- [ ] Verify **Streamable HTTP** transport is active — SSE-only transport is NOT accepted.
- [ ] Confirm valid TLS certificate (no self-signed; no expired cert).
- [ ] Verify CORS headers allow `claude.ai` and `localhost` origins.
- [ ] Confirm responses return within 300 seconds and tool results are under 25,000 tokens.

### Authentication
- [ ] Decide on auth strategy: OAuth 2.0 (preferred) OR document acceptable anonymous/key-based path with Anthropic.
- [ ] If using OAuth 2.0: whitelist both callback URLs in your OAuth provider:
  - `http://localhost:6274/oauth/callback`
  - `https://claude.ai/api/mcp/auth_callback`

### Documentation & Compliance
- [ ] Publish privacy policy at a public HTTPS URL.
- [ ] Add privacy policy URL to `claude/manifest.json` (`privacy_policies` array).
- [ ] Add privacy policy reference to `claude/README.md`.
- [ ] Prepare minimum 3 documented usage examples with expected Claude responses.
- [ ] Confirm dedicated support channel is set up (`support@tweekit.io`).

### Evidence
- [ ] Capture screenshot: Claude Desktop Settings → Connectors showing "TweekIT MCP".
- [ ] Capture screenshot: successful `doctype` call response in Claude chat.
- [ ] Capture screenshot: successful `convert_url` call response in Claude chat.

---

## Track 2: Local MCPB Bundle

**Submission form:** https://forms.gle/tyiAZvch1kDADKoP9
**Guide:** https://support.claude.com/en/articles/12922832-local-mcp-server-submission-guide
**Build docs:** https://support.claude.com/en/articles/12922929-building-desktop-extensions-with-mcpb

### Toolchain Setup
- [ ] Install new CLI: `npm install -g @anthropic-ai/mcpb`.
- [ ] Verify version: `mcpb --version`.

### Manifest Updates
- [ ] Update `claude/manifest.json`:
  - `manifest_version`: set to `"0.3"` (minimum required).
  - `privacy_policies`: add array with privacy policy URL.
  - Tool annotations present in tool definitions.
  - 512×512px icon recommended (`claude/icon.png`).
- [ ] Update `claude/README.md` with privacy policy reference.

### Build & Validate
- [ ] Rebuild bundle: `mcpb pack` from the `claude/` directory → outputs `dist/tweekit-claude.mcpb`.
- [ ] Validate: `mcpb validate dist/tweekit-claude.mcpb` — must pass with no errors.
- [ ] Update CI workflow (`.github/workflows/build-claude-bundle.yml`) to use `mcpb pack` instead of `dxt pack`.

### Cross-Platform Testing
- [ ] **macOS**: Install `dist/tweekit-claude.mcpb` via Claude Desktop → Settings → Extensions → Install Extension (or double-click).
  - Screenshot: Settings → Extensions showing "TweekIT MCP Server".
  - Screenshot: successful `doctype` or `convert_url` call in chat.
  - Log snippet: `~/Library/Logs/Claude/main.log` showing server launch (no errors).
- [ ] **Windows**: Install in a clean environment.
  - Screenshot: Settings → Extensions showing "TweekIT MCP Server".
  - Screenshot: successful tool call.
  - Log snippet: `%AppData%/Claude/logs/main.log`.
- [ ] Test in a clean environment (no pre-existing credentials) to confirm credential prompting works.
- [ ] Record API key/secret used for testing in secure vault (do NOT include in submission packet).

### Automation Outputs
- [ ] Confirm `.github/workflows/build-claude-bundle.yml` succeeded for the target tag.
- [ ] Download `tweekit-claude-bundle` artifact (`dist/tweekit-claude.mcpb`) and spot-check:
  - `manifest.json` has `manifest_version: "0.3"` or higher.
  - `privacy_policies` array is populated.
  - README is present.
  - Vendored dependencies are included.
- [ ] Archive the workflow run summary (link or PDF) for the submission packet.

---

## Security & Hosting Notes (Both Tracks)

- [ ] Include Tier 1 hosting statement: *"Headless production nodes run on Equilibrium-owned CPUcoin enterprise miners inside SAS 70 / ISO 27001 compliant data centers. Files are purged immediately after processing."*
- [ ] Document credential handling: Claude prompts for `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET`; the server falls back to env vars (no secrets shipped in the bundle).
- [ ] Reference purge policy (stateless processing) and link to the relevant README section.

---

## Submission Packet Contents

Aggregate the following into a single folder/share for each track:

**Remote Track:**
1. Production endpoint URL and transport type.
2. OAuth configuration details (or auth exemption rationale).
3. Screenshots of Claude integration + live tool calls.
4. Privacy policy URL.
5. 3+ usage examples with expected responses.
6. Support contact (`support@tweekit.io`).

**Local MCPB Track:**
1. `dist/tweekit-claude.mcpb` (CI artifact) and optionally locally rebuilt for cross-check.
2. Latest `claude/manifest.json` and `claude/README.md`.
3. Screenshots + log snippets from macOS and Windows installs.
4. Link to CI run and commit hash.
5. Privacy policy URL.
6. Contact info: `support@tweekit.io`.

> Store the packet in the secure release archive so future directory refreshes reuse the same evidence template.

---

## Changelog

- **2026-03-13**: Updated for `@anthropic-ai/mcpb` CLI (replacing `dxt`), `manifest_version: "0.3"` requirement, OAuth 2.0 guidance, and tool annotation pre-flight requirement. Added Remote Track checklist.
