"""Official TweekIT MCP Server & Python SDK by AMPS dba Equilibrium.

Provides:
- `TweekitClient`: Async FastMCP client wrapper for remote or stdio TweekIT MCP servers.
- `TweekitDirectClient`: Direct async Python client for the TweekIT REST API (no MCP hop required).
- `preflight_check` / `recommend_ai_format`: Instant file format validation and AI provider modality routing
  across 450+ extensions (syncs with Maitrix AI Hub, Claude, OpenAI, Gemini, Mistral, Grok, DeepSeek).
- `mcp`: The FastMCP server instance exposing all TweekIT tools (`doctype`, `preflight`, `convert`,
  `convert_url`, `convert_file`, `delete_document`, `fetch`, `search`).
"""

from clients.python.tweekit_client import TweekitClient, TweekitDirectClient
from server import (
    AI_PROVIDER_PROFILES,
    BASE_URL,
    EXTENSIVE_SUPPORTED_EXTENSIONS,
    FORMAT_TAXONOMY,
    SERVER_VERSION,
    convert,
    convert_file,
    convert_url,
    delete_document,
    doctype,
    fetch,
    main,
    mcp,
    mcp_version,
    preflight,
    preflight_check,
    recommend_ai_format,
    search,
    version,
)

__version__ = SERVER_VERSION
__author__ = "AMPS dba Equilibrium"

__all__ = [
    "__version__",
    "__author__",
    "SERVER_VERSION",
    "BASE_URL",
    "FORMAT_TAXONOMY",
    "EXTENSIVE_SUPPORTED_EXTENSIONS",
    "AI_PROVIDER_PROFILES",
    "TweekitClient",
    "TweekitDirectClient",
    "preflight_check",
    "recommend_ai_format",
    "mcp",
    "main",
    "version",
    "mcp_version",
    "doctype",
    "preflight",
    "convert",
    "convert_url",
    "convert_file",
    "delete_document",
    "fetch",
    "search",
]
