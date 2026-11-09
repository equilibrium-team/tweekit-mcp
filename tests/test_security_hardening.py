"""Security regression suite covering SSRF, local sandbox confinement, credential schemas, and `/mcp/` routing."""
from pathlib import Path

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

import server
from tests.conftest import tool_fn


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
def test_http_header_credentials_authenticate_mcp_tool(monkeypatch):
    """Streamable HTTP requests pass ApiKey/ApiSecret via HTTP headers with zero tool-arg secrets."""
    monkeypatch.delenv("TWEEKIT_API_KEY", raising=False)
    monkeypatch.delenv("TWEEKIT_API_SECRET", raising=False)

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
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "ApiKey": "hdr-key",
        "ApiSecret": "hdr-secret",
    }

    with TestClient(app, base_url="https://mcp.tweekit.io") as client:
        resp = client.post("/mcp/", json=call_body, headers=headers, follow_redirects=False)

    assert resp.status_code == 200
    assert route.called
    upstream_req = route.calls[0].request
    assert upstream_req.headers["apikey"] == "hdr-key"
    assert upstream_req.headers["apisecret"] == "hdr-secret"


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

    # Metadata-Flavor and Authorization headers from LLM tool calls must be rejected
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
        fetchHeaders={"Authorization": "Bearer secret-token"},
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
async def test_convert_file_sandbox_blocks_traversal_symlinks_dotfiles_and_overwrite(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()

    monkeypatch.setenv("TWEEKIT_ALLOW_LOCAL_FILES", "1")
    monkeypatch.setenv("TWEEKIT_ALLOWED_DIRS", str(workspace))
    monkeypatch.setenv("TWEEKIT_API_KEY", "k")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "s")

    outside_secret = outside / "secret.txt"
    outside_secret.write_text("top-secret")

    # 1. Outside workspace read blocked
    res_outside = await tool_fn(server.convert_file)(file_path=str(outside_secret), outfmt="pdf")
    assert "error" in res_outside
    assert "outside the allowed workspace" in res_outside["error"]

    # 2. Symlink escaping workspace blocked
    escape_link = workspace / "link.txt"
    escape_link.symlink_to(outside_secret)
    res_symlink = await tool_fn(server.convert_file)(file_path=str(escape_link), outfmt="pdf")
    assert "error" in res_symlink
    assert "Symbolic links" in res_symlink["error"]

    # 3. Sensitive dotfile (.env) inside workspace blocked
    dotenv_file = workspace / ".env"
    dotenv_file.write_text("SECRET=1")
    res_dotenv = await tool_fn(server.convert_file)(file_path=str(dotenv_file), outfmt="txt")
    assert "error" in res_dotenv
    assert "sensitive" in res_dotenv["error"].lower()

    # 4. Unsafe executable output extension (.sh) and existing file overwrite blocked
    valid_src = workspace / "image.psd"
    valid_src.write_bytes(b"PSDDATA")
    respx.post(server.BASE_URL).mock(
        return_value=Response(200, content=b"PNG_BYTES", headers={"content-type": "image/png"})
    )

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
