import base64
import json

import pytest
import respx
from httpx import Response

import server


@pytest.mark.asyncio
@respx.mock
async def test_convert_url_infers_extension_and_calls_convert():
    remote_url = "https://example.com/download?id=123"
    payload_bytes = b"PNGDATA"

    fetch_route = respx.get(remote_url).mock(
        return_value=Response(200, content=payload_bytes, headers={"content-type": "image/png"})
    )
    convert_route = respx.post(server.BASE_URL).mock(
        return_value=Response(200, json={"status": "ok"})
    )

    result = await server._convert_url_impl(
        apiKey="key",
        apiSecret="secret",
        url=remote_url,
        outfmt="webp",
        width=128,
        height=256,
        fetchHeaders={"Authorization": "Bearer token"},
    )

    assert result == {"status": "ok"}
    assert fetch_route.called
    fetch_request = fetch_route.calls[0].request
    assert fetch_request.headers["authorization"] == "Bearer token"

    assert convert_route.called
    convert_request = convert_route.calls[0].request
    sent_json = json.loads(convert_request.content.decode())
    assert sent_json["DocDataType"] == "png"
    assert sent_json["Fmt"] == "webp"
    assert sent_json["Width"] == 128
    assert sent_json["Height"] == 256
    assert sent_json["DocData"] == base64.b64encode(payload_bytes).decode("ascii")


@pytest.mark.asyncio
@respx.mock
async def test_convert_url_respects_inext_override():
    remote_url = "https://example.com/file"
    payload_bytes = b"PDFDATA"

    respx.get(remote_url).mock(return_value=Response(200, content=payload_bytes))
    convert_route = respx.post(server.BASE_URL).mock(return_value=Response(200, json={"status": "ok"}))

    await server._convert_url_impl(
        apiKey="key",
        apiSecret="secret",
        url=remote_url,
        outfmt="png",
        inext="pdf",
    )

    sent_json = json.loads(convert_route.calls[0].request.content.decode())
    assert sent_json["DocDataType"] == "pdf"


def test_all_tools_expose_mcp_annotations():
    expected_tools = {
        "doctype": (True, False),
        "preflight": (True, False),
        "convert": (False, False),
        "convert_url": (False, False),
        "convert_file": (False, False),
        "delete_document": (False, True),
        "fetch": (True, False),
        "search": (True, False),
    }

    async def _get_tools():
        return await server.mcp.list_tools()

    import asyncio
    tools = {t.name: t for t in asyncio.run(_get_tools())}
    for tool_name, (readonly, destructive) in expected_tools.items():
        assert tool_name in tools, f"Missing tool {tool_name}"
        annotations = tools[tool_name].annotations
        assert annotations is not None, f"Tool {tool_name} is missing annotations"
        assert annotations.readOnlyHint is readonly
        assert annotations.destructiveHint is destructive


def test_preflight_recommendations():
    res_dwg = server.recommend_ai_format("diagram.dwg", target_provider="claude")
    assert res_dwg["supported"] is True
    assert res_dwg["category"] == "design_vector_cad"
    assert res_dwg["needs_conversion"] is True
    assert res_dwg["recommended_outfmt"] == "png"

    res_xls = server.recommend_ai_format("report.xls", target_provider="openai")
    assert res_xls["supported"] is True
    assert res_xls["category"] == "spreadsheet"
    assert res_xls["needs_conversion"] is True
    assert res_xls["recommended_outfmt"] == "pdf"

    res_png = server.recommend_ai_format("image.png", target_provider="gemini")
    assert res_png["supported"] is True
    assert res_png["native_ai_supported"] is True
    assert res_png["needs_conversion"] is False

    res_url = server.recommend_ai_format("https://example.com/assets/photo.cr2?token=abc#view", target_provider="claude")
    assert res_url["extension"] == "cr2"
    assert res_url["supported"] is True
    assert res_url["category"] == "camera_raw"


@pytest.mark.asyncio
async def test_convert_file_disabled_via_env(monkeypatch, tmp_path):
    from tests.conftest import tool_fn

    monkeypatch.setenv("TWEEKIT_ALLOW_LOCAL_FILES", "0")
    fn = tool_fn(server.convert_file)
    result = await fn(file_path=str(tmp_path / "any.pdf"), outfmt="png", apiKey="k", apiSecret="s")
    assert "error" in result
    assert "TWEEKIT_ALLOW_LOCAL_FILES=0" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_convert_file_tool_writes_output_path(tmp_path):
    from tests.conftest import tool_fn

    src = tmp_path / "sample.psd"
    src.write_bytes(b"PSDDATA")
    dest = tmp_path / "out" / "sample.png"

    respx.post(server.BASE_URL).mock(
        return_value=Response(200, content=b"PNG_OUTPUT_BYTES", headers={"content-type": "image/png"})
    )

    fn = tool_fn(server.convert_file)
    result = await fn(
        file_path=str(src),
        outfmt="png",
        output_path=str(dest),
        apiKey="key",
        apiSecret="secret",
    )

    assert result["status"] == "ok"
    assert dest.exists()
    assert dest.read_bytes() == b"PNG_OUTPUT_BYTES"
    assert result["size_bytes"] == len(b"PNG_OUTPUT_BYTES")

