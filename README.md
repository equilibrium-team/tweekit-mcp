# TweekIT MCP Server

*Ingest and Convert Just About Any Filetype Into AI Workflows*

## Overview

TweekIT MCP Server is the universal media translator for AI workflows, making any file ready for processing in seconds. **Built on the robust content processing engine of Equilibrium's MediaRich Server, a technology developed since 2000 and trusted by massive portals and media companies worldwide, TweekIT brings decades of expertise in handling complex media, drawing on a pedigree that includes the renowned DeBabelizer.**

With TweekIT, you can upload, preview, transform, and download over 400 supported file types using a consistent API or widget interface. It removes the pain of unpredictable input formats by automatically normalizing and preparing assets for the next step in your workflow.

### What is TweekIT?

TweekIT is a universal media ingestion and transformation service designed to take any supported file and make it AI ready in seconds. Whether you are normalizing formats, resizing assets, or extracting a single page from a complex document, TweekIT provides a consistent, API first way to get exactly the output you need without worrying about the quirks of individual file types.

### Why use it in an MCP context?

In a Model Context Protocol (MCP) workflow, TweekIT acts like a universal translator for media. It sits between your AI agent and the unpredictable real world files it encounters, ensuring every asset is transformed into a compatible, standardized format before processing. This is similar to how GitHub Actions streamlines software automation, but applied to media handling in AI pipelines.

With TweekIT in your MCP toolset, your agents can:

- Accept a wider range of inputs from users without failure
- Automatically apply transformations such as cropping, resizing, format conversion, and background changes
- Pass clean, ready to use assets to the next step in your AI workflow with no manual intervention fixing the constant customer file ingestion failures we are all to familiar with

### Example scenario

A user uploads a scanned PDF of an ID card as part of an onboarding process. Your MCP agent calls TweekIT to:

- Convert the PDF to a PNG image
- Crop to just the ID card
- Resize to a standard 300x300 pixel headshot
- Return the transformed image directly into the verification pipeline

The entire process happens in seconds, and your workflow never sees an incompatible file format.

### Key Capabilities

- Supports **400+** file types for seamless ingestion and conversion, **leveraging a core engine refined over two decades to handle dynamic imaging and video processing.**
- Stateless and API first design for fast, scalable integrations
- Widget or REST API access to fit any application architecture
- Enterprise grade security with secure key handling and short lived asset storage
- Instant compatibility fixes that prevent AI pipeline failures from bad input formats immediately

### Try it now

- [Live Demo](https://www.tweekit.io/demo/) – Upload and transform files in your browser
- [Use Case Examples](https://www.tweekit.io/use-case/) – See practical workflows and code samples on the website. **The specific MCP manifest conversions are shown in section 7 below.**

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Authentication](#authentication)
- [Server and Hosting](#server-and-hosting)
- [Client Compatibility](#client-compatibility)
  - [Quickstart (Claude Desktop)](#quickstart-claude-desktop)
  - [Quickstart (ChatGPT MCP)](#quickstart-chatgpt-mcp)
- [Rate Limits and Pricing](#rate-limits-and-pricing)
- [Core Concepts](#core-concepts)
- [MCP API Reference](#mcp-reference)
- [REST API Reference](#rest-api-reference)
- [Use Cases](#use-cases)
- [Demo + Show Code](#demo--show-code)
- [Error Handling and Troubleshooting](#error-handling-and-troubleshooting)
- [Advanced Topics](#advanced-topics)
- [Resources](#resources)

## Requirements

- Python 3.10 or later
- Docker (optional, for containerized builds)
- `httpx` library for HTTP requests
- `FastMCP` for tool registration and server functionality

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/equilibrium-team/tweekit-mcp.git
   cd tweekit-mcp
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   - **PORT**: The port on which the server will run (default: 8080).

## Quickstart

### Step 1: Sign Up

Create your free TweekIT account and get started with 10,000 API calls included at no cost.  
[Pricing and Signup here](https://www.tweekit.io/) to generate your API credentials in the MANAGE ACCOUNT page and start using the service.

### Step 2: Choose Your Authentication Method

TweekIT supports multiple authentication methods. However ONLY the Key/Secret pair method will work with the MCP integration.

- **API Key and Secret** – Required for MCP production use, more secure and easier to control access

You will find these values in your account dashboard after sign up. Keep them safe and never expose them in client-side code.

### Step 3: Make Your First API Call

Below is a minimal working json example that sends an image with a basic resize operation, previews the transformation, and returns the result. This example uses API Key and Secret authentication.

The JSON was captured from the use of MCP Inspector with the publicly available MCP server.


```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "png",
      "outfmt": "png",
      "blob": "iVBORw0KGgoAAAANSUhEUgAAABwAAAA6CAYAAACj+Dm/AAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsSAAALEgHS3X78AAAAHnRFWHRTb2Z0d2FyZQBFcXVpbGlicml1bSBNZWRpYVJpY2h7w4AAAAAB30lEQVRYhe2Xv0vDQBTHP4rQTRGhLqKiYt38MaggKIi46e6im2Rw7FJw7NAh4uAi+h/oIDgKnR3VQZROKiLYrZtOOiQH1+RevJQ0INwXQt7de7lP++7l7tJTq9XIU7250hzQAR3QAR3QAXMH3gM/wG0ewHtgNrSXgXo3gXUNprTSLaAPrBv6C4DXDeBBgm8ha+ArwT+RNJkl8BoY/SNmKiugB2xaxA1nBayQnEolY+GkBdqkUlescNIAPWBL8D0I/bHCSQOsCP3fwFx4jypWOLbApFRehfdPgy9WODbApKpsATuh/WHwxwrHBphUlRea/SLErKUBniGn8g3Y19qPQtx4GuBugu8y0q4KcRN6oy9hwFvkVDaAfoKtaQgYBAaE2KINsE6wkUqaDi9b+UBZAn5ht3Sl0bwyTHOYNQxgRAIad+kMNJY3sAAcQvscesQPQ7qaBPP7Bbxr/XeaXab9BKdrMQrcS4AdhYPZ6EkArkJ7SucNQRC8c7YwCNZW084xAPgKeI25Or+B4xQwpWehf0MBl4SAG+C0A6D0zIwCFg3OJrDdAUwBTaeAggI2DM6TDmFKcwT7pa6GApY0aAs4R17908gnyBTh+CX9tShlAIiqSuSH/+sPUgd0QAf8J8BfT2hGnMaA5CUAAAAASUVORK5CYII=",
      "noRasterize": false,
      "width": 30,
      "height": 30,
      "page": 1,
      "bgcolor": ""
    }
  },
  "jsonrpc": "2.0",
  "id": 4
}
```

### Step 4: See It in Action

You can explore TweekIT visually before writing any code. The live demo lets you upload files, apply transformations, and download the results instantly.

- [Open the Live Demo](https://www.tweekit.io/demo/)
- [View Use Case Examples](https://www.tweekit.io/use-case/) for real workflows and code samples

## Authentication

TweekIT supports multiple authentication methods (REST API, APP ID method is ONLY for using). Set up your API Key and Secret so you can start quickly while maintaining security best practices.

### For MCP Server Use: API Key + Secret

This is the most secure and flexible option. Use this for all production deployments.

**Steps:**

1. Generate your API Key and Secret in your TweekIT account settings.
2. Store them securely — never commit to source control.
3. Use server-side code or a reverse proxy to inject credentials into requests.

**Security Tips:**

- Always use a reverse proxy or other server-side method to protect credentials.
- Never embed secrets in client-side code.

**Next Steps:**  
Once authenticated, you can:

- Upload media as part of the request using Base-64
- Recieve output

## Server and Hosting

### Hosted ready MCP server

All tools and resources are available here, used for testing and free trials:

- Public MCP endpoint (HTTP transport): [https://mcp.tweekit.io/mcp/](https://mcp.tweekit.io/mcp/)

The currently available resource name is 'version'. The currently available tool names are 'doctype' and 'convert'. See below for parameters, or query the MCP server as it will return metadata instructing use of each of these.

### MCP Installation

You can run the TweekIT MCP server locally or connect to a hosted instance. The local option is recommended for development and testing.

**Local Installation**

```bash
git clone https://github.com/equilibrium-team/tweekit-mcp.git
cd tweekit-mcp
pip install -r requirements.txt
```

**Run the server:**

```bash
uv run server.py
```

The server will listen on:

- [`http://localhost:8080`](http://localhost:8080)

### Config Options

**Local Development Mode**  
By default, `server.py` will bind to `localhost` on port 8080. You can override the port with the `PORT` environment variable:

```bash
PORT=9090 uv run server.py
```

## Client Compatibility

- Claude: Compatible (discovers tools via listTools; works with HTTP transport).
- ChatGPT (OpenAI): Compatible (provides required tools: `search`, `fetch`).
- Cursor: Not targeted (no workspace/file tools exposed).

Examples

- Claude Desktop (config snippet):

  ```json
  {
    "mcpServers": {
      "tweekit": {
        "transport": { "type": "http", "url": "https://mcp.tweekit.io/mcp/" }
      }
    }
  }
  ```

- Claude tool call (arguments example):

  ```json
  {
    "name": "convert",
    "arguments": {
      "apiKey": "YOUR_KEY",
      "apiSecret": "YOUR_SECRET",
      "inext": "png",
      "outfmt": "webp",
      "blob": "<base64>",
      "width": 300,
      "height": 300
    }
  }
  ```

- OpenAI (Node, using MCP TypeScript client):

  ```ts
  import { Client } from "@modelcontextprotocol/sdk/client";
  import { HttpClientTransport } from "@modelcontextprotocol/sdk/client/transport/http";

  const transport = new HttpClientTransport(new URL("https://mcp.tweekit.io/mcp/"));
  const client = new Client({ name: "tweekit-example", version: "1.0.0" }, { capabilities: {} }, transport);
  await client.connect();
  const tools = await client.listTools();
  const res = await client.callTool({ name: "search", arguments: { query: "tweekit", max_results: 3 } });
  console.log(res);
  ```

- OpenAI (Python, quick call):

  ```py
  import asyncio
  from fastmcp import Client

  async def main():
      async with Client("https://mcp.tweekit.io/mcp/") as c:
          print(await c.list_tools())
          out = await c.call_tool("fetch", {"url": "https://tweekit.io"})
          print(out)
  asyncio.run(main())
  ```

### Quickstart (Claude Desktop)

1) Configure MCP server

```json
{
  "mcpServers": {
    "tweekit": {
      "transport": { "type": "http", "url": "https://mcp.tweekit.io/mcp/" }
    }
  }
}
```

2) Use in chat

- Ask: “List supported input types via doctype.”
- Or call convert with your key/secret and a base64 blob:

```json
{
  "name": "convert",
  "arguments": { "apiKey": "…", "apiSecret": "…", "inext": "png", "outfmt": "webp", "blob": "<base64>" }
}
```

### Quickstart (ChatGPT MCP)

If your ChatGPT environment supports MCP tools, add an HTTP MCP server pointing to the public endpoint.

1) Configure server: URL `https://mcp.tweekit.io/mcp/` (HTTP transport)
2) Use tools in a chat:

- search

```json
{ "name": "search", "arguments": { "query": "tweekit", "max_results": 3 } }
```

- fetch

```json
{ "name": "fetch", "arguments": { "url": "https://tweekit.io" } }
```

## Rate Limits and Pricing

TweekIT offers a generous free tier so you can explore and integrate without cost.

### Free Tier

- **10,000 API calls** included at no charge.
- Full access to all core upload, preview, and download capabilities.
- No credit card required to start.

### Paid Plans

If you exceed the free tier limit, you can upgrade to a paid plan at any time.  
See the full pricing guide for details. You must have a token key pair to use the MCP Server:  
[https://www.tweekit.io/pricing/](https://www.tweekit.io/pricing/)

### Handling Rate Limit Errors

When you reach your monthly quota, the API will respond with an HTTP `429 Too Many Requests` status.

**MCP Integration Tip**:  
Your MCP client should:

1. Catch `429` responses.
2. Surface a clear error message to the user.
3. Recommend upgrading the plan immediately to continue.

## Core Concepts

Understanding these core concepts will help you get the most out of TweekIT in an MCP workflow.

### Request includes Base-64 content → Response include Base-64 Results

TweekIT MCP Server uses this simple, stateless and secure pipeline for document processing requests.

### Transformations

TweekIT supports a wide range of transformations, applied at preview time:

- **Resize** by width and height (if send only one parameter, the other will be automatically calculated to maintain aspect ratio)
- **OutFormat** change the file format to a different file type
- **Background color** fills for transparent or padded areas
- **NoRasterize** When combined with a PDF output format, converts entire textual documents into a PDF file for upstream AI ingest.

### Stateless Processing

TweekIT does not store your files persistently.

- Job folder and temp storage are purged after each request.
- This design ensures minimal storage overhead and stronger privacy for sensitive files.
- Data in transit is encrypted via SSL.

## MCP Reference

### Resources

#### /version

Description:
Fetches the current version of the TweekIT API. Takes no parameters.

### Tools

#### /doctype

Description:
Retrieves a list of supported input file formats or maps a file extension to its document type. If the document type field returned is empty, then the format isn't supported for reading.

Parameters:
- extension: File extension (e.g., jpg, docx). Optional, defaults to '*'. (return all supported input document types).
- apiKey: API key for authentication.
- apiSecret: API secret for authentication.

#### /convert

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
- x1, y1, x2, y2: Integee crop coordinates. Defaults to all 0 (no cropping). Cropping is applied before the resize. The x1 and y1 values can be negative, which adds padding to the top and left; the x2 amd y2 can be greater than the original raster size, which adds padding to the right and bottom.
- page: Page number to convert (for multi-page documents, default: 1).
- alpha: boolean (defaults to True - pass alpha channel through if output format supports it) If false, then the alpha channel is removed and the pixels are replaced with the bgColor value.
- bgColor: Background color padding or when transparent documents need to have their alpha channel removed. (default: "000000" or black). Is is okay to precede the hex value with a '#' (web color indicator)

The image of the specified page (or page 1) will be returned in the response with the correct content type set. If noRasterize is set to true and all other conditions are met, a PDF of the contents of the entire submitted document will be returned.

#### /search

Description: Performs a simple web search using DuckDuckGo's HTML endpoint.

Parameters:
- query: Search query string.
- max_results: Maximum number of results to return (default: 5, max: 10).

Returns: `{ query, results: [{ title, url, snippet }] }`

#### /fetch

Description: Fetches a URL and returns content based on content-type.

Parameters:
- url: The `http` or `https` URL to fetch.

Returns:
- Image content as `image` resource for `image/*` responses.
- PDF as `resource` with `format="pdf"` for `application/pdf`.
- Text/JSON as a JSON object with `text` and metadata.
- Other binary as a generic `resource` with `format="bin"`.

## REST API Reference

Please refer to the documentation at (https://tweekit.io/docs/rest-api/) to get an understanding of how the MCP server talks to the TweekIT REST API to proxy MCP requests to TweekIT.

## Use Cases

Below are common workflows where TweekIT improves reliability and speed in media processing. Each example shows both REST API and MCP usage patterns.

### 1. Employee Headshot Automation

Automatically crop and resize images into a consistent size and format.

**MCP Example**

```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "png",
      "outfmt": "png",
      "blob": "iVBORw0KGgoAAAANSUhEUgAAABwAAAA6CAYAAACj+Dm/AAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsSAAALEgHS3X78AAAAHnRFWHRTb2Z0d2FyZQBFcXVpbGlicml1bSBNZWRpYVJpY2h7w4AAAAAB30lEQVRYhe2Xv0vDQBTHP4rQTRGhLqKiYt38MaggKIi46e6im2Rw7FJw7NAh4uAi+h/oIDgKnR3VQZROKiLYrZtOOiQH1+RevJQ0INwXQt7de7lP++7l7tJTq9XIU7250hzQAR3QAR3QAXMH3gM/wG0ewHtgNrSXgXo3gXUNprTSLaAPrBv6C4DXDeBBgm8ha+ArwT+RNJkl8BoY/SNmKiugB2xaxA1nBayQnEolY+GkBdqkUlescNIAPWBL8D0I/bHCSQOsCP3fwFx4jypWOLbApFRehfdPgy9WODbApKpsATuh/WHwxwrHBphUlRea/SLErKUBniGn8g3Y19qPQtx4GuBugu8y0q4KcRN6oy9hwFvkVDaAfoKtaQgYBAaE2KINsE6wkUqaDi9b+UBZAn5ht3Sl0bwyTHOYNQxgRAIad+kMNJY3sAAcQvscesQPQ7qaBPP7Bbxr/XeaXab9BKdrMQrcS4AdhYPZ6EkArkJ7SucNQRC8c7YwCNZW084xAPgKeI25Or+B4xQwpWehf0MBl4SAG+C0A6D0zIwCFg3OJrDdAUwBTaeAggI2DM6TDmFKcwT7pa6GApY0aAs4R17908gnyBTh+CX9tShlAIiqSuSH/+sPUgd0QAf8J8BfT2hGnMaA5CUAAAAASUVORK5CYII=",
      "noRasterize": false,
      "width": 30,
      "height": 30,
      "page": 1,
      "bgcolor": ""
    }
  }
}
```

**Equivalent REST Example (requires a separate upload step)**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 30, "height": 30, "fmt": "png"}'
```

### 2. KYC Photo Ingestion and Normalization

Process identity document photos into standardized formats for automated verification.

**MCP Example**

```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "jpg",
      "outfmt": "webp",
      "blob": "{Your base64 encoded photo}",
      "width": 600,
      "height": 600,
      "bgcolor": "FFFFFF"
    }
  }
}
```

**Equivalent REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 600, "height": 400, "fmt": "webp", "bgcolor": "#FFFFFF"}'
```

### 3. Social Media and E-Commerce Image Resizing

Generate platform-specific product images with correct aspect ratios and background fills.

**MCP Example**

```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "jpg",
      "outfmt": "jpg",
      "blob": "{Your base64 encoded photo}",
      "width": 1080,
      "height": 1080,
      "bgcolor": "FFFFFF"
    }
  }
}
```

**Equivalent REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 1080, "height": 1080, "fmt": "jpg", "bgcolor": "#FFFFFF"}'
```


### 4. Cross-Platform Asset Conversion

Convert files between formats for compatibility across different tools and workflows.

**MCP Example**

```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "{filename extension of the input doc}",
      "outfmt": "webp",
      "blob": "{Your base64 encoded document}"
    }
  }
}
```

**Equivalent REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"fmt": "webp"}'
```

### 5. Multi-page Document conversion to PDF

Convert complex document or legacy filetypes from original formats into PDF files for compatibility into your current AI workflow.

**MCP Example**

```json
{
  "method": "tools/call",
  "params": {
    "name": "convert",
    "arguments": {
      "apiKey": "{Your TweekIT API key}",
      "apiSecret": "{Your TweekIT API secret}",
      "inext": "{filename extension of the input doc}",
      "outfmt": "pdf",
      "noRasterize": true,
      "blob": "{Your base64 encoded document}"
    }
  }
}
```

**Equivalent REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"fmt": "pdf", noRasterize: true}'
```

## Demo + Show Code

TweekIT includes an interactive MCP-ready demo that lets you try the upload, preview, and transformation workflow in your browser — then see the exact code needed to reproduce those actions in your own project.

### Interactive Tweekit Demo

Open the [Live Demo](https://www.tweekit.io/demo/) to:

1. Upload any supported file.
2. Preview transformations such as resize, crop, background fill, and format conversion.
3. Download the transformed output.

### Upload Preview UI

The demo provides a drag-and-drop or click-to-upload interface for selecting files. Once uploaded, you’ll see:

- File name and type.
- Generated **DocId** (expires in 20 minutes).
- Original image preview.

### Transformation UI

Adjust transformation parameters directly in the browser:

- Resize dimensions.
- Crop area (rectangular or elliptical).
- Output format.
- Background color fill.

Changes are applied in real time using the same REST endpoints your application will call.

### Auto-Generate Code Tabs

Every action in the demo can display corresponding code for:

- **Node.js**

  ```javascript
  await fetch(`https://www.tweekit.io/tweekit/api/image/preview/${docId}`, {
    method: 'POST',
    headers: { "apikey": "{Your API Key}", "apisecret": "{Your API Secret}" },
    body: JSON.stringify({ width: 300, height: 300, fmt: 'png' })
  });
  ```

- **curl**

  ```bash
  curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
    -H "apikey: {Your API Key}" \
    -H "apisecret: {Your API Secret}" \
    -H "Content-Type: application/json;charset=UTF-8" \
    -d '{"width": 300, "height": 300, "fmt": "png"}'
  ```

## Error Handling and Troubleshooting

Building robust MCP workflows with TweekIT means anticipating and handling common error scenarios. The API returns clear HTTP status codes and error payloads so your client or MCP action can respond appropriately.

### Common Issues

**Bad Format**

- **Cause**: The file format is unsupported or the requested output format is invalid.
- **Resolution**: Check the supported file formats list in the docs. Ensure transformations request a valid `fmt` value.
- **HTTP Status**: `400 Bad Request`
- **Error Example**:

  ```json
  {
    "error": "invalid_format",
    "message": "The requested format is not supported."
  }
  ```

**Quota Exceeded**

- **Cause**: Monthly API call limit reached.
- **Resolution**: Upgrade to a higher plan or wait until quota resets.
- **HTTP Status**: `429 Too Many Requests`
- **Error Example**:

  ```json
  {
    "error": "rate_limit_exceeded",
    "message": "You have reached your 10,000 call monthly limit."
  }
  ```

### Recommended Retry and Fallback Patterns

- **Retry**: For transient network errors (`5xx`), retry up to 3 times with exponential backoff.
- **Fallback**: If a transformation fails, fall back to delivering the original file or a cached previous version.
- **Graceful Degradation**: For quota limits, surface a user-friendly message and a link to [upgrade your plan](https://www.tweekit.io/pricing/).

### Debugging with Tweekit API Request Logs

When using TweekIT in an MCP context:

1. The TweekIT API call requests are logged inside of your [tweekit.io](http://tweekit.io) account under each key in use.
2. Your MCP requests return appropriate responses if they fail.
3. Review your console output where defined by you in your configuration of the MCP Server.

## Advanced Topics

For teams pushing TweekIT beyond simple transformations, these advanced techniques can help you integrate deeper into AI pipelines, improve performance, and harden security.

### Integrating with AI Pipelines

TweekIT can serve as the pre-processing layer for AI workflows, ensuring inputs are in the correct format and size before being fed to downstream models. Instead of errors or bad/non-existent conversions, just use tweekit, to make sure the file can be used as intended.

**Examples**

- **Image-to-Video**: Normalize all frames before passing them to a video synthesis model.
- **Image-to-Image**: Normalize any file, including the first page of any document or pdf, camera raw, tiff, psd, illustrator, etc. of any kind into a .png or .jpg that your LLM can handle.
- **Style Transfer**: Resize and reformat images to match the model’s expected input dimensions.
- **OCR Pipelines**: Convert documents to high-contrast PNGs to improve text recognition accuracy.
- **Pro formats (ie. Adobe Illustrator) ingestion**: Convert into usable image format for rendering a complex PDF document rather than failing, or receiving unusable results.
- **Office Document, legacy and complex formats to PDF**: Word files of all types (.doc, .docm, .docx, .dot, .ppt, .vso) can now be converted into a standard PDF to ingestible by most AI LLM’s.

In MCP, chain TweekIT transformations before invoking the AI model action.

### Performance Tuning

- **Reduce Output Size**: Use `fmt (rest) outfmt (MCP)` and compression-friendly formats like `webp` for faster delivery.
- **Minimize Transform Steps**: Chain transformations into one request instead of multiple previews.

### Security Hardening

- **API Key Management**: Rotate keys regularly and limit scope when possible.
- **Reverse Proxy Secrets**: Use a server-side proxy to inject credentials, keeping them out of the browser.
- **CORS and Domain Restrictions**: Configure your account to only accept widget calls from trusted domains.
- **Short DocId Lifespans**: Rely on the default 20-minute expiry to limit exposure of uploaded files. (only applies to Rest API’s - For MCP files are only used during lifetime of processing and then purged)

## Resources

Use the links below for deeper technical reference, pricing details, and support.

- **API Reference**  
  [TweekIT REST API Documentation](https://www.tweekit.io/docs/rest-api)  
  Full endpoint list, parameters, authentication methods, and sample code.

- **Widget API Reference**  
  [TweekIT Widget Documentation](https://www.tweekit.io/docs/widget-api)  
  Constructor options, properties, methods, and event listeners.

- **Pricing**  
  [TweekIT Pricing Guide](https://www.tweekit.io/pricing/)  
  Free tier details, paid plan tiers, and overage rates.

- **Support Contact**  
  Email: support@tweekit.io  
  Submit tickets for technical help, account issues, or feature requests.
