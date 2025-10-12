# TweekIT MCP Server

TweekIT MCP Server is a tool designed to normalize various file formats for AI ingestion. It provides a set of APIs to retrieve supported file formats, convert documents to different formats, and fetch the current version of the TweekIT API.

## Features

- **Version API**: Retrieve the current version of the TweekIT API.
- **Supported File Formats**: Query supported file formats or map file extensions to document types.
- **Document Conversion**: Convert documents as part of the payload (base64-encoded) to specified output formats, including optional resizing and background color adjustments.

## Requirements

- Python 3.13 or later
- Docker (optional, for containerized builds)
- `httpx` library for HTTP requests
- `FastMCP` for tool registration and server functionality

## Installation

1. Clone the repository:
   git clone https://github.com/your-username/mcpserver.git
   cd mcpserver

2. Install dependencies
   pip install -r requirements.txt

3. Set up environment variables:
   PORT: The port on which the server will run (default: 8080).

Usage
Running the Server
To start the server locally:

The server will start on the specified port (default: 8080).

API Endpoints
Version API:

Endpoint: /version
Description: Fetches the current version of the TweekIT API.
Supported File Formats:

Endpoint: /doctype
Description: Retrieves a list of supported file formats or maps a file extension to its document type.
Parameters:
ext: File extension (e.g., jpg, pdf).
apiKey: API key for authentication.
apiSecret: API secret for authentication.
Document Conversion:

Endpoint: /convert
Description: Converts a base64-encoded document to the specified output format<vscode_annotation details='%5B%7B%22title%22%3A%22hardcoded-credentials%22%2C%22description%22%3A%22Embedding%20credentials%20in%20source%20code%20risks%20unauthorized%20access%22%7D%5D'>. </vscode_annotation> - Parameters:
apiKey: API key for authentication.
apiSecret: API secret for authentication.
inext: Input file extension (e.g., jpg, png).
outfmt: Desired output format (e.g., pdf, png).
blob: Base64-encoded document data.
Optional:
width: Desired width of the output (default: 0 for no resizing).
height: Desired height of the output (default: 0 for no resizing).
page: Page number to convert (for multi-page documents, default: 1).
bgcolor: Background color for transparent documents (default: empty string).
Building with Docker
To build and run the project using Docker:

Build the Docker image:

Run the Docker container:

The server will be accessible at http://localhost:8080.

Logging
The server uses Python's logging module to log messages. Logs are displayed in the following format:

Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

License
This project is licensed under the MIT License. See the LICENSE file for details.

## Integration Guides

- ChatGPT plugin setup: `docs/chatgpt-plugin.md`
- Claude Desktop bundle: `docs/claude-bundle.md`
- Grok interim workflow: `docs/grok-integration.md`
- DeepSeek bridge + roadmap: `docs/deepseek-integration.md`
- IDE assistants (Cursor, Continue, etc.): `docs/developer-tools.md`
- SDK quickstarts (Python/Node): `docs/quickstarts.md`
- Automated testing strategy: `docs/testing.md`
- MCP Pulse submission checklist: `docs/mcp-pulse-checklist.md`

## Firebase Deploy (Functions + Hosting)

Deploy the MCP server as a Firebase Function (served via Hosting rewrite) to leverage Blaze plan pay‑per‑use.

Prerequisites
- Install CLI: `npm i -g firebase-tools`
- Login/project: `firebase login`, then `firebase use <PROJECT_ID>`

Vendor Python dependencies
- With uv (recommended):
  - `uv pip install -r functions/requirements.txt --target functions/packages`
- Or with pip:
  - `pip install -r functions/requirements.txt -t functions/packages`

Deploy
- `firebase deploy --only functions,hosting`

Endpoints
- Hosting rewrite: `https://<PROJECT_ID>.web.app/mcp` → Cloud Function `mcp_server`
- Function (direct, optional): `https://us-west1-<PROJECT_ID>.cloudfunctions.net/mcp_server/mcp`

Configuration
- Region: set to `us-west1` via `set_global_options` in `functions/main.py`.
- Instance limits: global max instances set to 10.
- Logging level: set `LOG_LEVEL` env var (e.g., `INFO`, `WARNING`).

Testing
- Point the client to Hosting:
  - In `test_server.py`: `Client("https://<PROJECT_ID>.web.app/mcp")`
- Run: `uv run python test_server.py`
