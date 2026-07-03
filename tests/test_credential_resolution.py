"""Tests for _resolve_credentials edge cases."""
import pytest

import server


def test_resolve_explicit_credentials():
    """Explicit key/secret are returned as-is."""
    key, secret = server._resolve_credentials("my-key", "my-secret")
    assert key == "my-key"
    assert secret == "my-secret"


def test_resolve_env_credentials(monkeypatch):
    """Falls back to environment variables when args are None."""
    monkeypatch.setenv("TWEEKIT_API_KEY", "env-key")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "env-secret")

    key, secret = server._resolve_credentials(None, None)
    assert key == "env-key"
    assert secret == "env-secret"


def test_resolve_partial_explicit_with_env_fallback(monkeypatch):
    """Explicit key but env secret still resolves both."""
    monkeypatch.setenv("TWEEKIT_API_KEY", "env-key")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "env-secret")

    key, secret = server._resolve_credentials("explicit-key", None)
    assert key == "explicit-key"
    assert secret == "env-secret"


def test_resolve_missing_key_raises(monkeypatch):
    """Missing API key raises RuntimeError."""
    monkeypatch.delenv("TWEEKIT_API_KEY", raising=False)
    monkeypatch.delenv("TWEEKIT_API_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="TWEEKIT_API_KEY"):
        server._resolve_credentials(None, None)


def test_resolve_missing_secret_raises(monkeypatch):
    """Has key but missing secret raises RuntimeError."""
    monkeypatch.setenv("TWEEKIT_API_KEY", "got-key")
    monkeypatch.delenv("TWEEKIT_API_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="TWEEKIT_API_SECRET"):
        server._resolve_credentials(None, None)


def test_resolve_empty_string_key_raises(monkeypatch):
    """Empty string key is treated as missing."""
    monkeypatch.setenv("TWEEKIT_API_KEY", "")
    monkeypatch.setenv("TWEEKIT_API_SECRET", "secret")

    with pytest.raises(RuntimeError):
        server._resolve_credentials(None, None)
