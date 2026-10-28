# Use the official Python image
FROM python:3.13-slim

LABEL io.modelcontextprotocol.server.name="io.github.equilibrium-team/tweekit"
LABEL org.opencontainers.image.title="TweekIT MCP Server"
LABEL org.opencontainers.image.description="Normalize, preflight, and convert 450+ file types for AI workflows via TweekIT MCP (AMPS dba Equilibrium)."
LABEL org.opencontainers.image.vendor="AMPS dba Equilibrium"
LABEL org.opencontainers.image.version="1.8.0"
LABEL org.opencontainers.image.source="https://github.com/equilibrium-team/tweekit-mcp"
LABEL org.opencontainers.image.licenses="MIT"

# Refresh OS CA trust store (remediates Oct 2026 eMudhra intermediate CA compromise)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && update-ca-certificates && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into /app
COPY . /app
WORKDIR /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1
ENV PLUGIN_PROXY_PORT=8000

# Install dependencies
RUN uv sync

EXPOSE 8080
EXPOSE 8000

# Run the FastMCP server and plugin proxy (if ports do not conflict)
CMD ["scripts/start_services.sh"]
