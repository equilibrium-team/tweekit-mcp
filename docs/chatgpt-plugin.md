# ChatGPT Plugin Packaging Guide

This document explains how to run the FastAPI proxy, publish the ChatGPT plugin manifest, and verify that the plugin can call the TweekIT MCP server through REST endpoints.

## Prerequisites
- Python 3.10+
- TweekIT API credentials (`ApiKey` + `ApiSecret`)
- Domain or tunnel (e.g., HTTPS ngrok) to expose the proxy with TLS

## Environment Variables
| Variable | Purpose | Example |
| --- | --- | --- |
| `TWEAKIT_API_BASE_URL` | Override upstream TweekIT API root (optional). | `https://dapp.tweekit.io/tweekit/api/image/` |
| `TWEAKIT_API_KEY` | Default API key for proxy requests. | `abc123` |
| `TWEAKIT_API_SECRET` | Default API secret for proxy requests. | `def456` |
| `PLUGIN_PUBLIC_BASE_URL` | Public HTTPS origin hosting the proxy. | `https://plugin.tweekit.com` |
| `PLUGIN_LOGO_URL` | Absolute URL for plugin logo. | `https://tweekit.com/assets/logo.png` |

> If you omit `TWEAKIT_API_KEY`/`SECRET`, each request must include either a `Bearer` token in `Authorization` or both `X-Api-Key` and `X-Api-Secret` headers.

## Run the Proxy Locally
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt  # or `pip install fastapi uvicorn httpx`
uvicorn plugin_proxy:app --host 0.0.0.0 --port 8000 --reload
```

Expose the service via HTTPS (e.g., `ngrok http 8000`) so ChatGPT can reach it.

## Verify Endpoints
```bash
curl -H "Authorization: Bearer $TWEAKIT_API_KEY" \
  "https://plugin.tweekit.com/version"

curl -H "Authorization: Bearer $TWEAKIT_API_KEY" \
  "https://plugin.tweekit.com/doctype?ext=pdf"

curl -X POST -H "Authorization: Bearer $TWEAKIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inext": "png", "outfmt": "pdf", "blob": "<base64>"}' \
  "https://plugin.tweekit.com/convert"
```

## ChatGPT Manual Installation
1. Navigate to *Settings → GPTs → Create new GPT → Configure → Actions*.
2. Choose *Import from URL* and provide `https://plugin.tweekit.com/.well-known/ai-plugin.json`.
3. Assign the bearer token (TweekIT API key) when prompted for authentication.
4. Test actions by requesting `List supported TweekIT doctype options`.

## Submission Checklist
- [ ] Manifest `/ .well-known/ai-plugin.json` reachable over HTTPS.
- [ ] `/openapi.json` reflects proxy routes.
- [ ] Logo and legal/contact links render.
- [ ] `version`, `doctype`, `convert` calls succeed via ChatGPT Configuration playground.
- [ ] Documented fallback strategy for rotating API credentials.
