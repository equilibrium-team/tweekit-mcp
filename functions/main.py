from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from werkzeug.wrappers import Response as WsgiResponse
import httpx
from typing import Any, Dict
import logging
import os
import sys

# Ensure vendored dependencies are importable in both deploy and local analysis
_PKG_DIR = os.path.join(os.path.dirname(__file__), "packages")
if os.path.isdir(_PKG_DIR) and _PKG_DIR not in sys.path:
    sys.path.append(_PKG_DIR)

# Try to import Firebase Admin initialize; fall back to no-op when unavailable during analysis
try:
    from firebase_admin import initialize_app as _initialize_app
    def initialize_app(*args, **kwargs):
        return _initialize_app(*args, **kwargs)
except Exception:
    def initialize_app(*args, **kwargs):  # type: ignore
        return None

# Try to import FastMCP and types; fall back to light stubs for CLI analysis
try:
    from fastmcp import FastMCP
    from fastmcp.utilities.types import Image, File
    from fastmcp.server.http import create_streamable_http_app
except Exception:
    class FastMCP:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def tool(self, *args, **kwargs):  # decorator passthrough
            def _decorator(fn):
                return fn

            return _decorator

        def init_app(self, app):  # no-op for analysis
            return None

    class Image:  # type: ignore
        def __init__(self, data: bytes, format: str):
            self.data = data
            self.format = format

        def to_image_content(self):
            return {"image": True, "format": self.format, "size": len(self.data)}

    class File:  # type: ignore
        def __init__(self, data: bytes, filename: str, mime_type: str):
            self.data = data
            self.filename = filename
            self.mime_type = mime_type

        def to_file_content(self):
            return {"file": True, "filename": self.filename, "mime_type": self.mime_type, "size": len(self.data)}
    def create_streamable_http_app(*args, **kwargs):  # type: ignore
        raise RuntimeError("FastMCP HTTP app not available in analysis stub")

BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"

initialize_app()
# Global options for cost control and consistency
set_global_options(max_instances=10, region="us-west1")

mcp = FastMCP("TweekIT MCP Server - normalize almost any file for AI ingestion")

# Logging configuration (respect env LOG_LEVEL, default WARNING)
_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=getattr(logging, _log_level, logging.WARNING))
logger = logging.getLogger(__name__)

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
    timeout = httpx.Timeout(10.0, read=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            client.headers["ApiKey"] = apiKey
            client.headers["ApiSecret"] = apiSecret
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error fetching supported file formats for '%s': %s", ext, e)
            return {"error": f"Failed to fetch supported file formats. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error("Network error calling doctype: %s", e)
            return {"error": f"Network error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error in doctype")
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
    timeout = httpx.Timeout(20.0, read=60.0)
    async with httpx.AsyncClient(default_encoding="ascii", timeout=timeout) as client:
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

            content_type = (response.headers.get("content-type") or "").lower()
            if content_type.startswith("image/"):
                image_format = content_type.split("/")[-1]
                img_obj = Image(data=response.content, format=image_format)
                return img_obj.to_image_content()

            if content_type == "application/pdf" or outfmt.lower() == "pdf":
                file_obj = File(data=response.content, filename="output.pdf", mime_type="application/pdf")
                return file_obj.to_file_content()

            if content_type.startswith("application/") or content_type == "application/octet-stream":
                # Fallback for other binary types
                ext = outfmt.lower().strip(".") or "bin"
                mime = content_type if content_type else "application/octet-stream"
                file_obj = File(data=response.content, filename=f"output.{ext}", mime_type=mime)
                return file_obj.to_file_content()

            if content_type.startswith("application/json"):
                # Bubble up JSON responses (e.g., API error details)
                return response.json()

            return {"error": f"Unsupported content type in response: '{content_type or 'unknown'}'"}
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error converting document: status=%s", getattr(e.response, 'status_code', 'unknown'))
            return {"error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error("Network error during convert: %s", e)
            return {"error": "Network error"}
        except Exception as e:
            logger.exception("Unexpected error in convert")
            return {"error": f"An unexpected error occurred: {e}"}

try:
    # Build the ASGI app for MCP HTTP transport on path /mcp
    asgi_app = create_streamable_http_app(
        mcp,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=False,
        debug=False,
    )

    # Robust ASGI -> WSGI adapter with lifespan running on a background loop
    import asyncio
    import threading
    from typing import List, Tuple

    class _ASGIWorker:
        def __init__(self, app):
            self.app = app
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_loop, name="asgi-loop", daemon=True)
            self._startup_done = threading.Event()
            self.thread.start()
            # Start ASGI lifespan in the loop
            fut = asyncio.run_coroutine_threadsafe(self._lifespan_start(), self.loop)
            fut.result(timeout=30)
            self._startup_done.set()

        def _run_loop(self):
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        async def _lifespan_start(self):
            async def receive():
                # First call sends startup, then waits forever until shutdown
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "lifespan.startup"}
                await asyncio.sleep(3600)  # keep alive

            async def send(event):
                # Accept startup complete; ignore others
                return None

            sent = False
            scope = {"type": "lifespan", "asgi": {"version": "3.0"}}
            # Run the lifespan task without exiting
            self._lifespan_task = asyncio.create_task(self.app(scope, receive, send))
            # Wait until startup completes (the app will call send with startup complete)
            await asyncio.sleep(0)  # yield control to allow app to process
            # We can't directly catch a specific event here; but app won't error if OK
            return

        def __call__(self, environ, start_response):
            self._startup_done.wait(timeout=30)
            body = environ.get("wsgi.input").read() if environ.get("wsgi.input") else b""

            async def handle_http():
                status_code = 500
                headers: List[Tuple[str, str]] = []
                chunks: List[bytes] = []

                # Build HTTP scope
                server_protocol = environ.get("SERVER_PROTOCOL", "HTTP/1.1")
                http_version = server_protocol.split("/")[-1]
                path = environ.get("PATH_INFO", "")
                query = environ.get("QUERY_STRING", "")
                headers_list: list[tuple[bytes, bytes]] = []
                for k, v in list(environ.items()):
                    if k.startswith("HTTP_"):
                        name = k[5:].replace("_", "-").lower().encode("latin-1")
                        headers_list.append((name, str(v).encode("latin-1")))
                if environ.get("CONTENT_TYPE"):
                    headers_list.append((b"content-type", environ["CONTENT_TYPE"].encode("latin-1")))
                if environ.get("CONTENT_LENGTH"):
                    headers_list.append((b"content-length", environ["CONTENT_LENGTH"].encode("latin-1")))

                scope = {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": http_version,
                    "method": environ.get("REQUEST_METHOD", "GET"),
                    "scheme": environ.get("wsgi.url_scheme", "http"),
                    "path": path,
                    "raw_path": path.encode("latin-1"),
                    "query_string": query.encode("latin-1"),
                    "headers": headers_list,
                    "server": (environ.get("SERVER_NAME", ""), int(environ.get("SERVER_PORT", 0) or 0)),
                    "client": (environ.get("REMOTE_ADDR", ""), 0),
                }

                received = False

                async def receive():
                    nonlocal received
                    if not received:
                        received = True
                        return {"type": "http.request", "body": body, "more_body": False}
                    return {"type": "http.disconnect"}

                async def send(event):
                    nonlocal status_code, headers, chunks
                    if event["type"] == "http.response.start":
                        status_code = int(event["status"])  # type: ignore[arg-type]
                        headers = []
                        for k, v in event.get("headers", []) or []:
                            if isinstance(k, bytes):
                                k = k.decode("latin-1")
                            if isinstance(v, bytes):
                                v = v.decode("latin-1")
                            headers.append((k, v))
                    elif event["type"] == "http.response.body":
                        chunks.append(event.get("body", b""))

                await self.app(scope, receive, send)
                return status_code, headers, b"".join(chunks)

            fut = asyncio.run_coroutine_threadsafe(handle_http(), self.loop)
            status_code, headers, body_bytes = fut.result(timeout=120)
            start_response(f"{status_code} OK", [(k, v) for k, v in headers])
            return [body_bytes]

    wsgi_app = _ASGIWorker(asgi_app)
except Exception:
    logger.exception("Failed to initialize ASGI app")
    wsgi_app = None  # type: ignore

@https_fn.on_request()
def mcp_server(req: https_fn.Request) -> https_fn.Response:
    if wsgi_app is None:
        return WsgiResponse("Server not initialized", status=500)
    # Delegate the request environ to the ASGI->WSGI wrapped app
    try:
        return WsgiResponse.from_app(wsgi_app, req.environ)
    except Exception:
        logger.exception("Unhandled error in MCP handler")
        return WsgiResponse("Internal Server Error", status=500)


@https_fn.on_request()
def health(req: https_fn.Request) -> https_fn.Response:
    return WsgiResponse("ok", status=200, content_type="text/plain")
