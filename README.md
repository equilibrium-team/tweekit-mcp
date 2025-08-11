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

# Resources

Endpoint: /version

Description:
Fetches the current version of the TweekIT API. Takes no parameters.

# Tools

Endpoint: /doctype

Description:
Retrieves a list of supported input file formats or maps a file extension to its document type. If the document type field returned is empty, then the format isn't supported for reading.

Parameters:
- extension: File extension (e.g., jpg, docx). Optional, defaults to '*'. (return all supported input document types).
- apiKey: API key for authentication.
- apiSecret: API secret for authentication.

Endpoint: /convert
Description: Converts a base64-encoded document to the specified output format.

Parameters:
- apiKey: API key for authentication.
- apiSecret: API secret for authentication.
- inext: Input file extension (e.g., jpg, png, doc, docx, etc.).
- outfmt: Desired output format (e.g., jpg, pdf, png).
- blob: Base64-encoded document data.

Optional:
- noRasterize: If the input document is a text-based document (doc, odt, xls, etc.) and the output format is set to 'pdf' with this parameter set to true, instead of rasterizing and doing image operations on the document, all pages will be converted to a PDF and returned. If the output format is not 'pdf', this parameter is ignored. Defaults to false. 
- width: Desired width of the output (default: 0 for no resizing).
- height: Desired height of the output (default: 0 for no resizing).
- page: Page number to convert (for multi-page documents, default: 1).
- bgcolor: Background color for transparent documents (default: empty string - leave transparent pixels as is).

The image of the specified page (or page 1) will be returned in the response with the correct content type set.

In addition to Docker, it can run simply by doing 'uv run server.py'.

The server will be accessible at http://localhost:8080.

Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

License
This project is licensed under the MIT License. See the LICENSE file for details.
