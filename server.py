import asyncio
import httpx
import logging
import os

from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from mcp.types import ImageContent
from typing import Any, Dict

BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
#BASE_URL = "http://localhost:16377/api/image/"

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.WARNING)

mcp = FastMCP("TweekIT MCP Server - normalize almost any file for AI ingestion")

@mcp.tool()
async def version() -> str:
    """Get current version of the TweekIT API."""
    url = f"{BASE_URL}version"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text

@mcp.tool()
async def doctype(ext: str, apiKey: str, apiSecret: str) -> Dict[str, Any]:
    """
    Retrieve a list of supported file formats or map a file extension to its document type.

    Args:
        ext (str): The file extension to query (e.g., 'jpg', 'pdf').
        apiKey (str): The API key for authentication.
        apiSecret (str): The API secret for authentication.

    Returns:
        Dict[str, Any]: A dictionary containing the supported file formats or an error message.
    """
    url = f"{BASE_URL}doctype"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            client.headers["ApiKey"] = apiKey
            client.headers["ApiSecret"] = apiSecret
            response = await client.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # FastMCP will automatically serialize this dict to JSON and set the mime_type
            return response.json()

        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching supported file formats given '{ext}': {e}")
            return {"error": f"Failed to fetch user data. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            print(f"Network error fetching supported file formats given '{ext}': {e}")
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
    width: int = 0,
    height: int = 0,
    page: int = 1,
    bgcolor: str = ""
) -> Any:
    """
    Convert a base64-encoded document to the specified output format.

    Args:
        apiKey (str): The API key for authentication.
        apiSecret (str): The API secret for authentication.
        inext (str): The input file extension (e.g., 'jpg', 'png').
        outfmt (str): The desired output format (e.g., 'pdf', 'png').
        blob (str): The base64-encoded document data.
        width (int, optional): The desired width of the output. Defaults to 0 (no resizing).
        height (int, optional): The desired height of the output. Defaults to 0 (no resizing).
        page (int, optional): The page number to convert (for multi-page documents). Defaults to 1.
        bgcolor (str, optional): The background color to apply to documents with transparent backgroundsfor the output (e.g., 'FFFFFF'). Defaults to an empty string -.

    Returns:
        Any: The converted document or an error message.
    """
    url = BASE_URL
    async with httpx.AsyncClient(default_encoding="ascii") as client:
        try:
            client.headers["ApiKey"] = apiKey
            client.headers["ApiSecret"] = apiSecret
            response = await client.post(url, json={
                "Fmt": outfmt,
                "Width": width,
                "Height": height,
                "BgColor": bgcolor,
                "Page": page,
                "DocDataType": inext,
                "DocData": blob
            })
            response.raise_for_status()  # Raise an exception for HTTP errors

            content_type = response.headers.get("content-type")
            if content_type and "image/" in content_type:
                image_format = content_type.split("/")[-1]
                img_obj = Image(data=response.content, format=image_format)
                return img_obj.to_image_content()

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

# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Use this to add two numbers together.

#     Args:
#         a: The first number.
#         b: The second number.

#     Returns:
#         The sum of the two numbers.
#     """
#     logger.info(f">>> 🛠️ Tool: 'add' called with numbers '{a}' and '{b}'")
#     return a + b

# @mcp.tool()
# def subtract(a: int, b: int) -> int:
#     """Use this to subtract two numbers.

#     Args:
#         a: The first number.
#         b: The second number.

#     Returns:
#         The difference of the two numbers.
#     """
#     logger.info(f">>> 🛠️ Tool: 'subtract' called with numbers '{a}' and '{b}'")
#     return a - b

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
