import importlib
import os
from collections.abc import Generator

import pytest


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
