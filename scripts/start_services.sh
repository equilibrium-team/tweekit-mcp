#!/usr/bin/env bash
set -euo pipefail

SERVER_PORT="${PORT:-8080}"
PLUGIN_PROXY_PORT="${PLUGIN_PROXY_PORT:-8000}"

if [[ "${SERVER_PORT}" == "${PLUGIN_PROXY_PORT}" ]]; then
    echo "Port conflict detected: PORT (${SERVER_PORT}) matches PLUGIN_PROXY_PORT (${PLUGIN_PROXY_PORT})." >&2
    exit 1
fi

trap 'kill 0 2>/dev/null || true' EXIT

uv run server.py &
uv run uvicorn plugin_proxy:app --host 0.0.0.0 --port "${PLUGIN_PROXY_PORT}" &

wait -n
