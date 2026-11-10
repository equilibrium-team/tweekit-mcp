# Security Policy & Architecture (`tweekit-mcp`)

## Supported Versions

| Version | Supported | Notes |
| --- | --- | --- |
| `1.8.2` | ✅ Yes | Current release — zero-CVE supply chain (`fastmcp>=4.1.6`), connect-time DNS IP pinning, `O_NOFOLLOW` workspace sandbox, credential-free tool schemas, and On-Premises / Localhost Miner Renderery zero-egress mode (`TWEEKIT_LOCAL_ONLY=1`). |
| `1.8.1` | ✅ Yes | Security hardening & `/mcp/` trailing-slash normalization release. |
| `< 1.8.1` | ❌ No | Upgrade to `tweekit>=1.8.2` (`pip install -U tweekit`). |

## Reporting a Vulnerability

Please report security issues privately to **AMPS dba Equilibrium Security**:

- **Email**: [support@tweekit.io](mailto:support@tweekit.io) (subject: `[SECURITY] tweekit-mcp`)
- **GitHub Security Advisories**: [Report a vulnerability](https://github.com/equilibrium-team/tweekit-mcp/security/advisories/new)

We acknowledge reports within 24 hours and publish coordinated fixes with signed PyPI OIDC provenance attestations (PEP 740).

---

## Defense-in-Depth Security Controls

### 1. Credential-Free MCP Tool Schemas & Atomic Transport Authentication
- **Zero Secrets in LLM Prompts**: None of the MCP tools (`doctype`, `preflight`, `convert`, `convert_url`, `convert_file`, `delete_document`, `fetch`, `search`) or REST proxy models (`ConvertRequest`, `ConvertUrlRequest`) accept `apiKey` or `apiSecret` in tool arguments or JSON request bodies.
- **Transport-Level Auth**:
  - **Streamable HTTP (`https://mcp.tweekit.io/mcp`)**: Credentials must be supplied atomically via `ApiKey` and `ApiSecret` HTTP request headers. Partial headers are rejected, and server environment credentials are never silently used on unauthenticated HTTP calls (`TWEEKIT_ALLOW_ENV_CREDENTIALS_OVER_HTTP=0` by default).
  - **Local `stdio`**: Credentials are read from `TWEEKIT_API_KEY` and `TWEEKIT_API_SECRET` environment variables (or omitted when `TWEEKIT_MINER_NOAUTH=1` targets a loopback `NOAUTH;NODB` Miner Renderery).

### 2. Zero-Cloud-Egress Mode via On-Premises / Localhost Miner Renderery (`TWEEKIT_LOCAL_ONLY=1` / `TWEEKIT_MINER_LOCAL=1` / `local_miner=True`)
For regulated, confidential, or air-gapped workloads where local documents must never be uploaded to an external cloud endpoint (`dapp.tweekit.io`), `tweekit-mcp` supports **On-Premises / Localhost Miner Renderery** execution:
- Point `TWEEKIT_API_BASE_URL` to a local Miner Renderery instance (`http://127.0.0.1:16377/api/image/` or `http://127.0.0.1:5000/api/image/`), pass `--local-miner` on the CLI, set `TWEEKIT_MINER_LOCAL=1`, or initialize `TweekitDirectClient(local_miner=True)`.
- Enabling `TWEEKIT_MINER_LOCAL=1` or `TweekitDirectClient(local_miner=True)` **automatically enforces `TWEEKIT_LOCAL_ONLY=1` zero-egress mode by default** (unless `TWEEKIT_LOCAL_ONLY=0` or `allow_remote_fetch=True` / `TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1` is explicitly configured):
  - Enforces that `TWEEKIT_API_BASE_URL` targets `localhost` (`127.0.0.1`, `::1`, `localhost`) or an explicitly allowlisted internal node in `TWEEKIT_ONPREM_HOSTS`, and rejects wildcard bind addresses (`0.0.0.0`, `::`). Note that `TWEEKIT_ONPREM_HOSTS` matches operator-configured hostnames/IPs directly and permits plain `http://` transport (including `ApiKey`/`ApiSecret` headers when configured) to those trusted LAN Miner Renderery nodes; only add hosts on trusted private networks.
  - Rejects any configuration that would send base64 payloads to an external host.
  - Disables outbound internet tools (`convert_url`, `fetch`, `search`) by default unless `TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1` (or `allow_remote_fetch=True` in `TweekitDirectClient`) is explicitly enabled.
  - **Loopback Listener Requirement for `NOAUTH;NODB` Gateways**: In `equilibrium-team/tweekit-api` (`6727c59`), `TweekIT_API/appsettings.Release_CloudMaitrix.json` binds Kestrel strictly to `http://127.0.0.1:5000` (not `0.0.0.0:5000`). Operators deploying containerized or custom on-premises `NOAUTH;NODB` gateways must verify the effective host listener (`lsof -nP -iTCP:5000 -sTCP:LISTEN` / `ss -tlnp`) and ensure non-loopback interfaces cannot reach unauthenticated endpoints.
- See [`docs/onprem-miner-renderery-spec.md`](docs/onprem-miner-renderery-spec.md) for the complete architecture and installation specification.

### 3. Opt-In Local Filesystem Sandbox (`convert_file`)
- **Disabled by Default (`TWEEKIT_ALLOW_LOCAL_FILES=0`)**: Local filesystem access is off by default and unconditionally disabled whenever the server handles Streamable HTTP requests.
- **Explicit Workspace Confinement (`TWEEKIT_ALLOWED_DIRS`)**: When `TWEEKIT_ALLOW_LOCAL_FILES=1` is enabled on a local `stdio` server, `TWEEKIT_ALLOWED_DIRS` must explicitly list one or more non-root workspace directories.
- **Symlink & TOCTOU Protection (`lstat` + `O_NOFOLLOW`)**: Both read and write paths reject symlinks on every path component via `Path.is_symlink()` (`lstat`) and open files with `os.O_NOFOLLOW` (plus `os.O_EXCL` on writes unless `TWEEKIT_ALLOW_OVERWRITE=1`), preventing symlink-swap races and dangling-symlink write escapes.
- **Sensitive Path & Extension Blocking**: Dotfiles and credential directories (`.env*`, `.ssh`, `.aws`, `.gnupg`, `.kube`, `.docker`, `.git`, `.config`, `.vscode`, `.idea`, `.github`, `.claude`, `.cursor`, `.gemini`, private keys) and executable output extensions (`.sh`, `.py`, `.js`, `.exe`, `.dll`, etc.) are blocked.

### 4. Connect-Time DNS IP Pinning & SSRF Protection (`convert_url`, `fetch`)
- **HTTPS-Only**: Only `https://` URLs without embedded credentials are permitted.
- **Connect-Time IP Pinning (`_PinnedPublicDNSBackend`)**: Every hostname is resolved and validated before connect and on each redirect hop (`MAX_REDIRECT_HOPS = 5`). The underlying `httpcore.AsyncNetworkBackend` connects directly to the pre-validated public IP and verifies `server_addr` post-connect, eliminating DNS-rebinding TOCTOU attacks.
- **Comprehensive Address Filtering**: Blocks loopback (`127.0.0.0/8`, `::1`), RFC 1918 private networks, link-local and cloud metadata (`169.254.0.0/16`, `fe80::/10`, `metadata.google.internal`), CGNAT (`100.64.0.0/10`), and IPv6 transition prefixes (`::ffff:0:0/96`, `64:ff9b::/96` NAT64, `2002::/16` 6to4, `2001::/32` Teredo).
- **Header Allowlist & Streaming Cap**: `fetchHeaders` is restricted to 7 non-credential headers (`Accept`, `Accept-Language`, `Cache-Control`, `If-Modified-Since`, `If-None-Match`, `Range`, `User-Agent`), and downloads are capped at `25 MiB` (`TWEEKIT_MAX_DOWNLOAD_BYTES`).

### 5. Supply Chain & Provenance Attestation
- Locked with `uv.lock` (`fastmcp>=4.1.6`, `mcp>=2.3.0`, `fastapi>=0.162.2`, `httpx>=0.28.1`, `httpcore>=1.0.9`, `starlette>=1.7.0` (`1.10.0` on Python 3.11+), `uvicorn>=0.54.0`, `certifi>=2026.10.23`) and audited via `pip-audit` (`0` known vulnerabilities).
- Published to PyPI via GitHub Actions OIDC Trusted Publishing with cryptographic **Sigstore PEP 740 provenance attestations**.
