"""Security regression suite covering DNS-pinned SSRF, dangling-symlink sandbox, credential schemas, and `/mcp/` routing."""
from pathlib import Path

import httpcore
import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

import server
from tests.conftest import tool_fn


def _try_symlink(link: Path, target: Path) -> bool:
    try:
        link.symlink_to(target)
        return True
    except OSError as exc:
        # Windows without Developer Mode raises WinError 1314 on unprivileged symlink creation.
        if getattr(exc, "winerror", None) == 1314:
            return False
        raise


def test_trailing_slash_mcp_initialize_returns_200_without_redirect():
    """Both `/mcp` and `/mcp/` handle MCP `initialize` directly without a 307 redirect."""
    app = server.build_streamable_http_app()
    init_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "witan-probe-regression", "version": "1.0.0"},
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "X-Forwarded-Proto": "https",
    }

    with TestClient(app, base_url="http://mcp.tweekit.io") as client:
        resp_no_slash = client.post("/mcp", json=init_body, headers=headers, follow_redirects=False)
        resp_slash = client.post("/mcp/", json=init_body, headers=headers, follow_redirects=False)

    assert resp_no_slash.status_code == 200
    assert resp_slash.status_code == 200
    assert "location" not in resp_slash.headers


@respx.mock
def test_http_header_credentials_authenticate_mcp_tool_and_reject_partial_headers(monkeypatch):
    """Streamable HTTP requests pass ApiKey/ApiSecret via HTTP headers and never mix partial headers with env."""
    monkeypatch.setenv("TWEEKIT_API_KEY", "operator-env-key")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "operator-env-secret")

    route = respx.get(f"{server.BASE_URL}doctype").mock(
        return_value=Response(200, json={"supported": ["pdf", "png"]})
    )
    app = server.build_streamable_http_app()
    call_body = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "doctype", "arguments": {"extension": "pdf"}},
    }
    full_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "ApiKey": "hdr-key",
        "ApiSecret": "hdr-secret",
    }
    partial_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "ApiKey": "hdr-key-only",
    }

    with TestClient(app, base_url="https://mcp.tweekit.io") as client:
        resp = client.post("/mcp/", json=call_body, headers=full_headers, follow_redirects=False)
        partial_resp = client.post("/mcp/", json=call_body, headers=partial_headers, follow_redirects=False)
        no_hdr_resp = client.post(
            "/mcp/",
            json=call_body,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            follow_redirects=False,
        )

    assert resp.status_code == 200
    assert route.call_count == 1
    upstream_req = route.calls[0].request
    assert upstream_req.headers["apikey"] == "hdr-key"
    assert upstream_req.headers["apisecret"] == "hdr-secret"
    assert partial_resp.status_code == 200
    assert "Incomplete TweekIT HTTP header credentials" in partial_resp.text
    assert no_hdr_resp.status_code == 200
    assert "Missing TweekIT HTTP header credentials" in no_hdr_resp.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_url",
    [
        "http://example.com/file.pdf",
        "file:///etc/passwd",
        "https://localhost/secret.pdf",
        "https://127.0.0.1/secret.pdf",
        "https://169.254.169.254/latest/meta-data/",
        "https://metadata.google.internal/computeMetadata/v1/",
        "https://10.0.0.5/internal.pdf",
        "https://192.168.1.10/router.png",
        "https://100.64.0.1/cgnat.pdf",
        "https://[::1]/loopback.pdf",
        "https://[::ffff:169.254.169.254]/mapped.pdf",
        "https://[64:ff9b::a9fe:a9fe]/nat64-metadata.pdf",
        "https://[2002:7f00:0001::]/sixtofour-loopback.pdf",
        "https://user:pass@example.com/file.pdf",
    ],
)
async def test_ssrf_blocks_insecure_schemes_and_private_targets(monkeypatch, bad_url):
    monkeypatch.setenv("TWEEKIT_API_KEY", "k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "s")

    conv_res = await tool_fn(server.convert_url)(url=bad_url, outfmt="png")
    fetch_res = await tool_fn(server.fetch)(url=bad_url)

    assert "error" in conv_res
    assert "error" in fetch_res


@pytest.mark.asyncio
async def test_dns_rebinding_pinned_backend_never_re_resolves_hostname():
    """Verify `_PinnedPublicDNSBackend` connects strictly to the pre-validated IP, defeating DNS rebinding."""

    class FakeStream(httpcore.AsyncNetworkStream):
        def __init__(self, peer_ip: str, peer_port: int) -> None:
            self._peer = (peer_ip, peer_port)
            self.closed = False

        async def read(self, max_bytes: int, timeout=None) -> bytes:
            return b""

        async def write(self, buffer: bytes, timeout=None) -> None:
            return None

        async def aclose(self) -> None:
            self.closed = True

        async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            return self

        def get_extra_info(self, info: str):
            if info == "server_addr":
                return self._peer
            return None

    class FakeInnerBackend(httpcore.AsyncNetworkBackend):
        def __init__(self, reported_peer_ip: str | None = None) -> None:
            self.connect_calls: list[tuple[str, int]] = []
            self.reported_peer_ip = reported_peer_ip

        async def connect_tcp(self, host: str, port: int, timeout=None, local_address=None, socket_options=None):
            # If httpcore passed the unpinned hostname here, an OS getaddrinfo call could rebind to 169.254.169.254!
            self.connect_calls.append((host, port))
            return FakeStream(self.reported_peer_ip or host, port)

        async def connect_unix_socket(self, path: str, timeout=None, socket_options=None):
            raise RuntimeError("unused")

        async def sleep(self, seconds: float) -> None:
            return None

    inner = FakeInnerBackend()
    pinned = server._PinnedPublicDNSBackend(inner)
    pinned.register("rebind.attacker.example", 443, ["93.184.216.34"])

    stream = await pinned.connect_tcp("rebind.attacker.example", 443)
    assert inner.connect_calls == [("93.184.216.34", 443)]
    assert stream is not None

    # Unregistered hostnames must be refused immediately without DNS resolution
    with pytest.raises(httpcore.ConnectError, match="Refusing unpinned"):
        await pinned.connect_tcp("unregistered.example", 443)

    # Even if an underlying socket reports a private peer_addr, the stream is closed and rejected
    spoofed_inner = FakeInnerBackend(reported_peer_ip="169.254.169.254")
    spoofed_pinned = server._PinnedPublicDNSBackend(spoofed_inner)
    spoofed_pinned.register("rebind.attacker.example", 443, ["93.184.216.34"])
    with pytest.raises(httpcore.ConnectError, match="not a public IP"):
        await spoofed_pinned.connect_tcp("rebind.attacker.example", 443)


@pytest.mark.asyncio
@respx.mock
async def test_ssrf_blocks_redirect_to_metadata_and_disallowed_headers(monkeypatch):
    monkeypatch.setenv("TWEEKIT_API_KEY", "k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "s")

    respx.get("https://example.com/hop").mock(
        return_value=Response(302, headers={"location": "https://169.254.169.254/latest/meta-data/"})
    )
    redirect_res = await tool_fn(server.fetch)(url="https://example.com/hop")
    assert "error" in redirect_res
    assert "Blocked non-public IP" in redirect_res["error"]

    hdr_res = await tool_fn(server.convert_url)(
        url="https://example.com/doc.pdf",
        outfmt="png",
        fetchHeaders={"Metadata-Flavor": "Google"},
    )
    assert "error" in hdr_res
    assert "Disallowed fetchHeader" in hdr_res["error"]

    auth_hdr_res = await tool_fn(server.convert_url)(
        url="https://example.com/doc.pdf",
        outfmt="png",
        fetchHeaders={"Authorization": "Bearer placeholder"},
    )
    assert "error" in auth_hdr_res
    assert "Authorization" in auth_hdr_res["error"]


@pytest.mark.asyncio
@respx.mock
async def test_remote_download_size_limit_enforced(monkeypatch):
    monkeypatch.setenv("TWEEKIT_MAX_DOWNLOAD_BYTES", "64")
    respx.get("https://example.com/big.bin").mock(
        return_value=Response(200, content=b"X" * 256, headers={"content-type": "application/octet-stream"})
    )

    res = await tool_fn(server.fetch)(url="https://example.com/big.bin")
    assert "error" in res
    assert "exceeds maximum allowed size" in res["error"]


@pytest.mark.asyncio
@respx.mock
async def test_convert_file_sandbox_blocks_traversal_dangling_symlinks_dotfiles_and_overwrite(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    monkeypatch.setenv("TWEEKIT_ALLOW_LOCAL_FILES", "1")
    monkeypatch.setenv("TWEEKIT_API_KEY", "k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "s")

    # 0. Missing TWEEKIT_ALLOWED_DIRS must fail closed rather than defaulting to cwd
    monkeypatch.delenv("TWEEKIT_ALLOWED_DIRS", raising=False)
    res_no_dirs = await tool_fn(server.convert_file)(file_path=str(workspace / "a.psd"), outfmt="png")
    assert "error" in res_no_dirs
    assert "TWEEKIT_ALLOWED_DIRS" in res_no_dirs["error"]

    monkeypatch.setenv("TWEEKIT_ALLOWED_DIRS", str(workspace))

    outside_secret = outside / "secret.txt"
    outside_secret.write_text("top-secret")

    # 1. Outside workspace read blocked
    res_outside = await tool_fn(server.convert_file)(file_path=str(outside_secret), outfmt="pdf")
    assert "error" in res_outside
    assert "outside the allowed workspace" in res_outside["error"]

    # 2. Sensitive dotfile (.env) inside workspace blocked
    dotenv_file = workspace / ".env"
    dotenv_file.write_text("FLAG=1")
    res_dotenv = await tool_fn(server.convert_file)(file_path=str(dotenv_file), outfmt="txt")
    assert "error" in res_dotenv
    assert "sensitive" in res_dotenv["error"].lower()

    valid_src = workspace / "image.psd"
    valid_src.write_bytes(b"PSDDATA")
    respx.post(server.BASE_URL).mock(
        return_value=Response(200, content=b"PNG_BYTES", headers={"content-type": "image/png"})
    )

    # 3. Symlink read escape AND dangling-symlink write escape (even with TWEEKIT_ALLOW_OVERWRITE=1!)
    escape_read_link = workspace / "read_link.txt"
    if _try_symlink(escape_read_link, outside_secret):
        res_symlink = await tool_fn(server.convert_file)(file_path=str(escape_read_link), outfmt="pdf")
        assert "error" in res_symlink
        assert "Symbolic links" in res_symlink["error"]

        outside_nonexistent = outside / "escaped_write.png"
        dangling_out_link = workspace / "dangling_out.png"
        assert _try_symlink(dangling_out_link, outside_nonexistent)
        monkeypatch.setenv("TWEEKIT_ALLOW_OVERWRITE", "1")
        res_dangling = await tool_fn(server.convert_file)(
            file_path=str(valid_src),
            outfmt="png",
            output_path=str(dangling_out_link),
        )
        assert "error" in res_dangling
        assert "Symbolic links" in res_dangling["error"]
        assert not outside_nonexistent.exists()
        monkeypatch.delenv("TWEEKIT_ALLOW_OVERWRITE", raising=False)

    # 4. Unsafe executable output extension (.sh) and existing file overwrite blocked
    res_sh = await tool_fn(server.convert_file)(
        file_path=str(valid_src),
        outfmt="png",
        output_path=str(workspace / "exploit.sh"),
    )
    assert "error" in res_sh
    assert "extension" in res_sh["error"].lower()

    existing_out = workspace / "existing.png"
    existing_out.write_bytes(b"ORIGINAL")
    res_overwrite = await tool_fn(server.convert_file)(
        file_path=str(valid_src),
        outfmt="png",
        output_path=str(existing_out),
    )
    assert "error" in res_overwrite
    assert "overwrite" in res_overwrite["error"].lower()
    assert existing_out.read_bytes() == b"ORIGINAL"


@pytest.mark.asyncio
async def test_delete_document_blocks_path_traversal(monkeypatch):
    monkeypatch.setenv("TWEEKIT_API_KEY", "k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "s")

    res = await tool_fn(server.delete_document)(docId="../../admin/purge")
    assert "error" in res
    assert "Invalid docId" in res["error"]


def test_plugin_proxy_ssrf_and_body_credential_exclusion(proxy_app):
    client = TestClient(proxy_app)
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]
    for model_name in ("ConvertRequest", "ConvertUrlRequest"):
        props = schemas[model_name]["properties"]
        assert "apiKey" not in props
        assert "apiSecret" not in props

    resp = client.post(
        "/convert-url",
        json={"url": "http://169.254.169.254/latest/meta-data/", "outfmt": "png"},
        headers={"X-Api-Key": "test-key", "X-Api-Secret": "test-secret"},
    )
    assert resp.status_code == 400


def test_firebase_functions_credentials_reject_partial_headers_and_http_env_fallback(monkeypatch):
    import importlib.util
    import sys
    import types

    ff_mod = types.ModuleType("firebase_functions")
    https_fn_mod = types.ModuleType("firebase_functions.https_fn")
    https_fn_mod.Request = object  # type: ignore[attr-defined]
    https_fn_mod.Response = object  # type: ignore[attr-defined]
    https_fn_mod.on_request = lambda *a, **kw: (lambda fn: fn)  # type: ignore[attr-defined]
    ff_mod.https_fn = https_fn_mod  # type: ignore[attr-defined]
    ff_opts_mod = types.ModuleType("firebase_functions.options")
    ff_opts_mod.set_global_options = lambda **kw: None  # type: ignore[attr-defined]
    wz_mod = types.ModuleType("werkzeug")
    wz_wrappers_mod = types.ModuleType("werkzeug.wrappers")
    wz_wrappers_mod.Response = object  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "firebase_functions", ff_mod)
    monkeypatch.setitem(sys.modules, "firebase_functions.https_fn", https_fn_mod)
    monkeypatch.setitem(sys.modules, "firebase_functions.options", ff_opts_mod)
    monkeypatch.setitem(sys.modules, "werkzeug", wz_mod)
    monkeypatch.setitem(sys.modules, "werkzeug.wrappers", wz_wrappers_mod)

    spec = importlib.util.spec_from_file_location("functions_main_mod", Path("functions/main.py"))
    assert spec is not None and spec.loader is not None
    fn_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fn_mod)

    monkeypatch.setenv("TWEEKIT_API_KEY", "env-k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "env-s")
    monkeypatch.delenv("TWEEKIT_ALLOW_ENV_CREDENTIALS_OVER_HTTP", raising=False)

    # No headers -> must NOT silently use env credentials over HTTP
    monkeypatch.setattr(fn_mod, "get_http_headers", lambda **_: {})
    with pytest.raises(RuntimeError, match="Missing TweekIT HTTP header credentials"):
        fn_mod._resolve_request_credentials()

    # Partial headers -> must NOT mix header key with env secret
    monkeypatch.setattr(fn_mod, "get_http_headers", lambda **_: {"apikey": "only-key"})
    with pytest.raises(RuntimeError, match="Incomplete TweekIT HTTP header credentials"):
        fn_mod._resolve_request_credentials()

    # Complete header pair -> succeeds
    monkeypatch.setattr(fn_mod, "get_http_headers", lambda **_: {"apikey": "hk", "apisecret": "hs"})
    assert fn_mod._resolve_request_credentials() == ("hk", "hs")
