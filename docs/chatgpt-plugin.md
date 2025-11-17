# ChatGPT Plugin Packaging Guide

This document explains how to run the FastAPI proxy, publish the ChatGPT plugin manifest, and verify that the plugin can call the TweekIT MCP server through REST endpoints.

## Prerequisites
- Python 3.10+
- TweekIT API credentials (`ApiKey` + `ApiSecret`)
- Domain or tunnel (e.g., HTTPS ngrok) to expose the proxy with TLS

## Environment Variables
| Variable | Purpose | Example |
| --- | --- | --- |
| `TWEEKIT_API_BASE_URL` | Override upstream TweekIT API root (optional). | `https://dapp.tweekit.io/tweekit/api/image/` |
| `TWEEKIT_API_KEY` | Default API key for proxy requests. | `abc123` |
| `TWEEKIT_API_SECRET` | Default API secret for proxy requests. | `def456` |
| `PLUGIN_PUBLIC_BASE_URL` | Public HTTPS origin hosting the proxy. | `https://mcp.tweekit.io/mcp` |
| `PLUGIN_LOGO_URL` | Absolute URL for plugin logo. | `https://tweekit.com/assets/logo.png` |

> If you omit `TWEEKIT_API_KEY`/`SECRET`, each request must include either a `Bearer` token in `Authorization` or both `X-Api-Key` and `X-Api-Secret` headers.

## Run the Proxy Locally
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt  # or `pip install fastapi uvicorn httpx`
uvicorn plugin_proxy:app --host 0.0.0.0 --port 8000 --reload
```

Expose the service via HTTPS (e.g., `ngrok http 8000`) so ChatGPT can reach it.

## Verify Endpoints
Set `PROXY_URL` to the Cloud Run URL (or ngrok tunnel) that is running `plugin_proxy.py`. Then verify the REST surface that ChatGPT will call:

```bash
PROXY_URL="https://tweekit-mcp-stage-958133016924.us-west1.run.app"

curl "$PROXY_URL/.well-known/ai-plugin.json"

curl -H "Authorization: Bearer $TWEEKIT_API_KEY" \
  "$PROXY_URL/version"

curl -H "Authorization: Bearer $TWEEKIT_API_KEY" \
  "$PROXY_URL/doctype?ext=pdf"

curl -X POST -H "Authorization: Bearer $TWEEKIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inext": "png", "outfmt": "pdf", "blob": "<base64>"}' \
  "$PROXY_URL/convert"
```

All three endpoints must return HTTP 200 before publishing.

## ChatGPT Manual Installation (Developer Settings)

> **Prerequisite:** ChatGPT Pro/Plus users can unlock the full MCP toolset by enabling *Settings → Connectors → Advanced → Developer mode*. Team/Enterprise plans already include Actions access.

1. Open ChatGPT and click your avatar → *Settings & Beta* → *Developer*. Toggle **Enable Actions** if it is off.
2. Under *User Settings → Developer → Actions*, select **Add Action** and choose **Import from URL**.
3. Paste `https://mcp.tweekit.io/mcp/.well-known/ai-plugin.json` (or the staging proxy URL). ChatGPT fetches the manifest and OpenAPI schema automatically.
4. When the Auth screen appears, pick **Bearer Token** and paste your TweekIT API key. The proxy forwards this value as `ApiKey`; you can supply `ApiSecret` later via headers if needed.
5. Finish the import, then use the *Preview Action* panel to run:
   - `List supported TweekIT doctype options`
   - `Convert a PNG to PDF` (upload a small test file)
   - Ensure the response includes file attachments or JSON as expected.
6. Save the Action so it is available to your custom GPTs or workspace.

## Cloud Run Deployment Checklist

### Stage
1. Build/publish the container image (already handled by `scripts/deploy_cloud_run.sh` or Cloud Build).
2. Deploy the proxy:
   ```bash
   bash scripts/deploy_cloud_run.sh stage \
     --version 1.6.01 \
     --project tweekitmcp-a26b6 \
     --env-file stage.env \
     --command uv \
     --args run,uvicorn,plugin_proxy:app,--host,0.0.0.0,--port,8080
   ```
   `stage.env` must export `TWEEKIT_API_KEY`, `TWEEKIT_API_SECRET`, and `PLUGIN_PUBLIC_BASE_URL=https://mcp.tweekit.io/mcp`.
3. Map the staging hostname (e.g., `staging.mcp.tweekit.io`) to the Cloud Run service or use the default `*.a.run.app` URL.
4. Run the curl smoke tests above and capture screenshots from the ChatGPT configuration playground.

### Production
1. Deploy the same image with `--version <release-tag>` against the `tweekit-mcp` Cloud Run service (prod target in `deploy_cloud_run.sh`).
2. Point `mcp.tweekit.io` at the prod service via a Cloud Run domain mapping (manage TLS and DNS records).
3. Confirm:
   - `https://mcp.tweekit.io/mcp/.well-known/ai-plugin.json`
   - `https://mcp.tweekit.io/mcp/openapi.json`
   - `GET /version`, `GET /doctype`, `POST /convert` (with bearer token)
4. Document the deploy in the release notes and update the MCP Pulse packet with screenshots and logs.

## Submission Checklist
- [ ] Manifest `/ .well-known/ai-plugin.json` reachable over HTTPS.
- [ ] `/openapi.json` reflects proxy routes.
- [ ] Logo and legal/contact links render.
- [ ] `version`, `doctype`, `convert` calls succeed via ChatGPT Configuration playground.
- [ ] Documented fallback strategy for rotating API credentials.
