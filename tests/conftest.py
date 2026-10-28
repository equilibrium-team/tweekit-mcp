import importlib
import os
from collections.abc import Generator
from typing import Any, Callable

import pytest


def tool_fn(tool: Any) -> Callable:
    """Return the underlying callable for an MCP tool, regardless of FastMCP version.

    FastMCP 2.x wrapped tools in a Tool object exposing ``.fn``; FastMCP 3.x
    returns the decorated function directly (still callable). This helper
    handles both so tests aren't coupled to the FastMCP version.
    """
    return getattr(tool, "fn", tool)


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
