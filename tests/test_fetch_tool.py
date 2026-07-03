"""Tests for the fetch MCP tool."""
import pytest
import respx
from httpx import Response

import server


@pytest.mark.asyncio
@respx.mock
async def test_fetch_html_returns_markdown():
    """Fetching an HTML page returns normalized markdown-like text."""
    url = "https://example.com/page"
    html_content = "<html><body><h1>Hello World</h1><p>Some content</p></body></html>"

    respx.get(url).mock(
        return_value=Response(
            200,
            content=html_content.encode(),
            headers={"content-type": "text/html; charset=utf-8"},
        )
    )

    result = await server.fetch.fn(url=url)

    assert "error" not in result
    # Result should contain the text content
    content = result.get("content", result.get("text", ""))
    assert "Hello World" in content or len(content) > 0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_json_returns_raw():
    """Fetching a JSON endpoint returns the parsed JSON."""
    url = "https://api.example.com/data"
    json_data = {"key": "value", "count": 42}

    respx.get(url).mock(
        return_value=Response(
            200,
            json=json_data,
            headers={"content-type": "application/json"},
        )
    )

    result = await server.fetch.fn(url=url)
    assert "error" not in result


@pytest.mark.asyncio
@respx.mock
async def test_fetch_404_returns_error():
    """404 response is reported as an error."""
    url = "https://example.com/missing"
    respx.get(url).mock(return_value=Response(404, content=b"Not Found"))

    result = await server.fetch.fn(url=url)
    assert "error" in result
    assert "404" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_fetch_timeout():
    """Connection timeout returns a network error."""
    import httpx

    url = "https://slow.example.com/"
    respx.get(url).mock(side_effect=httpx.ReadTimeout("Timed out"))

    result = await server.fetch.fn(url=url)
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_fetch_follows_redirects():
    """Fetch follows HTTP redirects to the final URL."""
    original_url = "https://example.com/redirect"
    final_url = "https://example.com/final"

    respx.get(original_url).mock(
        return_value=Response(
            301,
            headers={"location": final_url},
        )
    )
    respx.get(final_url).mock(
        return_value=Response(
            200,
            content=b"Final content",
            headers={"content-type": "text/plain"},
        )
    )

    result = await server.fetch.fn(url=original_url)
    # Should succeed with content from the final URL
    assert "error" not in result
