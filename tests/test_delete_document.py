"""Tests for the delete_document MCP tool."""
import pytest
import respx
from httpx import Response

import server


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_success():
    """Successful deletion returns confirmation."""
    doc_id = "abc-123"
    route = respx.delete(f"{server.BASE_URL}{doc_id}").mock(
        return_value=Response(200, json={"message": "Deleted", "docId": doc_id})
    )

    result = await server.delete_document.fn(
        docId=doc_id,
        apiKey="test-key",
        apiSecret="test-secret",
    )

    assert route.called
    assert result["docId"] == doc_id
    assert "error" not in result
    # Verify auth headers were sent
    req = route.calls[0].request
    assert req.headers["apikey"] == "test-key"
    assert req.headers["apisecret"] == "test-secret"


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_not_found():
    """404 returns an error dict instead of raising."""
    doc_id = "nonexistent-999"
    respx.delete(f"{server.BASE_URL}{doc_id}").mock(
        return_value=Response(404, json={"error": "Not found"})
    )

    result = await server.delete_document.fn(
        docId=doc_id,
        apiKey="test-key",
        apiSecret="test-secret",
    )

    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_no_json_response():
    """Server returns 200 with no JSON body — should still succeed."""
    doc_id = "plain-text-response"
    respx.delete(f"{server.BASE_URL}{doc_id}").mock(
        return_value=Response(200, content=b"OK")
    )

    result = await server.delete_document.fn(
        docId=doc_id,
        apiKey="test-key",
        apiSecret="test-secret",
    )

    assert result["docId"] == doc_id
    assert result["message"] == "Document deleted successfully"


@pytest.mark.asyncio
@respx.mock
async def test_delete_document_network_error():
    """Network failure returns an error dict."""
    import httpx

    doc_id = "network-fail"
    respx.delete(f"{server.BASE_URL}{doc_id}").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    result = await server.delete_document.fn(
        docId=doc_id,
        apiKey="test-key",
        apiSecret="test-secret",
    )

    assert "error" in result


@pytest.mark.asyncio
async def test_delete_document_missing_credentials(monkeypatch):
    """Missing credentials returns a RuntimeError-based error."""
    monkeypatch.delenv("TWEEKIT_API_KEY", raising=False)
    monkeypatch.delenv("TWEEKIT_API_SECRET", raising=False)

    result = await server.delete_document.fn(docId="some-id")

    assert "error" in result
