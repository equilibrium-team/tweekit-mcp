import asyncio
import httpx
import logging
import os
import re
from urllib.parse import quote_plus, urlparse

from fastmcp import FastMCP
from fastmcp.utilities.types import Image, File
from typing import Any, Dict, List

BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
#BASE_URL = "http://localhost:16377/api/image/"

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.WARNING)

mcp = FastMCP("TweekIT MCP Server - normalize almost any file for AI ingestion")

@mcp.resource("config://tweekit-version")
async def version() -> str:
    """Get current version of the TweekIT API."""
    url = f"{BASE_URL}version"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

@mcp.tool()
async def doctype(apiKey: str, apiSecret: str, extension: str = "*") -> Dict[str, Any]:
    """
    Retrieve a list of supported file formats or map a file extension to its document type.

    Args:
        apiKey (str): The API key for authentication.
        apiSecret (str): The API secret for authentication.
        extension (str): The file extension to query (e.g., 'jpg', 'pdf') or leave off or use '*' to return all supported input formats.

    Returns:
        Dict[str, Any]: A dictionary containing the supported file formats or an error message.
    """
    url = f"{BASE_URL}doctype"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers={"ApiKey": apiKey, "ApiSecret": apiSecret}, params={"extension": extension})
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            if isinstance(data, dict):
                return data
            else:
                return {"result": data}

        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching supported file formats given '{extension}': {e}")
            return {"error": f"Failed to fetch user data. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            print(f"Network error fetching supported file formats given '{extension}': {e}")
            return {"error": f"Network error: {e}"}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {"error": f"An unexpected error occurred: {e}"}

@mcp.tool()
async def convert(
    apiKey: str,
    apiSecret: str,
    inext: str,
    outfmt: str,
    blob: str,
    noRasterize: bool = False,
    width: int = 0,
    height: int = 0,
    x1: int = 0,
    y1: int = 0,
    x2: int = 0,
    y2: int = 0,
    page: int = 1,
    alpha: bool = True,
    bgColor: str = ""
) -> Any:
    """
    Convert a base64-encoded document to the specified output format.

    Args:
        apiKey (str): The API key for authentication.
        apiSecret (str): The API secret for authentication.
        inext (str): The input file extension (e.g., 'jpg', 'png').
        outfmt (str): The desired output format. Current supported types include 'jpg', 'png', 'webp', 'bmp', and 'pdf'.
        blob (str): The base64-encoded document data.
        noRasterize (bool, optional): For input document formats that are not raster images, do not rasterize the document - return it as a PDF. (outfmt must be set to pdf). The parameters listed below are ignored when doing document to PDF conversions.
        width (int, optional): The desired width of the output. Defaults to 0 (no resizing).
        height (int, optional): The desired height of the output. Defaults to 0 (no resizing).
        x1, y1, x2, y2 (int, optional): The crop region of the input. The raster is scaled after the crop is applied. The x1 and y1 values can be negative, which adds padding to the top and left; the x2 amd y2 can be greater than the original raster size, which adds padding to the right and bottom. Defaults to all 0 (no cropping).
        page (int, optional): The page number to convert (for multi-page documents). Defaults to 1.
        bgcolor (str, optional): The background color to apply when padding it required or when alpha is false and the input document uses an alpha channel (e.g., 'FFFFFF' or '#FFFFFF'). Defaults to 000000 (black).
        alpha (bool, optional): Whether to preserve the alpha channel (transparency) in the output. Defaults to true. Alpha is only preserved for output formats which support it, regardless of this setting.

    Returns:
        Any: The converted document or an error message.
    """
    url = BASE_URL
    # Convert bgcolor from hex string (e.g., '#FFFFFF' or 'FFFFFF') to integer
    bg = 0
    if bgColor:
        hexstr = bgColor.lstrip('#')
        try:
            bg = int(hexstr, 16)
        except ValueError:
            bg = 0  # fallback to black if invalid

    # Call TweekIT
    async with httpx.AsyncClient(default_encoding="ascii", timeout=60.0) as client:
        try:
            client.headers["ApiKey"] = apiKey
            client.headers["ApiSecret"] = apiSecret
            response = await client.post(url, json={
                "Fmt": outfmt,
                "Width": width,
                "Height": height,
                "X1": x1,
                "Y1": y1,
                "X2": x2,
                "Y2": y2,
                "Bg": bg,
                "Alpha": alpha,
                "Page": page,
                "NoRasterize": noRasterize,
                "DocDataType": inext,
                "DocData": blob
            })
            response.raise_for_status()  # Raise an exception for HTTP errors

            content_type = response.headers.get("content-type")
            if content_type:
                if "image/" in content_type:
                    image_format = content_type.split("/")[-1]
                    return Image(data=response.content, format=image_format)
                elif content_type == "application/pdf":
                    return File(data=response.content, format="pdf")

            # Default case if content type is unknown
            return {"error": f"Unsupported content type in response: '{content_type}'"}

        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching document from {url}: {e}")
            return {"error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            print(f"Network error fetching document from {url}: {e}")
            return {"error": "Network error"}
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool()
async def fetch(url: str) -> Any:
    """Fetch a URL and return content.

    - Images return as FastMCP Image.
    - PDFs return as File(format="pdf").
    - Text/JSON return as a JSON payload with metadata and text.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return {"error": "Unsupported URL scheme. Use http or https."}

    headers = {
        "User-Agent": "tweekit-mcp/0.1 (+https://github.com/equilibrium-team/tweekit-mcp)"
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "").lower()

            if ct.startswith("image/"):
                return Image(data=resp.content, format=ct.split("/")[-1])
            if ct.startswith("application/pdf"):
                return File(data=resp.content, format="pdf")
            if ct.startswith("text/") or "json" in ct:
                text = resp.text
                return {
                    "url": str(url),
                    "status": resp.status_code,
                    "content_type": ct,
                    "text": text,
                }
            # Fallback for other binary types
            return File(data=resp.content, format="bin")
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"Network error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


@mcp.tool()
async def search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Simple web search using DuckDuckGo HTML endpoint.

    Returns a list of {title, url, snippet} objects. Best‑effort parsing.
    """
    max_results = max(1, min(int(max_results), 10))
    q = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    headers = {
        "User-Agent": "tweekit-mcp/0.1 (+https://github.com/equilibrium-team/tweekit-mcp)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text

        # Very light parsing for result blocks
        items: List[Dict[str, str]] = []
        # Anchor tags have class result__a and href; snippets often in result__snippet
        # This is heuristic and may change.
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = m.group(1)
            title = re.sub("<.*?>", "", m.group(2))
            # Try to find a nearby snippet
            start = m.end()
            snippet_match = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(.*?)</div>', html[start:start+2000], re.I | re.S)
            snippet_html = snippet_match.group(1) if snippet_match and snippet_match.group(1) else (snippet_match.group(2) if snippet_match and snippet_match.group(2) else "")
            snippet = re.sub("<.*?>", "", snippet_html)
            items.append({"title": title.strip(), "url": href, "snippet": snippet.strip()})
            if len(items) >= max_results:
                break

        return {"query": query, "results": items}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"Network error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}


if __name__ == "__main__":
    logger.info(f"🚀 TweekIT MCP server started on port {os.getenv('PORT', 8080)}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    try:
        asyncio.run(
            mcp.run_async(
                transport="streamable-http",
                host="0.0.0.0",
                port=os.getenv("PORT", 8080),
            )
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred while running the server: {e}")
        raise
    finally:
        logger.info("Server shutdown complete.")
