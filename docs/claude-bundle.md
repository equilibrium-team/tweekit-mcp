 # Claude Desktop Bundle Guide
 
This guide captures everything we learned while packaging the Tweekit MCP server for Claude Desktop using the Anthropic `.mcpb` format. Follow it whether you’re using the upstream bundle or rolling your own from this repository.

> **Hosting context:** Production workloads run on Tier 1 nodes—Equilibrium-owned CPUcoin enterprise miners hosted in SAS 70 / ISO 27001 compliant data centers. The local bundle keeps feature parity so you can rehearse the exact flows before touching those hardened environments.
 
 ## Why We Bundle Locally
 
 Claude Desktop requires every MCP server to be installable as a local process launched via stdio. Even if your production server runs remotely, the `.mcpb` needs to include:
 
 - The MCP entry point (`server.py`) that can run over stdio.
 - All Python dependencies vendored alongside the server.
 - A manifest that tells Claude how to invoke the process and collect user-supplied credentials.
 
 We switched from the old remote-only manifest to a fully self-contained bundle so Claude could validate and launch it without custom code.
 
 ## Directory Layout Recap
 
 The bundle produced by `scripts/build_claude_bundle.py` has this structure:
 
 ```
 tweekit-claude.mcpb (zip archive)
 ├── manifest.json
 ├── README.md
 ├── server/
 │   └── server.py
 └── python/
     └── <vendored wheels and packages>
 ```
 
 `python/` is populated by `pip install --target` so the stdio server can import `fastmcp`, `httpx`, `fastapi`, and their dependencies without talking to PyPI at runtime.
 
 ## Manifest Requirements (DXT Schema)
 
 Claude Desktop validates the manifest against the [`@anthropic-ai/dxt` schema](https://github.com/anthropics/dxt). Key fields we rely on:
 
 - `dxt_version`: currently `0.1`.
 - `server.type`: set to `"python"`.
 - `server.entry_point`: path to the entry script inside the bundle (`server/server.py`).
 - `server.mcp_config.command`: `"python3"` (Claude launches the local Python runtime).
 - `server.mcp_config.args`: `["${__dirname}/server/server.py", "--transport", "stdio"]`.
 - `server.mcp_config.env`: sets `PYTHONPATH` to include the vendored packages and wires user config variables into `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET`.
 - `user_config`: prompts the installer for API credentials (marked as required + sensitive).
 - `compatibility.platforms`: `["darwin", "win32"]` at minimum.
 
 After editing `claude/manifest.json`, run:
 
 ```bash
 npx @anthropic-ai/dxt@latest validate claude/manifest.json
 ```
 
 Claude also refuses bundles where the manifest name/description/version are missing or inconsistent, so keep those current.
 
 ## Building the Bundle
 
 We rely on `scripts/build_claude_bundle.py`. It stages the server, vendors dependencies, and zips everything up. Use `uv` (or your preferred Python runner) so the script inherits the repo’s interpreter.
 
 ```bash
 uv run python scripts/build_claude_bundle.py \
   --version 1.6.01 \
   --output dist/tweekit-claude.mcpb
 ```
 
 The script will:
 
 1. Copy `claude/manifest.json` into a temporary bundle directory.
 2. Copy `claude/README.md` (if present) for end-user instructions.
 3. Copy `server.py` into `server/server.py`.
 4. Run `pip install --target bundle/python fastmcp==… httpx==… fastapi==…`.
 5. Zip the directory into `dist/tweekit-claude.mcpb`.
 
We pin dependency versions in the script to match `uv.lock`, so update both places on version bumps.

### Guided Setup Script

Prefer a step-by-step walkthrough? Use the interactive helper:

```bash
uv run python scripts/configure_claude_desktop.py
```

It will:

1. Prompt for the bundle version/output path (defaults to the manifest values).
2. Call the bundler to regenerate `dist/tweekit-claude.mcpb`.
3. Run `npx @anthropic-ai/dxt@latest validate claude/manifest.json` when Node tooling is present.
4. Print the Claude Desktop import steps with a reminder about supplying `TWEEKIT_API_KEY` / `TWEEKIT_API_SECRET`.

Credentials are never stored; Claude injects them at launch time just like the Tier 1 headless nodes do in production.

## Preparing Your Own Manifest
 
 If you fork this project or build a custom MCP server:
 
 1. Start with `npx @anthropic-ai/dxt init` to generate a skeleton manifest.
 2. Set `server.type`, `entry_point`, and `mcp_config` to match your server layout.
 3. Bundle any non-standard dependencies into `python/` (or provide a self-contained virtualenv).
 4. Use `user_config` entries for secrets; Claude will prompt users and inject the values as environment variables when launching the process.
 5. Annotate your manifest with up-to-date `version`, `description`, and `author`.
 
 ## Installation Flow
 
 1. Open Claude Desktop → **Settings → Connectors → Advanced → Developer Mode** (Plus/Pro accounts).
 2. Click **Install from file** and choose `dist/tweekit-claude.mcpb`.
 3. Enter `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET` when prompted.
 4. Claude verifies the manifest, unpacks the bundle, and runs the server via stdio.
 5. Ask Claude “list Tweekit tools” or invoke `doctype` to confirm everything is wired up.
 
 If installation fails:
 
 - Check `~/Library/Logs/Claude/main.log` (macOS) or `%AppData%/Claude/logs/main.log` (Windows).
 - Run `npx @anthropic-ai/dxt validate` on the manifest or `npx @anthropic-ai/dxt info dist/tweekit-claude.mcpb` to inspect the bundle.
 
 ## Troubleshooting & Lessons Learned
 
 - **Manifest validation:** Claude emits generic “invalid bundle” errors if required fields are missing. Always run the CLI validator before distribution.
 - **Credential handling:** Tools like `convert`/`convert_url` now treat API credentials as optional arguments and fall back to `TWEEKIT_API_KEY`/`TWEEKIT_API_SECRET`, so Claude’s stored secrets work seamlessly.
 - **Dependency size:** Vendored wheels can push the bundle past 20 MB; that’s acceptable, but prune unused packages if you add new dependencies.
 - **Cross-platform:** Default command (`python3`) works on macOS and modern Windows with Python installed via the bundle. If you embed a specific interpreter or target Linux, add `platform_overrides` in `mcp_config`.
 
## Future Enhancements

- Add CI automation to rebuild and validate the bundle on each release tag.
- Offer signed bundles once Anthropic publishes their signing guidelines.
- Explore slimmer dependency sets or compiled binaries (PyInstaller) if we need sub-10 MB artifacts.
- Reference the submission checklist (`docs/claude-submission-checklist.md`) before shipping to Anthropic; it outlines required screenshots, logs, and CI artifacts.
 
 With this workflow, you can ship a Claude-ready MCP bundle that mirrors production behavior, keeps credentials local, and passes Anthropic’s validation. Customize the manifest and build script as needed for your own servers, and share updates via PRs so the rest of the team stays in sync.
