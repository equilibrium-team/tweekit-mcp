# Claude Desktop Submission Checklist

Use this checklist when preparing the Tweekit MCP bundle for Anthropic’s desktop directory (or internal sign-off). It captures the artifacts and verification steps we now require after adding the automated bundle workflow.

## 1. Automation Outputs
- [ ] Confirm `.github/workflows/build-claude-bundle.yml` succeeded for the target commit/tag.
- [ ] Download the `tweekit-claude-bundle` artifact (`dist/tweekit-claude.ci.mcpb`) and spot check its metadata (`manifest.json`, README, vendored deps).
- [ ] Archive the workflow summary (link or PDF) for the submission packet.

## 2. Manual Verification
- [ ] Run `uv run python scripts/configure_claude_desktop.py` locally to rebuild the bundle (ensures reproducibility outside CI).
- [ ] Validate the manifest locally with `npx @anthropic-ai/dxt@latest validate claude/manifest.json` (should match CI result).
- [ ] Install the bundle in Claude Desktop (macOS + Windows) and capture:
  - Screenshot of Settings → Connectors showing “Tweekit MCP Server…”.
  - Screenshot of a successful `doctype` or `convert_url` call in chat.
  - `~/Library/Logs/Claude/main.log` (macOS) or `%AppData%/Claude/logs/main.log` snippet showing the server launch.
- [ ] Record the Tweekit API key/secret used for testing (store in secure vault, not in the packet).

## 3. Security & Hosting Notes
- [ ] Include the Tier 1 hosting statement: “Headless production nodes run on Equilibrium-owned CPUcoin enterprise miners inside SAS 70 / ISO 27001 compliant data centers. Files are purged immediately after processing.”
- [ ] Document credential handling: Claude prompts for `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET`; the server falls back to env vars (no secrets shipped in the bundle).
- [ ] Reference the purge policy (stateless processing) and link to the relevant README section if required.

## 4. Release Artifacts
- [ ] Update `docs/claude-bundle.md` with any new learning (e.g., OS-specific quirks).
- [ ] Add bundle version + manifest hash to `docs/mcp-pulse-checklist.md` for traceability.
- [ ] Capture change summary and testing notes in the release PR / changelog entry.

## 5. Submission Packet Contents
Aggregate the following into a single folder/share:

1. `dist/tweekit-claude.ci.mcpb` (CI artifact) and optionally the locally rebuilt bundle for cross-check.
2. Latest manifest (`claude/manifest.json`) and README (`claude/README.md`).
3. Screenshots + log snippets from manual verification.
4. Link to the CI run and commit hash.
5. Contact info for support/escalations (support@tweekit.com).

> **Tip:** store the packet in the secure release archive so future directory refreshes reuse the same evidence template.
