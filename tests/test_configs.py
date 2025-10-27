import json
from pathlib import Path


def _load_config(name: str) -> dict:
    path = Path("configs") / name
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def test_cursor_config_structure():
    config = _load_config("cursor-mcp.json")
    assert "mcpServers" in config
    server = config["mcpServers"]["tweekit"]
    assert server["type"] == "http"
    assert server["url"].startswith("https://")
    assert "${TWEEKIT_API_KEY}" in server["headers"]["ApiKey"]


def test_continue_config_structure():
    config = _load_config("continue-mcp.json")
    server = config["mcpServers"]["tweekit"]
    assert server["type"] == "streamable-http"
    assert server["url"].startswith("https://")
    assert "ApiSecret" in server["headers"]
