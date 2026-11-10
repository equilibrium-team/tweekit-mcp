# On-Premises & Localhost Miner Renderery Specification

> **Document Role:** Last-Mile Integration & Architecture Specification for `tweekit-mcp` + **New Miner Installation Initiative**  
> **Version:** `1.8.3` (`2026-11-10`)  
> **Organization:** AMPS dba Equilibrium / CPUcoin Content Generation Network (CGN)  
> **Repositories Covered:**  
> - `equilibrium-team/tweekit-mcp` (MCP Server, Python SDK, AI Hub Preflight Router, REST Plugin Proxy)  
> - `equilibrium-team/tweekit-api` (`TweekIT_API` .NET 9 Gateway & `TweekIT.ms` MediaScript Controller)  
> - `equilibrium-team/Devel` (`CGNMiner` / MediaRich CORE™ V7 Engine & `MediaGen` HTTP Renderery Daemon)

---

## 1. Executive Overview

`tweekit-mcp` supports two interchangeable execution topologies for normalizing, preflighting, and converting 450+ legacy, enterprise, CAD, RAW, vector, and Office document formats into AI-ready payloads (`png`, `webp`, `pdf`, `txt`):

1. **Cloud CGN Mode (Default)**:
   - `tweekit-mcp` (or `https://mcp.tweekit.io/mcp`) routes conversion requests to `https://dapp.tweekit.io/tweekit/api/image/`, which dispatches workloads across Equilibrium's globally distributed Tier 1 CPUcoin Content Generation Network (CGN) Miner Renderery nodes.
2. **On-Premises / Localhost Miner Renderery Mode (Zero-Cloud-Egress / Air-Gapped)**:
   - For regulated enterprises, confidential local workspaces, developer workstations, and edge appliances provisioned under the **New Miner Installation Initiative**, the **Miner Renderery** is installed directly on-premises or on `localhost`.
   - `tweekit-mcp` connects over loopback (`http://127.0.0.1:16377/api/image/` or `http://127.0.0.1:5000/api/image/`) with `TWEEKIT_LOCAL_ONLY=1`.
   - **100% of file bytes stay on the local host or private LAN** — eliminating third-party cloud egress while preserving full tool, SDK, and MCP compatibility.

---

## 2. End-to-End Architecture & Three-Tier Local Stack

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ AI Host / Agent Surface (Claude Desktop, Cursor, ChatGPT, Antigravity, SDK)   │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │ MCP (stdio or 127.0.0.1:8080/mcp)
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Tier 1: tweekit-mcp (v1.8.2+) — FastMCP Server & Python SDK                   │
│   • Preflight router (450+ extensions -> AI-ready format recommendation)      │
│   • Opt-in O_NOFOLLOW workspace sandbox (TWEEKIT_ALLOWED_DIRS)                │
│   • Zero-egress enforcement (TWEEKIT_LOCAL_ONLY=1 / --local-miner)            │
│   • Runtime introspection resource: config://tweekit-runtime-mode             │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │ HTTP Loopback (127.0.0.1:16377 or :5000)
                                        │ Path: /api/image/
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Tier 2: Local TweekIT API Gateway (TweekIT_API — ASP.NET Core 9.0)            │
│   • Build Profile: Release_CloudMaitrix or On-Prem (NOAUTH;NODB optional)     │
│   • Endpoints: GET /api/image/version, GET|POST /api/image/doctype,           │
│     POST /api/image (inline base64 DocData + DocDataType), DELETE /{docId}    │
│   • Stages ephemeral job files into NativePathToStorage (/tmp/tweekitdata)    │
│     with path-traversal validation & immediate post-conversion cleanup        │
└───────────────────────────────────────┬────────────────────────────────────────┘
                                        │ HTTP Loopback (127.0.0.1:8088)
                                        │ Path: /mgen/TweekIT.ms?f=GetImage&...
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Tier 3: Miner Renderery Engine (CGNMiner / MediaRich CORE™ V7 + TweekIT.ms)   │
│   • CMake Preset: <platform>-cgnminer-release (macOS arm64, Linux, Windows)   │
│   • MediaGen HTTP listener on 127.0.0.1:8088 executing TweekIT.ms (v0.13)     │
│   • 450+ format PipeDevices + PDF intermediate pipeline + AIMediaEngine       │
│   • Emits X-CPUCoinMiner-* diagnostic, dimension, page-count, & GPU headers   │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Port, Endpoint & Protocol Contract Matrix

| Component | Default Bind Address | Canonical Base URL / Path | Purpose & Protocol Notes |
| --- | --- | --- | --- |
| **`tweekit-mcp` (HTTP mode)** | `127.0.0.1:8080` | `http://127.0.0.1:8080/mcp` | Local Streamable HTTP MCP endpoint (`/mcp` and `/mcp/` normalized in-place). |
| **`tweekit-mcp` (`stdio` mode)** | Process `stdin`/`stdout` | `tweekit-mcp --transport stdio --local-miner` | Standard local desktop agent transport (Claude Desktop, Cursor, Antigravity). |
| **Miner Renderery API Gateway (Windows / IIS Express / Appliance)** | `127.0.0.1:16377` | `http://127.0.0.1:16377/api/image/` | Canonical `LOCAL_MINER_BASE_URL` in `server.py` and `launchSettings.json`. |
| **Miner Renderery API Gateway (Linux / macOS / Container Kestrel)** | `127.0.0.1:5000` (or `:5025`) | `http://127.0.0.1:5000/api/image/` | `Release_CloudMaitrix` (`NOAUTH;NODB`) Kestrel profile (`LOCAL_MINER_KESTREL_URL`). |
| **MediaGen Renderery Daemon (`CGNMiner` + `TweekIT.ms`)** | `127.0.0.1:8088` | `http://127.0.0.1:8088/mgen/TweekIT.ms` | Internal MediaRich script engine (`CGNServerURL` in `appsettings.*.json`). |

### 3.1 REST Contract Between `tweekit-mcp` and the Miner Renderery Gateway (`TweekIT_API`)

All requests from `tweekit-mcp` to `TWEEKIT_API_BASE_URL` use the following wire contract:

1. **Health & Version Handshake (`GET {BASE_URL}version`)**:
   - **Request**: `GET http://127.0.0.1:16377/api/image/version` (anonymous allowed).
   - **Response**: `200 OK` (`text/plain`), e.g., `1.0.0.74`.
   - **Exposed via MCP Resource**: `config://tweekit-version`.

2. **Supported Format & Document Type Discovery (`GET {BASE_URL}doctype?extension={ext}`)**:
   - **Request**: `GET http://127.0.0.1:16377/api/image/doctype?extension=psd` (or `extension=*` for all formats) with headers `ApiKey` and `ApiSecret`.
   - **Upstream Dispatch**: `TweekIT_API` invokes `POST http://127.0.0.1:8088/mgen/TweekIT.ms?f=FileTypeFromExtension&nc=1&ext=psd` with header `X-CGN-Internal-RequestedQueueType: best`.
   - **Response**: `200 OK` (`application/json`), e.g., `{"docType": "Photoshop", "extensions": [".psd"]}` or an array of all registered `Media.getFileFormats()` entries.

3. **Synchronous Stateless Conversion (`POST {BASE_URL}`)**:
   - **Request**: `POST http://127.0.0.1:16377/api/image/` with headers `ApiKey`, `ApiSecret`, and JSON body:
     ```json
     {
       "Fmt": "png",
       "Width": 0,
       "Height": 0,
       "X1": 0,
       "Y1": 0,
       "X2": 0,
       "Y2": 0,
       "Bg": 0,
       "Alpha": true,
       "Page": 1,
       "NoRasterize": false,
       "DocDataType": "psd",
       "DocData": "<base64-encoded-document-bytes>"
     }
     ```
   - **Upstream Execution (`ImageController.FinalImagePostAsync` -> `TweekIT.ms:GetImage`)**:
     1. `TweekIT_API` validates `DocDataType` (`[^A-Za-z0-9]` stripped), decodes `DocData`, writes the temporary file to `{NativePathToStorage}/{UserId}/{WorkFolderDocId}/document.{ext}` (enforcing `StartsWith(rootPath)` path-traversal protection), and constructs the `GetImage` query.
     2. `TweekIT.ms` ingests the staged document into its isolated job temp directory (`req.getJobTempDir()`), converts Office documents (`MSWord`, `MSExcel`, `PowerPoint`, `OODraw`) through an intermediate PDF when needed, renders or crops/scales the requested page (`scaleImage()`), streams the binary output back, and clears the job cache (`docFile.clearCached()`).
     3. `TweekIT_API` immediately deletes `{ nativeWorkFolderPath }` (`Directory.Delete(nativeWorkFolderPath, true)`) before returning the HTTP response stream.
   - **Response Headers Forwarded from Miner Renderery**:
     - `X-CPUCoinMiner-TweekITScriptVer`: `"0.13"`
     - `X-CPUCoinMiner-Timing`: `"<xferMs>/<processMs>/<totalMs>"`
     - `X-CPUCoinMiner-PageCount`: total pages/frames when `gi=1` or PNG metadata inspected
     - `X-CPUCoinMiner-OrigImageWidth` / `X-CPUCoinMiner-OrigImageHeight`
     - `X-CPUCoinMiner-ImageWidth` / `X-CPUCoinMiner-ImageHeight`
     - `X-CPUCoinMiner-Error` / `X-TweekIT-API-Error`: surfaced automatically by `server._extract_error_details()`

---

## 4. `tweekit-mcp` Environment & CLI Configuration for On-Premises Miner Renderery

`tweekit-mcp` `v1.8.2` introduces first-class environment variables and CLI flags for local and on-premises Miner Renderery deployments:

| Variable / Flag | Default | Description |
| --- | --- | --- |
| `TWEEKIT_API_BASE_URL` / `--api-base-url` | `https://dapp.tweekit.io/tweekit/api/image/` | Target TweekIT REST API endpoint. Set to `http://127.0.0.1:16377/api/image/` (Windows/IIS Express) or `http://127.0.0.1:5000/api/image/` (Linux/macOS/Docker `Release_CloudMaitrix`) for localhost Miner Renderery execution. |
| `TWEEKIT_MINER_LOCAL` / `--local-miner` | `0` | When `1` (or `--local-miner`), automatically switches the default API base URL to `http://127.0.0.1:16377/api/image/` **and enables `TWEEKIT_LOCAL_ONLY=1` zero-egress mode by default** (unless `TWEEKIT_LOCAL_ONLY=0` is explicitly set). Likewise, `TweekitDirectClient(local_miner=True)` blocks outbound `convert_url` fetches by default unless `allow_remote_fetch=True` or `TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1` is passed. |
| `TWEEKIT_LOCAL_ONLY` | `0` (`1` when `TWEEKIT_MINER_LOCAL=1` or `local_miner=True`) | **Zero-Cloud-Egress Mode.** When active: (a) requires `TWEEKIT_API_BASE_URL` to target `localhost` (`127.0.0.1`, `::1`, `localhost`) or an allowlisted host in `TWEEKIT_ONPREM_HOSTS`, rejecting any external cloud URL or `0.0.0.0`/`::` wildcard bind address; and (b) disables outbound internet tools (`convert_url`, `fetch`, `search`) unless `TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1`. |
| `TWEEKIT_REQUIRE_LOCAL_MINER_FOR_FILES` | `0` | When `1`, `convert_file` refuses to run unless `TWEEKIT_API_BASE_URL` points to a loopback or `TWEEKIT_ONPREM_HOSTS` Miner Renderery — allowing hybrid setups where remote URLs can use Cloud CGN while local disk files are strictly restricted to localhost Miner Renderery processing. |
| `TWEEKIT_ONPREM_HOSTS` | `""` | Comma-separated list of private LAN hostnames or IPs (e.g., `miner01.corp.internal,10.20.30.40`) permitted as on-premises Miner Renderery endpoints under `TWEEKIT_LOCAL_ONLY=1` or `http://`. |
| `TWEEKIT_MINER_NOAUTH` | `0` | When `1` on a local `stdio` server targeting a loopback/on-prem Miner Renderery compiled with `NOAUTH;NODB` (`Release_CloudMaitrix`), allows conversions without requiring cloud portal `TWEEKIT_API_KEY` / `TWEEKIT_API_SECRET`. |
| `TWEEKIT_ALLOW_LOCAL_FILES` | `0` | Must be set to `1` on local `stdio` servers to enable `convert_file` (always disabled over HTTP). |
| `TWEEKIT_ALLOWED_DIRS` | `""` | Path-separator (`:` on macOS/Linux, `;` on Windows) list of workspace directories that `convert_file` is allowed to read/write (with `lstat` + `O_NOFOLLOW` symlink rejection). |

---

## 5. Reference Client Configurations (Localhost Miner Renderery)

### 5.1 Claude Desktop / Cursor / Antigravity (`stdio` + Local Miner Renderery, Zero Cloud Egress)

```json
{
  "mcpServers": {
    "tweekit-local-miner": {
      "command": "uvx",
      "args": [
        "--from",
        "tweekit>=1.8.3",
        "tweekit-mcp",
        "--transport",
        "stdio",
        "--local-miner"
      ],
      "env": {
        "TWEEKIT_API_BASE_URL": "http://127.0.0.1:16377/api/image/",
        "TWEEKIT_LOCAL_ONLY": "1",
        "TWEEKIT_MINER_NOAUTH": "1",
        "TWEEKIT_ALLOW_LOCAL_FILES": "1",
        "TWEEKIT_ALLOWED_DIRS": "/Users/operator/Documents/workspace"
      }
    }
  }
}
```

### 5.2 Python SDK (`TweekitDirectClient` Targeting Localhost Miner Renderery)

```python
import asyncio
from pathlib import Path
from tweekit import TweekitDirectClient

async def main() -> None:
    # Connects directly to http://127.0.0.1:16377/api/image/
    async with TweekitDirectClient(
        local_miner=True,
        api_key="local-miner",
        api_secret="local-miner",
    ) as miner:
        print("Miner API version:", await miner.version())
        plan = miner.preflight("engineering-drawing.dwg", target_provider="claude")
        print("Preflight:", plan)
        result = await miner.convert_file(
            Path("/Users/operator/Documents/workspace/engineering-drawing.dwg"),
            outfmt=plan["recommended_outfmt"],
        )
        print("Converted:", type(result))

asyncio.run(main())
```

---

## 6. Last-Mile Provisioning Checklist for the New Miner Installation Initiative

As the **New Miner Installation Initiative** packages the standalone Miner Renderery installer (Windows Service, macOS LaunchDaemon / `.pkg`, Linux `systemd` / OCI Container), the installer must satisfy the following five last-mile requirements so `tweekit-mcp` attaches with zero manual configuration:

1. **Build & Bundle Both Local Tiers**:
   - **Tier 3 (`CGNMiner` / MediaGen)**: Build from `equilibrium-team/Devel` using the `CGNMiner` CMake preset (`macos-arm64-cgnminer-release`, `linux-x64-cgnminer-release`, or `windows-x64-cgnminer-release`) and stage `TweekIT.ms` (`ThisScriptVersion = "0.13"`) under `/mgen/TweekIT.ms` listening on `127.0.0.1:8088`.
   - **Tier 2 (`TweekIT_API` Local Gateway)**: Build `TweekIT_API.csproj` with `-c Release_CloudMaitrix` (`DefineConstants: NOAUTH;NODB`) so the local gateway runs statelessly without SQL Server or remote Identity Server dependencies.
2. **Storage Protocol Alignment (`DAppStorageUrl` vs. `TweekIT.ms` Line 44)**:
   - In `TweekIT.ms` line 44, `GetImage()` currently checks `if (srcDocUrl && srcDocUrl.substr(0, 4) !== "http")` while `appsettings.Release_CloudMaitrix.json` sets `"DAppStorageUrl": "twkit:"`.
   - **Installer Requirement**: Either:
     - Configure the local `TweekIT_API` static file middleware to serve `NativePathToStorage` (`/tmp/tweekitdata`) on loopback `http://127.0.0.1:16377/tstore` and set `"DAppStorageUrl": "http://127.0.0.1:16377/tstore"`, **OR**
     - Permit the `twkit:` MediaRich VFS mount prefix in `TweekIT.ms` (`srcDocUrl.substr(0, 4) !== "http" && srcDocUrl.substr(0, 6) !== "twkit:"`) mapped to `/tmp/tweekitdata`.
3. **Standardize Loopback-Only Listener Binding (`127.0.0.1:16377` Primary, `127.0.0.1:5000` Kestrel Alias — Never Wildcard `0.0.0.0`)**:
   - Because `Release_CloudMaitrix` builds with `NOAUTH;NODB`, the local `TweekIT_API` listener **must bind strictly to loopback (`http://127.0.0.1:16377` or `http://127.0.0.1:5000`)**, never `http://0.0.0.0:5000` on a host network interface (`TweekIT_API/appsettings.Release_CloudMaitrix.json` is set to `"http://127.0.0.1:5000"` as of `equilibrium-team/tweekit-api@6727c59`).
   - When deploying `Release_CloudMaitrix` inside a container that overrides `ASPNETCORE_URLS=http://0.0.0.0:5000` for container bridge networking, publish the host port strictly on loopback (`-p 127.0.0.1:5000:5000`).
   - Always verify the effective listener on the host (`lsof -nP -iTCP:5000 -sTCP:LISTEN` on macOS, `ss -tlnp 'sport = :5000'` on Linux, or `Get-NetTCPConnection -LocalPort 5000,16377` on Windows) and confirm non-loopback interfaces cannot reach the port before treating the installation as isolated.
4. **Startup Readiness Probe**:
   - Verify the local Miner Renderery installation by probing:
     1. `GET http://127.0.0.1:16377/api/image/version` → expects `200 OK` (`1.0.0.74+`).
     2. `GET http://127.0.0.1:16377/api/image/doctype?extension=pdf` → expects `200 OK` JSON (`{"docType": "PDF", ...}`), proving `TweekIT_API` -> `MediaGen (127.0.0.1:8088/mgen/TweekIT.ms)` round-trip health.
5. **Auto-Register `tweekit-mcp` in Local AI Hosts**:
   - Have the New Miner Installer write or update the `tweekit-local-miner` MCP server entry (`--local-miner` / `TWEEKIT_LOCAL_ONLY=1`) and verify `config://tweekit-runtime-mode` reports `"execution_mode": "onprem-miner-renderery"` and `"local_only_zero_egress": true`.
