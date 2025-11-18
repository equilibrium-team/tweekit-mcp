#!/usr/bin/env bash
set -euo pipefail

# The main application port provided by Cloud Run.
# The plugin proxy is the primary, user-facing service.
MAIN_PORT="${PORT:-8080}"

# A secondary port for the internal MCP server.
MCP_SERVER_PORT="${MCP_SERVER_PORT:-8000}"

if [[ "${MAIN_PORT}" == "${MCP_SERVER_PORT}" ]]; then
    echo "Port conflict detected: PORT (${MAIN_PORT}) matches MCP_SERVER_PORT (${MCP_SERVER_PORT})." >&2
    exit 1
fi

trap 'kill 0 2>/dev/null || true' EXIT

# Run the user-facing plugin proxy on the main port Cloud Run expects.
echo "Starting Plugin Proxy on port ${MAIN_PORT}"
uv run uvicorn plugin_proxy:app --host 0.0.0.0 --port "${MAIN_PORT}" &

# Run the internal MCP server on the secondary port.
echo "Starting MCP Server on port ${MCP_SERVER_PORT}"
PORT="${MCP_SERVER_PORT}" uv run server.py &

wait -n
