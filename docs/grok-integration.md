# xAI Grok Integration Strategy

This document captures the current path to enable TweekIT MCP inside xAI’s Grok assistant and outlines the roadmap toward a native integration once official tooling is published.

## Current State (Q1 2025)
- Grok does not yet expose a public plugin or MCP connector interface.
- Power users rely on community extensions (e.g., **MCP SuperAssistant**, custom browser extensions) to inject MCP toolchains, including TweekIT.
- Therefore, our immediate offering is a guided workflow using these third-party extensions while we track xAI’s roadmap.

## Interim Workflow via MCP SuperAssistant
1. Install the MCP SuperAssistant browser extension (Chrome/Edge) from the web store.
2. Open the extension options and add a server entry:
   - **Name:** TweekIT Converter
   - **URL:** `https://mcp.tweekit.com/mcp` (update as needed)
   - **Transport:** `streamable-http`
   - Provide `TWEAKIT_API_KEY`/`SECRET` in the extension’s credential fields.
3. Enable Grok (plus any other supported chat UIs) inside the extension.
4. Within the Grok interface, invoke TweekIT tools using the extension’s command palette or slash commands.

> Note: Third-party extensions are outside our control. Provide clear disclaimers and advise users to review extension security policies before entering credentials.

## Future-Native Integration Plan
- **Manifest Prep:** Reuse the ChatGPT proxy schema (`.well-known/ai-plugin.json`) or adapt it to xAI’s forthcoming plugin spec once available.
- **Proxy Readiness:** Ensure `plugin_proxy.py` supports any authentication scheme xAI mandates (OAuth or service auth). For now it accepts bearer and header credentials.
- **Monitoring:** Track xAI announcements for official plugin or MCP support. Key signals:
  - Developer portal and API documentation updates from xAI.
  - Early access programs for tool builders—submit interest requests when offered.
  - Compatibility requirements (rate limits, response formats) for Grok tools.
- **Backlog Items:**
  - Build a Grok-specific onboarding guide mirroring ChatGPT/Claude documentation as soon as APIs stabilize.
  - Add automated tests to validate the proxy against xAI’s schema once public.

## Action Items
- [ ] Maintain communication with xAI developer relations for roadmap visibility.
- [ ] Provide trained support staff with the interim extension instructions.
- [ ] Schedule quarterly review of Grok integration status and update this doc accordingly.
