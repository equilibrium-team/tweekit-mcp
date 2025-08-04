# TweekIT MCP Server

TweekIT MCP Server is a tool designed to normalize various file formats for AI ingestion. It provides a set of APIs to retrieve supported file formats, convert documents to different formats, and fetch the current version of the TweekIT API.

## Features

- **Version API**: Retrieve the current version of the TweekIT API.
- **Supported File Formats**: Query supported file formats or map file extensions to document types.
- **Document Conversion**: Convert documents as part of the payload (base64-encoded) to specified output formats, including optional resizing and background color adjustments.

## Requirements

- Python 3.10 or later
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
ext: File extension (e.g., jpg, docx).
apiKey: API key for authentication.
apiSecret: API secret for authentication.
Document Conversion:

Endpoint: /convert
Description: Converts a base64-encoded document to the specified output format - Parameters:
apiKey: API key for authentication.
apiSecret: API secret for authentication.
inext: Input file extension (e.g., jpg, png).
outfmt: Desired output format (e.g., pdf, png).
blob: Base64-encoded document data.
Optional:
width: Desired width of the output (default: 0 for no resizing).
height: Desired height of the output (default: 0 for no resizing).
page: Page number to convert (for multi-page documents, default: 1).
bgcolor: Background color for transparent documents (default: empty string - leave transparent pixels as is).

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
