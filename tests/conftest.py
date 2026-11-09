import importlib
import socket
from collections.abc import Generator
from typing import Any, Callable

import pytest

import server


def tool_fn(tool: Any) -> Callable:
    """Return the underlying callable for an MCP tool, regardless of FastMCP version."""
    return getattr(tool, "fn", tool)


@pytest.fixture(autouse=True)
def mock_example_dns_for_respx(monkeypatch):
    """Resolve RFC 2606 `.example.com` / `.test` hostnames offline for `respx` tests while keeping SSRF checks live."""
    real_resolve = server._resolve_host_ips

    async def _fake_resolve(hostname: str, port: int) -> list[str]:
        lower = hostname.lower().rstrip(".")
        if lower == "example.com" or lower.endswith(".example.com") or lower.endswith(".test"):
            return ["93.184.216.34"]
        if lower == "unresolvable.invalid":
            raise socket.gaierror("NXDOMAIN")
        return await real_resolve(hostname, port)

    monkeypatch.setattr(server, "_resolve_host_ips", _fake_resolve)


@pytest.fixture
def proxy_app(monkeypatch) -> Generator:
    monkeypatch.setenv("TWEEKIT_API_BASE_URL", "https://api.test/")
    monkeypatch.setenv("TWEEKIT_API_KEY", "test-key")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "test-secret")
    monkeypatch.setenv("PLUGIN_PUBLIC_BASE_URL", "https://plugin.test")
    monkeypatch.delenv("PLUGIN_LOGO_URL", raising=False)

    module = importlib.import_module("plugin_proxy")
    importlib.reload(module)
    yield module.app


@pytest.fixture
def proxy_module(monkeypatch):
    monkeypatch.setenv("TWEEKIT_API_BASE_URL", "https://api.test/")
    monkeypatch.setenv("TWEEKIT_API_KEY", "test-key")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "test-secret")
    monkeypatch.setenv("PLUGIN_PUBLIC_BASE_URL", "https://plugin.test")
    monkeypatch.delenv("PLUGIN_LOGO_URL", raising=False)

    module = importlib.import_module("plugin_proxy")
    importlib.reload(module)
    return module
