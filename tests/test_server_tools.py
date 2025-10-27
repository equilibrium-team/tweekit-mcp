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
