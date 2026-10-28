import asyncio
from pathlib import Path

import pytest
import respx

from clients.python import tweekit_client


class DummyResult:
    def __init__(self, data=None, structured=None, content=None, is_error=False):
        self.data = data
        self.structured_content = structured
        self.content = content or []
        self.is_error = is_error


class DummyClient:
    def __init__(self, url):
        self.url = url
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def list_tools(self):
        return []

    async def call_tool(self, name, payload):
        self.calls.append((name, payload))
        return DummyResult(data={"status": "ok", "tool": name})


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    monkeypatch.setattr(tweekit_client, "Client", DummyClient)


def test_convert_file(tmp_path, monkeypatch):
    input_path = tmp_path / "input.txt"
    input_path.write_text("hello")

    client = tweekit_client.TweekitClient(
        server_url="https://mcp.test/mcp",
        api_key="key",
        api_secret="secret",
    )

    async def runner():
        async with client:
            result = await client.convert_file(input_path, outfmt="txt")
            calls = list(client._client.calls)
        return result, calls

    result, calls = asyncio.run(runner())

    assert result["status"] == "ok"
    assert calls[-1][0] == "convert"
    assert calls[-1][1]["bgColor"] == ""


def test_convert_url(monkeypatch):
    client = tweekit_client.TweekitClient(
        server_url="https://mcp.test/mcp",
        api_key="key",
        api_secret="secret",
    )

    async def runner():
        async with client:
            result = await client.convert_url(
                url="https://example.com/file.png",
                outfmt="webp",
                inext="png",
                width=42,
                height=84,
                fetch_headers={"Authorization": "Bearer token"},
            )
            calls = list(client._client.calls)
        return result, calls

    result, calls = asyncio.run(runner())

    assert result["status"] == "ok"
    name, payload = calls[-1]
    assert name == "convert_url"
    assert payload["inext"] == "png"
    assert payload["width"] == 42
    assert payload["fetchHeaders"] == {"Authorization": "Bearer token"}


def test_missing_credentials_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("TWEEKIT_API_KEY", raising=False)
    monkeypatch.delenv("TWEEKIT_API_SECRET", raising=False)

    doc = tmp_path / "doc.txt"
    doc.write_text("hello")

    client = tweekit_client.TweekitClient(server_url="https://mcp.test/mcp")

    async def runner():
        async with client:
            await client.convert_file(doc, outfmt="txt")

    with pytest.raises(RuntimeError):
        asyncio.run(runner())


def test_tweekit_mcp_package_exports_and_batch_convert(tmp_path):
    import tweekit_mcp

    import tweekit
    assert tweekit.__version__ == "1.8.0"
    assert tweekit.TweekitClient is tweekit_mcp.TweekitClient
    assert tweekit_mcp.__version__ == "1.8.0"
    assert tweekit_mcp.__author__ == "AMPS dba Equilibrium"
    assert "psd" in tweekit_mcp.EXTENSIVE_SUPPORTED_EXTENSIONS

    doc = tmp_path / "sheet.xls"
    doc.write_bytes(b"XLSDATA")

    client = tweekit_mcp.TweekitClient(
        server_url="https://mcp.test/mcp",
        api_key="key",
        api_secret="secret",
    )

    async def runner():
        async with client:
            dt = await client.doctype("pdf")
            pf = await client.preflight("photo.cr2", target_provider="claude")
            batch = await client.batch_convert([
                {"path": doc, "outfmt": "pdf"},
                {"url": "https://example.com/scan.tif", "outfmt": "png"},
                {"data": b"RAWBYTES", "inext": "bmp", "outfmt": "webp"},
            ])
            del_res = await client.delete_document("doc-123")
            calls = list(client._client.calls)
        return dt, pf, batch, del_res, calls

    dt, pf, batch, del_res, calls = asyncio.run(runner())
    assert dt["tool"] == "doctype"
    assert pf["tool"] == "preflight"
    assert len(batch) == 3
    assert del_res["tool"] == "delete_document"
    assert calls[0] == ("doctype", {"extension": "pdf", "apiKey": "key", "apiSecret": "secret"})


@pytest.mark.asyncio
@respx.mock
async def test_tweekit_direct_client():
    import respx
    from httpx import Response
    import server
    from tweekit_mcp import TweekitDirectClient

    respx.post(server.BASE_URL).mock(
        return_value=Response(200, json={"status": "converted_direct"})
    )

    async with TweekitDirectClient(api_key="k", api_secret="s") as api:
        info = api.preflight("deck.pptx", target_provider="claude")
        assert info["recommended_outfmt"] == "pdf"
        res = await api.convert_bytes(b"PPTXDATA", inext="pptx", outfmt="pdf")
        assert res == {"status": "converted_direct"}

