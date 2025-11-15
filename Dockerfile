# Use the official Python image
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
#RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 && rm -rf /var/lib/apt/lists/*

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
