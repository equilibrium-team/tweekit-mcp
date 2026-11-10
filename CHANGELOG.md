# Changelog

All notable changes to the TweekIT MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.8.3] - 2026-11-10

### Security
- **Zero-Egress Guarantee by Default for Local Miner Mode (`local_miner=True` / `TWEEKIT_MINER_LOCAL=1`)**: `_is_local_only_mode()` and `_assert_outbound_internet_allowed()` now automatically enforce zero-cloud-egress semantics whenever `TWEEKIT_MINER_LOCAL=1` or `TweekitDirectClient(local_miner=True)` is active, blocking outbound internet tools (`convert_url`, `fetch`, `search`) by default unless `TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1`, `TWEEKIT_LOCAL_ONLY=0`, or `TweekitDirectClient(local_miner=True, allow_remote_fetch=True)` is explicitly set.
- **Wildcard Bind Address Rejection (`0.0.0.0` / `::`) & Loopback Kestrel Alignment**: `_resolve_api_base_url()` and `_is_local_or_onprem_api_url()` now explicitly reject `0.0.0.0` and `::` wildcard bind URLs in `TWEEKIT_API_BASE_URL` and `TWEEKIT_ONPREM_HOSTS`, paired with the `equilibrium-team/tweekit-api@6727c59` update binding `TweekIT_API/appsettings.Release_CloudMaitrix.json` to `http://127.0.0.1:5000` by default.

## [1.8.2] - 2026-11-10

### Added
- **On-Premises & Localhost Miner Renderery Support (`--local-miner`, `TWEEKIT_API_BASE_URL`, `TWEEKIT_LOCAL_ONLY=1`)**: Added first-class support for routing `tweekit-mcp` and `TweekitDirectClient(local_miner=True)` to a local or on-premises **Miner Renderery** (`http://127.0.0.1:16377/api/image/` or `http://127.0.0.1:5000/api/image/`), serving as the last-mile MCP integration for the **New Miner Installation Initiative**.
- **Zero-Cloud-Egress Enforcement (`TWEEKIT_LOCAL_ONLY=1` & `TWEEKIT_REQUIRE_LOCAL_MINER_FOR_FILES=1`)**: Guarantees that local workspace files converted via `convert_file` or `convert` never leave the host machine or private LAN (`TWEEKIT_ONPREM_HOSTS`) and blocks outbound internet tools (`convert_url`, `fetch`, `search`) when running in air-gapped local mode.
- **Loopback `NOAUTH;NODB` Miner Renderery Mode (`TWEEKIT_MINER_NOAUTH=1`)**: Allows local `stdio` MCP sessions and `TweekitDirectClient` to communicate with a loopback `NOAUTH;NODB` Miner Renderery without requiring cloud portal API credentials, while forwarding `X-CPUCoinMiner-*` diagnostic headers.
- **Runtime Mode Introspection Resource (`config://tweekit-runtime-mode`)**: Added an MCP resource reporting `execution_mode` (`"onprem-miner-renderery"` vs `"cloud-cgn"`), `api_base_url`, `local_only_zero_egress`, and `local_files_enabled`.
- **On-Premises Miner Renderery Specification & Security Policy**: Added [`docs/onprem-miner-renderery-spec.md`](docs/onprem-miner-renderery-spec.md), [`SECURITY.md`](SECURITY.md), [`glama.json`](glama.json), and [`smithery.yaml`](smithery.yaml).

### Changed
- **Explicit Direct Runtime Dependencies & CI Registry Sync**: Declared `httpcore>=1.0.9`, `starlette>=1.7.0` (`1.10.0` on Python 3.11+), and `uvicorn>=0.54.0` explicitly in `pyproject.toml`, `functions/requirements.txt`, and `scripts/build_claude_bundle.py`, expanded `_SENSITIVE_PATH_SEGMENTS` to block IDE/agent config directories (`.vscode`, `.idea`, `.github`, `.claude`, `.cursor`, `.gemini`), and updated `.github/workflows/publish-mcp.yml` to wait for PyPI version propagation (failing closed on timeout) before running `mcp-publisher publish`.

## [1.8.1] - 2026-11-09

### Changed (Breaking Security Hardening)
- **Credential-Free MCP Tool Schemas & Atomic HTTP Header Auth**: Removed `apiKey` and `apiSecret` from all LLM-visible MCP tool schemas (`server.py`, `functions/main.py`) and REST JSON request bodies (`plugin_proxy.py`) so credentials never enter model context or tool-call logs. Callers authenticate via HTTP `ApiKey` + `ApiSecret` headers (sent automatically by `TweekitClient` via `StreamableHttpTransport`) or `TWEEKIT_API_KEY` + `TWEEKIT_API_SECRET` environment variables on local `stdio` servers.
- **Explicit Workspace Requirement for Local File Conversion (`convert_file`)**: Local file access now defaults to `TWEEKIT_ALLOW_LOCAL_FILES=0`, is unconditionally disabled during HTTP requests, and requires `TWEEKIT_ALLOWED_DIRS` to be explicitly configured when opted in on `stdio`.

### Security
- **Supply-Chain Dependency Upgrade (`0` CVEs)**: Raised dependency floors to `fastmcp>=4.1.6`, `mcp>=2.3.0`, `fastapi>=0.162.2`, and `certifi>=2026.10.23` across `pyproject.toml`, `uv.lock`, `functions/requirements.txt`, and `scripts/build_claude_bundle.py`, remediating `CVE-2026-32871`, `CVE-2026-27124` (`GHSA-rww4-4w9c-7733`), `GHSA-7xgj-8392-5q4r`, and `CVE-2025-64340`.
- **Connect-Time DNS IP Pinning & SSRF Protections (`convert_url`, `fetch`, `/convert-url`)**: Enforced `https://`-only URLs, connect-time IP pinning (`_PinnedPublicDNSBackend`) preventing DNS-rebinding TOCTOU across initial requests and every redirect hop (`max_redirects=5`), IPv4/IPv6/NAT64/6to4/Teredo private-range blocking, a `25 MiB` streaming download cap, and a non-credential `fetchHeaders` allowlist.
- **Symlink-Safe Local Sandbox (`lstat` + `O_NOFOLLOW`)**: Unconditionally rejects existing and dangling symlinks on read and write paths (including `TWEEKIT_ALLOW_OVERWRITE=1`), blocks workspace-relative dotfile/credential paths, enforces safe media/document output extensions, validates `docId`/`inext`/`outfmt` tokens, and binds `--host` to `127.0.0.1` locally (`0.0.0.0` in Cloud Run/Docker) with `host_origin_protection="auto"`.

### Fixed
- **Trailing-Slash `/mcp/` In-Place Routing & Registry Ownership Markers**: Added `_NormalizeMcpPathMiddleware` and Uvicorn `--proxy-headers` support so both `https://mcp.tweekit.io/mcp` and `https://mcp.tweekit.io/mcp/` initialize directly (`200 OK`) without `307` redirects or `http://` scheme downgrades, and included both active Official MCP Registry ownership markers (`io.github.equilibrium-team/tweekit` and `io.tweekit/mcp`) in `README.md`.

## [1.8.0] - 2026-10-28

### Added
- **Official PyPI Package (`pip install tweekit`)**: Published under the approved **AMPS dba Equilibrium** PyPI organization (`Equilibrium/tweekit`), exposing both `tweekit` and `tweekit-mcp` CLI entry points plus `import tweekit` and `import tweekit_mcp` SDK namespaces.
- **Full Async Python SDK (`TweekitClient` & `TweekitDirectClient`)**: Added direct async REST API conversion (`convert_bytes`, `convert_file`, `convert_url`), concurrent `batch_convert`, and MCP client wrappers.
- **AI Hub Preflight & Modality Router (`preflight` tool & `preflight_check`)**: Added 450+ file-extension taxonomy (`FORMAT_TAXONOMY`) and provider-aware target format recommendations aligned with **Maitrix AI Hub**, Claude, OpenAI, Gemini, Mistral, Grok, and DeepSeek.
- **Local File Conversion Tool (`convert_file`)**: Added opt-in (`TWEEKIT_ALLOW_LOCAL_FILES`) local path ingestion tool for trusted desktop/CLI workflows alongside MCP `ToolAnnotations` across all 8 tools (`doctype`, `preflight`, `convert`, `convert_url`, `convert_file`, `delete_document`, `fetch`, `search`).
- **OpenAI / Plugin Proxy Enhancements (`plugin_proxy.py`)**: Added strict `Content-Security-Policy` headers, `GET /preflight`, `POST /convert-url`, and `DELETE /documents/{doc_id}` endpoints.
- **ABI-Resilient Claude `.mcpb` Bundle (`scripts/build_claude_bundle.py`)**: Added pure-stdlib runtime ABI guard so Homebrew/OS minor Python version upgrades (e.g., Python 3.14 → 3.15) seamlessly delegate to matching interpreters or `uvx` without `pydantic_core` C-extension errors.

### Security
- **October 2026 eMudhra CA Trust-Store Remediation**: Pinned `certifi>=2026.10.19` (`2026.10.23`), refreshed container `ca-certificates` in `Dockerfile`, hardened PyPI GitHub Actions workflow (`publish-pypi.yml` with OIDC Trusted Publisher primary + token fallback), and standardized all domain references to Equilibrium's `tweekit.io`.

## [1.7.0] - 2026-05-22

### Added
- **Document Cleanup Tool (`delete_document`)**: Added explicit document deletion by `DocId` (`DELETE /api/image/{doc_id}`) with unit and E2E test coverage.
- **Comprehensive End-to-End Test Runner (`scripts/run_full_e2e_test.py`)**: Added multi-format ingestion, conversion, and output verification test harness.
- **OpenAI Codex CLI & MCP Directory Guides**: Added `configs/codex-mcp.yaml`, `docs/mcp-directories.md`, and updated developer tool and submission checklists.
- **Python 3.14 & Credential Resolution Improvements**: Added `tests/test_credential_resolution.py`, `tests/test_fetch_tool.py`, FastMCP `stateless_http` startup optimization, and pytest-asyncio strict compatibility.

## [1.6.1] - 2025-11-23

### Added
- **Claude Desktop `.mcpb` Bundle & CI (`scripts/build_claude_bundle.py`, `build-claude-bundle.yml`)**: Automated building and `@anthropic-ai/mcpb` validation of standalone Claude Desktop extension bundles with embedded branding assets.
- **OpenAI / ChatGPT REST Plugin Proxy (`plugin_proxy.py`)**: Added FastAPI REST proxy running alongside the MCP server in Docker/Cloud Run, serving `/logo.png`, guarded `/assets/{name}` static branding routes, and OpenAPI schema generation.
- **Cloud Run Staging & Production Deployment Automation (`scripts/deploy_cloud_run.sh`)**: Unified container deployment for both MCP streamable HTTP and plugin proxy services across `stage` and `prod` targets, plus stateless Firebase Hosting FastMCP configuration.
- **Recursive E2E Asset Sweep (`scripts/run_mcp_e2e.py`)**: Added directory-tree conversion sweep preserving nested output structure and error/skip audit markers.

## [1.5.0] - 2025-11-06

### Added

#### Core Features
- **Universal Media Conversion**: Support for 400+ file types including images, documents, videos, and professional formats (Adobe Illustrator, Camera RAW, PSD, etc.)
- **MCP Server Implementation**: FastMCP-based streamable HTTP server with full Model Context Protocol compliance
- **Cloud Deployments**: Production-ready deployments on Firebase Hosting and Google Cloud Run

#### MCP Tools
- `doctype`: Query supported file formats and map extensions to document types
- `convert`: Convert base64-encoded documents with transformation options (resize, crop, format change, background fill)
- `convert_url`: Download and convert remote documents via HTTP(S) URLs
- `fetch`: Retrieve content from URLs with automatic content-type detection
- `search`: Perform web searches using DuckDuckGo

#### MCP Resources
- `config://tweekit-version`: TweekIT API version information
- `config://tweekit-mcp-version`: MCP server version (1.5.0)

#### Transformation Capabilities
- **Resize**: Width and height adjustments with automatic aspect ratio preservation
- **Crop**: Coordinate-based cropping with support for negative values (padding)
- **Format Conversion**: Convert between image formats (PNG, JPG, WebP, etc.) and document formats
- **Background Fill**: Hex color background for transparent or padded areas
- **Page Selection**: Extract specific pages from multi-page documents
- **NoRasterize Mode**: Convert text documents directly to PDF without rasterization
- **Alpha Channel Control**: Enable/disable transparency passthrough

#### Client Integrations
- **Claude Desktop**: HTTP transport configuration with manifest
- **ChatGPT MCP**: Compatible with OpenAI MCP tools
- **Cursor IDE**: MCP configuration with environment variable support
- **Continue IDE**: Streamable HTTP transport integration
- **MCP Inspector**: Full tooling support for development and debugging

#### Developer Tools
- **Python Client SDK**: `tweekit_client.py` helper for programmatic access
- **Node.js Quickstart**: Example integration using MCP TypeScript SDK
- **Python Quickstart**: AsyncIO example with FastMCP client
- **Example Assets**: Test files (PNG, DOCX) for validation

#### Documentation
- Comprehensive README with 400+ file type support details
- Integration guides for Claude, ChatGPT, Cursor, and Continue
- Use case examples (employee headshots, KYC photos, social media resizing, document conversion)
- REST API reference and MCP API reference
- Error handling and troubleshooting guide
- Advanced topics (AI pipeline integration, performance tuning, security hardening)
- Integration roadmap for upcoming platform support

#### Testing & CI/CD
- **Test Suite**: pytest-based tests for server tools, configs, plugin proxy, and Claude bundle
- **Smoke Tests**: `test_server.py` for async endpoint validation
- **GitHub Actions**: Automated MCP registry publishing on version tags
- **Deployment Scripts**: 
  - `deploy_firebase.sh`: Firebase Hosting deployment with vendoring
  - `deploy_cloud_run.sh`: Google Cloud Run deployment for stage/prod
  - `run_mcp_e2e.py`: End-to-end MCP testing script

#### Configuration & Environment
- Environment variable support for API keys and secrets
- Sample configuration files for multiple MCP clients
- Docker containerization support
- Firebase Functions ASGI bridge for serverless deployment

#### Security
- API key and secret authentication
- HTTPS-only endpoints
- Short-lived asset storage (20-minute expiry for REST API)
- Stateless processing with automatic cleanup

#### Additional Integration Prep
- ChatGPT plugin proxy (`plugin_proxy.py`)
- Claude bundle builder script (`build_claude_bundle.py`)
- DeepSeek MCP bridge script (`deepseek_mcp_bridge.py`)
- Platform-specific documentation:
  - `docs/chatgpt-plugin.md`
  - `docs/claude-bundle.md`
  - `docs/deepseek-integration.md`
  - `docs/grok-integration.md`
  - `docs/developer-tools.md`

### Infrastructure
- **Firebase Hosting**: Rewrite rules for `/mcp` endpoint routing
- **Google Cloud Run**: Multi-environment support (local, stage, prod)
- **Dependency Management**: uv.lock for reproducible builds
- **Vendored Dependencies**: Firebase Functions package vendoring support

### Documentation Enhancements
- MCP Pulse checklist for registry readiness
- Integration roadmap for OpenAI, Anthropic, xAI, DeepSeek
- Testing guide with integration patterns
- Quickstart guides for multiple platforms
- Development backlog tracking

---

## [Unreleased]

### Planned
- Native Grok integration (pending xAI API release)
- DeepSeek bridge hardening
- Additional IDE integrations (Windsurf, v0, Sourcegraph Cody)
- SDK packaging for PyPI and NPM
- OpenAPI specification for REST API
- Staging environment for pre-release testing

---

**Note**: This is the initial public release of TweekIT MCP Server. Previous development was internal.

For detailed API documentation, visit [https://www.tweekit.io/docs/](https://www.tweekit.io/docs/)

For support, contact: support@tweekit.io
