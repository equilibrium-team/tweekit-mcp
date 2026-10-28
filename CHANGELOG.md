# Changelog

All notable changes to the TweekIT MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
