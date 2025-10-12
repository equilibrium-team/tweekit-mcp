# MCP Pulse Submission Checklist

Use this checklist when preparing the TweekIT MCP server for submission to the MCP Pulse community directory. Update it whenever requirements change.

## Required Artifacts
- ✅ Live MCP endpoint (staging + production) with healthy `/mcp` transport.
- ✅ ChatGPT plugin proxy deployed with accessible `/.well-known/ai-plugin.json` and OpenAPI schema.
- ✅ Claude `.mcpb` bundle built from `scripts/build_claude_bundle.py` and smoke-tested on macOS/Windows.
- ✅ Public documentation: integration guides (ChatGPT, Claude, Grok, DeepSeek, IDE, Quickstarts), security notes, testing guide.
- ✅ Versioned changelog for MCP releases (include bundle + proxy updates).

## Automated Testing
- ✅ `pytest` suite covering proxy, bundle packaging, config files, and helper SDK (`tests/`).
- ✅ CI pipeline executes `pip install -e .[dev] && pytest`.
- ✅ Plan for optional staging E2E tests (skipped by default; run manually before submission).

## Operational Requirements
- ✅ Secrets management strategy for API keys/secrets.
- ✅ Monitoring/alerting for hosted MCP endpoint.
- ✅ Rollback plan for proxy/bundle deployments.
- ✅ Hosting uptime SLA communicated in docs.

## Submission Packet
- ✅ README overview with integration links.
- ✅ Screenshots or recordings of each platform integration.
- ✅ Test results (latest `pytest` run) and deployment logs.
- ✅ Contact information & support plan (`support@tweekit.com` or equivalent).
- ✅ License and legal terms referenced in docs/manifests.

## Outstanding Tasks (Update as Completed)
- ☐ Configure CI workflow to publish bundle artifact and manifest checksums on release.
- ☐ Add staging-based E2E tests once endpoints are available.
- ☐ Collect partner feedback on IDE configs and update documentation accordingly.
