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

- Supports **450+** file types for seamless ingestion and conversion, **leveraging a core engine refined over two decades to handle dynamic imaging and video delivery.**
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
- [Rate Limits and Pricing](#rate-limits-and-pricing)
- [Core Concepts](#core-concepts)
- [API Reference (MCP-Ready)](#api-reference-mcp-ready)
- [Widget API Integration](#widget-api-integration)
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
   git clone https://github.com/your-username/mcpserver.git
   cd mcpserver
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
[Pricing and Signup here](https://www.tweekit.io/) to access your API credentials and start using the service.

### Step 2: Choose Your Authentication Method

TweekIT supports multiple authentication methods. Both work with the MCP integration.

- **AppID** – Fastest way to get started for quick tests and prototyping
- **API Key and Secret** – Recommended for production use, more secure and easier to control access

You will find these values in your account dashboard after sign up. Keep them safe and never expose them in client-side code.

### Step 3: Make Your First API Call

Below is a minimal working Node.js example that uploads an image, previews the transformation, and downloads the result. This example uses API Key and Secret authentication.

```javascript
const fetch = require('node-fetch');
const fs = require('fs');
const FormData = require('form-data');

const headers = {
  apikey: '{Your API Key}',
  apisecret: '{Your API Secret}'
};

async function uploadFile(filePath, fileName) {
  const url = 'https://www.tweekit.io/tweekit/api/image/upload';
  const formData = new FormData();
  formData.append('name', fileName);
  formData.append('file', fs.createReadStream(filePath));
  const response = await fetch(url, { method: 'POST', headers, body: formData });
  const docID = response.headers.get('x-tweekit-docid');
  return docID;
}

async function previewImage(docID) {
  const url = `https://www.tweekit.io/tweekit/api/image/preview/${docID}`;
  const options = {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json;charset=UTF-8' },
    body: JSON.stringify({ width: 300, height: 300, fmt: 'png' })
  };
  const response = await fetch(url, options);
  const buffer = await response.buffer();
  fs.writeFileSync('output.png', buffer);
}

(async () => {
  const docID = await uploadFile('example.jpg', 'example.jpg');
  await previewImage(docID);
  console.log('Transformation complete. File saved as output.png');
})();
```

### Step 4: See It in Action

You can explore TweekIT visually before writing any code. The live demo lets you upload files, apply transformations, and download the results instantly.

- [Open the Live Demo](https://www.tweekit.io/demo/)
- [View Use Case Examples](https://www.tweekit.io/use-case/) for real workflows and code samples

## Authentication

TweekIT supports multiple authentication methods so you can start quickly while maintaining security best practices as your project grows.

### Recommended Default: API Key + Secret

This is the most secure and flexible option. Use this for all production deployments.

**Steps:**

1. Generate your API Key and Secret in your TweekIT account settings.
2. Store them securely — never commit to source control.
3. Use server-side code or a reverse proxy to inject credentials into requests.

**Example (Node.js):**

```javascript
const headers = {
  "apikey": "{Your API Key}",
  "apisecret": "{Your API Secret}"
};
```

**Security Tips:**

- Always use a reverse proxy or other server-side method to protect credentials.
- Never embed secrets in client-side code.

### AppID (Quick Prototyping)

Use this for rapid experimentation, demos, or proof-of-concept work where security is less critical.

**Steps:**

1. Sign up for a free account.
2. Register your widget to receive a domain-specific AppID.
3. Pass the AppID in your widget constructor.

**Example:**

```javascript
var tweekit = new Tweekit('#canvas0', {
  appId: '{Your App ID}'
});
```

### Bearer Token (auth.cpucoin.io)

If you are integrating with CPUcoin's decentralized compute network, you can obtain a bearer token via `auth.cpucoin.io` and use it in the `Authorization` header.

**Example:**

```javascript
const headers = {
  "Authorization": "Bearer {YourToken}"
};
```

**Next Steps:**  
Once authenticated, you can:

- Upload media
- Transform and preview results
- Download outputs

## Server and Hosting

### Hosted ready endpoints

Used for testing and free trials:

- [**https://mcp-tweekit-728625953614.us-west1.run.app/mcp/version**](https://mcp-tweekit-728625953614.us-west1.run.app/mcp/version)

Production for returning supported reader formats, or if a specific format is readable with a param request:

- [**https://mcp-tweekit-728625953614.us-west1.run.app/mcp/doctype**](https://mcp-tweekit-728625953614.us-west1.run.app/mcp/doctype)

Production for executing conversion requests:

- [**https://mcp-tweekit-728625953614.us-west1.run.app/mcp/convert**](https://mcp-tweekit-728625953614.us-west1.run.app/mcp/convert)

### MCP Tool Installation

You can run the TweekIT MCP server locally or connect to a hosted instance. The local option is recommended for development and testing.

**Local Installation**

```bash
git clone https://github.com/your-org/tweekit-mcp.git
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

**Remote Server Override**  
If you have access to a hosted TweekIT MCP endpoint, update your MCP host configuration to point to that server’s base URL.  
Example (VS Code MCP config):

```json
{
  "mcpServers": {
    "tweekit": {
      "url": "https://mcp.yourdomain.com"
    }
  }
}
```

**Local Development Mode**  
By default, `server.py` will bind to `localhost` on port 8080. You can override the port with the `PORT` environment variable:

```bash
PORT=9090 uv run server.py
```

## Rate Limits and Pricing

TweekIT offers a generous free tier so you can explore and integrate without cost.

### Free Tier

- **10,000 API calls** included at no charge.
- Full access to all core upload, preview, and download capabilities.
- No credit card required to start.

### Paid Plans

If you exceed the free tier limit, you can upgrade to a paid plan at any time.  
See the full pricing guide for details:  
[https://www.tweekit.io/pricing/](https://www.tweekit.io/pricing/)

### Handling Rate Limit Errors

When you reach your monthly quota, the API will respond with an HTTP `429 Too Many Requests` status.

**MCP Integration Tip**:  
Your MCP client should:

1. Catch `429` responses.
2. Surface a clear error message to the user.
3. Recommend upgrading the plan or waiting until the quota resets.

Example error payload:

```json
{
  "error": "rate_limit_exceeded",
  "message": "You have reached your 10,000 call monthly limit."
}
```

## Core Concepts

Understanding these core concepts will help you get the most out of TweekIT in an MCP workflow.

### DocId

Every upload is assigned a unique **DocId**.

- The DocId is used to reference your file in all subsequent preview, transform, and download requests.
- DocIds expire **20 minutes** after upload. Once expired, the file is permanently deleted and cannot be retrieved.

### Upload → Preview → Download Flow

TweekIT uses a simple, stateless, three-step process:

1. **Upload** the file and receive a DocId.
2. **Preview/Transform** using the DocId and transformation parameters.
3. **Download** the final transformed file in the desired format.

This pattern works for both the REST API and the MCP tool, and ensures predictable, repeatable workflows.

### Transformations

TweekIT supports a wide range of transformations, applied at preview time:

- **Resize** by width and height
- **Crop** by coordinates or aspect ratio
- **Reformat** to a different file type
- **Alpha channel** transparency control
- **Elliptical crops** for circular or oval shapes
- **Background color** fills for transparent or padded areas

Multiple transformations can be applied in a single request.

### Stateless Processing

TweekIT does not store your files persistently.

- Every transformation request works from the uploaded file *in memory*.
- Once the DocId expires, sozinho the file and all transformation data are purged.
- This design ensures minimal storage overhead and stronger privacy for sensitive files.
- Data in transit is encrypted all ways via SSL.

## API Reference (MCP-Ready)

TweekIT provides both REST API endpoints and Widget API methods that can be accessed directly or have a critical subset in the MCP server. All methods require authentication (see Section 3: Authentication).

### Upload File

**REST Endpoint**

`POST /api/image/upload`

**Purpose**  
Uploads a single file and returns a unique DocId for use in transformations and downloads.

**Note: The MCP server does not require an upload endpoint because the document is sent in Base-64 form with every conversion request. (See size limits in the pricing plans)**

**Node.js Example**

```javascript
const fetch = require('node-fetch');
const fs = require('fs');
const FormData = require('form-data');

const headers = {
  "apikey": "{Your API Key}",
  "apisecret": "{Your API Secret}"
};

async function uploadFile(filePath, fileName) {
  const url = 'https://www.tweekit.io/tweekit/api/image/upload';
  const formData = new FormData();
  formData.append("name", fileName);
  formData.append("file", fs.createReadStream(filePath));
  const response = await fetch(url, { method: 'POST', headers, body: formData });
  const docID = response.headers.get('x-tweekit-docid');
  return docID;
}
```

**Example Response**

```json
{
  "docId": "81736373272E49248519DE8C203A6001"
}
```

### Preview / Transform File

**REST Endpoint**

`POST /api/image/preview/{docId}`

`GET  /api/image/preview/{docId}`

**Purpose**  
Applies transformations to the uploaded file and returns the preview image.

**Parameters**

- `width` (integer): Scale output image width.
- `height` (integer): Scale output image height.
- `fmt` (string): Output format (jpg, png, webp, gif, etc.).
- `bgcolor` (string): Hex or color name for background fill.
- `page` (integer): Page number for multi-page formats.
- `cropX`, `cropY`, `cropWidth`, `cropHeight` (integers): Crop coordinates.

**Node.js Example**

```javascript
async function previewImage(docId) {
  const url = `https://www.tweekit.io/tweekit/api/image/preview/${docId}`;
  const options = {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json;charset=UTF-8' },
    body: JSON.stringify({ width: 300, height: 300, fmt: 'png', bgcolor: '#FFFFFF' })
  };
  const response = await fetch(url, options);
  return await response.buffer();
}
```

### Download File

**REST Endpoint**

`GET /api/image/{docId}`

**Purpose**  
Retrieves the fully transformed file.

**Supported Output Formats**

- JPEG (`.jpg`)
- PNG (`.png`)
- WebP (`.webp`)
- GIF (`.gif`)
- TIFF (`.tif`)
- PDF (`.pdf`) (first page image render when image is requested, or complete complex PDF can be generated from any file with complex data such as .docx, .doc, .ppt, .pptx, etc.)

**Example**

```javascript
async function downloadFile(docId, outputPath) {
  const url = `https://www.tweekit.io/tweekit/api/image/${docId}`;
  const response = await fetch(url, { headers });
  const buffer = await response.buffer();
  fs.writeFileSync(outputPath, buffer);
}
```

### Other Methods

#### Widget API

- **`getParams()`** – Returns the current transformation parameters.
- **`reset()`** – Resets the widget state and clears the current file.
- **`result()`** – Retrieves the transformed image as a Blob.

#### Event Listeners

- **`render`** – Triggered when the widget finishes rendering.
- **`update`** – Fired when transformation parameters change.
- **`propertychange`** – Fired when widget properties are updated.

## Widget API Integration

TweekIT offers a JavaScript-based Widget API that can be embedded into MCP webviews for interactive media processing. The widget provides an end-user interface for uploading, previewing, and transforming files without writing REST calls directly.

### When to Use Widget vs REST

- **Use the Widget API** when you want an interactive visual interface for users to manipulate images directly inside your MCP environment.
- **Use the REST API** when you need automated or backend processing without direct user interaction.
- Many workflows combine both: the widget handles interactive cropping or resizing, then REST endpoints finalize transformations or run batch processing.

### Constructor Parameters

The widget is created by instantiating `Tweekit(selector, options)`.

**`selector`**  
A CSS selector pointing to the HTML element that will contain the widget.

**`options`** (object)

| Parameter    | Type    | Description                                               |
|--------------|---------|-----------------------------------------------------------|
| `appId`      | string  | Application ID for authentication                         |
| `message`    | string  | Displayed when there is no image loaded                   |
| `headers`    | object  | Name-value pairs for HTTP headers (e.g., API Key and Secret) |
| `cropOnRender` | boolean | Whether to display the crop tool immediately after rendering |
| `cropWidth`  | number  | Initial width of the crop tool                            |
| `cropHeight` | number  | Initial height of the crop tool                           |

### Properties & Methods

- **`getParams()`** – Returns the current transformation parameters.
- **`reset()`** – Clears the widget state and removes the loaded file.
- **`result()`** – Returns the transformed file as a Blob.
- **`render()`** – Forces the widget to re-render with current parameters.

## Use Cases

Below are common workflows where TweekIT improves reliability and speed in media processing. Each example shows both REST API and MCP usage patterns.

### 1. Employee Headshot Automation

Automatically crop and resize employee photos into a consistent headshot format.

**REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 300, "height": 300, "cropWidth": 300, "cropHeight": 300, "fmt": "png"}'
```

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
  },
  "jsonrpc": "2.0",
  "id": 4
}
```

### 2. KYC Photo Ingestion and Normalization

Process identity document photos into standardized formats for automated verification.

**REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 600, "height": 400, "fmt": "webp", "bgcolor": "#FFFFFF"}'
```

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
  },
  "jsonrpc": "2.0",
  "id": 4
}
```

### 3. Social Media and E-Commerce Image Resizing

Generate platform-specific product images with correct aspect ratios and background fills.

**REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 1080, "height": 1080, "fmt": "jpg", "bgcolor": "#FFFFFF"}'
```

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
  },
  "jsonrpc": "2.0",
  "id": 4
}
```

### 4. Cross-Platform Asset Conversion

Convert files between formats for compatibility across different tools and workflows.

**REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"fmt": "webp"}'
```

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
  },
  "jsonrpc": "2.0",
  "id": 4
}
```

### 5. Multi-page Document conversion to PDF

Convert complex document or legacy filetypes from original formats into PDF files for compatibility into your current AI workflow.

**REST Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"fmt": "pdf", noRasterize: true}'
```

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
  },
  "jsonrpc": "2.0",
  "id": 4
}
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

**Expired DocId**

- **Cause**: The DocId has exceeded its 20-minute lifespan.
- **Resolution**: Re-upload the file to obtain a new DocId.
- **HTTP Status**: `404 Not Found`
- **Error Example**:

  ```json
  {
    "error": "docid_expired",
    "message": "The DocId has expired. Please upload the file again."
  }
  ```

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

### Chaining Transformations

You can apply multiple transformations in a single request by including all parameters in the preview or transform call. This reduces network round trips and ensures the DocId lifespan is used efficiently.

**Example**

```bash
curl -X POST "https://www.tweekit.io/tweekit/api/image/preview/{docId}" \
  -H "apikey: {Your API Key}" \
  -H "apisecret: {Your API Secret}" \
  -H "Content-Type: application/json;charset=UTF-8" \
  -d '{"width": 512, "height": 512, "fmt": "webp", "cropWidth": 400, "cropHeight": 400, "bgcolor": "#000000"}'
```

**Why**: Useful when you need to crop, resize, and reformat in one step. ***Crop is only available when using the widget currently.***

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
