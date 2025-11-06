# DeepSeek Integration Guide

DeepSeek does not yet provide a first-class MCP connector, but teams can still incorporate TweekIT by pairing the DeepSeek API with a lightweight bridge that forwards file conversion requests to the MCP server. This guide covers both the interim bridge workflow and future readiness work once DeepSeek exposes native tooling.

## Current Workflow (API + Bridge Script)
1. Obtain a DeepSeek API key and confirm your deployment can issue HTTPS requests (DeepSeek’s API is compatible with the OpenAI-style chat/completions format).
2. Configure TweekIT credentials for the MCP server (API key + secret).
3. Use the bridge script to convert documents before passing results back into your DeepSeek agent logic:

```bash
python scripts/deepseek_mcp_bridge.py \
  --file path/to/input.pdf \
  --outfmt txt \
  --server https://mcp.tweekit.io/mcp \
  --api-key "$TWEEKIT_API_KEY" \
  --api-secret "$TWEEKIT_API_SECRET" \
  --output converted.txt
```

The script invokes the MCP `convert` tool via `fastmcp.Client`, writing any base64 content to `converted.txt` when the response includes binary data (images, PDFs, etc.). You can embed this call inside your DeepSeek agent loop—e.g., have the LLM request a conversion, run the script, then stream the normalized text back into the conversation.

## Using the Script in Automation
- **Python orchestration:** Import `convert_document` from `scripts/deepseek_mcp_bridge` and call it inside an async workflow tied to DeepSeek completions.
- **CLI pipelines:** Run the script inside a shell pipeline before invoking DeepSeek’s `chat.completions` endpoint, piping plain text output back to the model.
- **Credential handling:** Provide `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET` via environment variables or parameter flags; rotate keys through your secrets manager.

## Future Native Integration
- Monitor DeepSeek announcements for MCP or plugin support. Once official hooks exist, reuse the same configuration (`https://mcp.tweekit.io/mcp`) and tool names (`version`, `doctype`, `convert`).
- Prepare a DeepSeek-specific manifest mirroring the ChatGPT plugin proxy if their platform adopts an OpenAPI-based registration system.
- Add automated tests that validate TweekIT responses through DeepSeek’s tooling as soon as beta access becomes available.

## Action Items
- [ ] Wire the bridge script into your existing DeepSeek agent process.
- [ ] Capture output samples (logs/screenshots) demonstrating successful conversions for onboarding docs.
- [ ] Track DeepSeek’s platform updates quarterly and revisit this guide when official integration paths launch.
