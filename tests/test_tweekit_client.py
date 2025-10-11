import asyncio
from pathlib import Path

import pytest

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
        return result

    result = asyncio.run(runner())

    assert result["status"] == "ok"


def test_missing_credentials_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("TWEAKIT_API_KEY", raising=False)
    monkeypatch.delenv("TWEAKIT_API_SECRET", raising=False)

    doc = tmp_path / "doc.txt"
    doc.write_text("hello")

    client = tweekit_client.TweekitClient(server_url="https://mcp.test/mcp")

    async def runner():
        async with client:
            await client.convert_file(doc, outfmt="txt")

    with pytest.raises(RuntimeError):
        asyncio.run(runner())
