from firebase_functions import https_fn
from firebase_admin import initialize_app
from fastmcp import FastMCP
from flask import Flask
import httpx
from typing import Any, Dict
from fastmcp.utilities.types import Image

BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"

initialize_app()

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
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"Failed to fetch user data. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}
        except Exception as e:
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
            response.raise_for_status()

            content_type = response.headers.get("content-type")
            if content_type and "image/" in content_type:
                image_format = content_type.split("/")[-1]
                img_obj = Image(data=response.content, format=image_format)
                return img_obj.to_image_content()

            return {"error": f"Unsupported content type in response: '{content_type}'"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            return {"error": "Network error"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

app = Flask(__name__)
mcp.init_app(app)

@https_fn.on_request()
def mcp_server(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()
