from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from werkzeug.wrappers import Response as WsgiResponse
import httpx
from typing import Any, Dict, Optional
import logging
import os
import re
import sys

# Ensure vendored dependencies are importable in both deploy and local analysis
_PKG_DIR = os.path.join(os.path.dirname(__file__), "packages")
if os.path.isdir(_PKG_DIR) and _PKG_DIR not in sys.path:
    sys.path.append(_PKG_DIR)

try:
    from firebase_admin import initialize_app as _initialize_app

    def initialize_app(*args, **kwargs):
        return _initialize_app(*args, **kwargs)
except Exception:
    def initialize_app(*args, **kwargs):  # type: ignore
        return None

try:
    from fastmcp import FastMCP
    from fastmcp.server.dependencies import get_http_headers
    from fastmcp.utilities.types import Image, File
    from fastmcp.server.http import create_streamable_http_app
except Exception:
    class FastMCP:  # type: ignore
        def __init__(self, *args, **kwargs):
            # Deliberate no-op stub used only during Firebase CLI static discovery.
            self._stub = True

        def tool(self, *args, **kwargs):
            def _decorator(fn):
                return fn
            return _decorator

        def init_app(self, app):
            return None

    def get_http_headers(*args, **kwargs) -> Dict[str, str]:  # type: ignore
        return {}

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

from urllib.parse import urlparse


def _resolve_functions_base_url() -> str:
    raw = (os.getenv("TWEEKIT_API_BASE_URL") or "https://dapp.tweekit.io/tweekit/api/image/").strip()
    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    hostname = (parsed.hostname or "").lower()
    if scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password:
        raise ValueError(
            "Invalid TWEEKIT_API_BASE_URL: must include http(s) scheme and hostname without embedded credentials."
        )
    if scheme == "http" and hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(
            "Plain HTTP TWEEKIT_API_BASE_URL is only permitted for loopback endpoints; "
            "use HTTPS for remote TweekIT gateways."
        )
    return raw.rstrip("/") + "/"


BASE_URL = _resolve_functions_base_url()
_FORMAT_RE = re.compile(r"^[A-Za-z0-9]{1,16}$")

initialize_app()
set_global_options(max_instances=10, region="us-west1")

mcp = FastMCP("TweekIT MCP Server - normalize almost any file for AI ingestion")

_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=getattr(logging, _log_level, logging.WARNING))
logger = logging.getLogger(__name__)


def _resolve_request_credentials() -> tuple[str, str]:
    req_headers = get_http_headers(
        include={"apikey", "apisecret", "x-api-key", "x-api-secret", "authorization"}
    )
    auth = (req_headers.get("authorization") or "").strip()
    bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    header_key = (
        req_headers.get("apikey")
        or req_headers.get("x-api-key")
        or bearer
        or ""
    ).strip()
    header_secret = (
        req_headers.get("apisecret")
        or req_headers.get("x-api-secret")
        or ""
    ).strip()
    if header_key or header_secret:
        if not (header_key and header_secret):
            raise RuntimeError("Incomplete TweekIT HTTP header credentials: supply both ApiKey and ApiSecret headers.")
        return header_key, header_secret

    allow_http_env = os.getenv("TWEEKIT_ALLOW_ENV_CREDENTIALS_OVER_HTTP", "0").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if not allow_http_env:
        raise RuntimeError("Missing TweekIT HTTP header credentials: supply both ApiKey and ApiSecret headers.")

    env_key = (os.getenv("TWEEKIT_API_KEY") or "").strip()
    env_secret = (os.getenv("TWEEKIT_API_SECRET") or "").strip()
    if not env_key or not env_secret:
        raise RuntimeError("Missing TweekIT credentials in HTTP headers (ApiKey/ApiSecret) or environment.")
    return env_key, env_secret


@mcp.tool()
async def version() -> str:
    """Get current version of the TweekIT API."""
    url = f"{BASE_URL}version"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


@mcp.tool()
async def doctype(ext: str = "*") -> Dict[str, Any]:
    """Retrieve supported file formats or map a file extension to its document type."""
    cleaned_ext = "*" if (ext or "").strip() in {"", "*"} else ext.strip().lstrip(".").lower()
    if cleaned_ext != "*" and not _FORMAT_RE.fullmatch(cleaned_ext):
        return {"error": "Invalid file extension."}
    try:
        api_key, api_secret = _resolve_request_credentials()
    except RuntimeError as exc:
        return {"error": str(exc)}

    url = f"{BASE_URL}doctype"
    timeout = httpx.Timeout(10.0, read=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            client.headers["ApiKey"] = api_key
            client.headers["ApiSecret"] = api_secret
            response = await client.get(url, params={"extension": cleaned_ext})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error fetching supported file formats for '%s': %s", cleaned_ext, e)
            return {"error": f"Failed to fetch supported file formats. Status: {e.response.status_code}"}
        except httpx.RequestError:
            logger.error("Network error calling doctype")
            return {"error": "Network error"}
        except Exception:
            logger.exception("Unexpected error in doctype")
            return {"error": "An unexpected error occurred"}


@mcp.tool()
async def convert(
    inext: str,
    outfmt: str,
    blob: str,
    width: int = 0,
    height: int = 0,
    page: int = 1,
    bgcolor: str = "",
) -> Any:
    """Convert a base64-encoded document to the specified output format."""
    safe_inext = (inext or "").strip().lstrip(".").lower()
    safe_outfmt = (outfmt or "").strip().lstrip(".").lower()
    if not _FORMAT_RE.fullmatch(safe_inext) or not _FORMAT_RE.fullmatch(safe_outfmt):
        return {"error": "Invalid input or output format token."}
    if not blob or len(blob) > 70 * 1024 * 1024:
        return {"error": "Invalid or oversized base64 payload."}

    try:
        api_key, api_secret = _resolve_request_credentials()
    except RuntimeError as exc:
        return {"error": str(exc)}

    url = BASE_URL
    timeout = httpx.Timeout(20.0, read=60.0)
    async with httpx.AsyncClient(default_encoding="ascii", timeout=timeout) as client:
        try:
            client.headers["ApiKey"] = api_key
            client.headers["ApiSecret"] = api_secret
            response = await client.post(
                url,
                json={
                    "Fmt": safe_outfmt,
                    "Width": width,
                    "Height": height,
                    "BgColor": bgcolor,
                    "Page": page,
                    "DocDataType": safe_inext,
                    "DocData": blob,
                },
            )
            response.raise_for_status()

            content_type = (response.headers.get("content-type") or "").lower()
            if content_type.startswith("image/"):
                image_format = content_type.split("/")[-1].split(";")[0].strip()
                img_obj = Image(data=response.content, format=image_format)
                return img_obj.to_image_content()

            if content_type == "application/pdf" or safe_outfmt == "pdf":
                file_obj = File(data=response.content, filename="output.pdf", mime_type="application/pdf")
                return file_obj.to_file_content()

            if content_type.startswith("application/") or content_type == "application/octet-stream":
                mime = content_type if content_type else "application/octet-stream"
                file_obj = File(data=response.content, filename=f"output.{safe_outfmt}", mime_type=mime)
                return file_obj.to_file_content()

            if content_type.startswith("application/json"):
                return response.json()

            return {"error": f"Unsupported content type in response: '{content_type or 'unknown'}'"}
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error converting document: status=%s", getattr(e.response, "status_code", "unknown"))
            return {"error": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError:
            logger.error("Network error during convert")
            return {"error": "Network error"}
        except Exception:
            logger.exception("Unexpected error in convert")
            return {"error": "An unexpected error occurred"}


try:
    asgi_app = create_streamable_http_app(
        mcp,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        debug=False,
    )

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
            fut = asyncio.run_coroutine_threadsafe(self._lifespan_start(), self.loop)
            fut.result(timeout=30)
            self._startup_done.set()

        def _run_loop(self):
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        async def _lifespan_start(self):
            async def receive():
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "lifespan.startup"}
                await asyncio.sleep(3600)

            async def send(event):
                return None

            sent = False
            scope = {"type": "lifespan", "asgi": {"version": "3.0"}}
            self._lifespan_task = asyncio.create_task(self.app(scope, receive, send))
            await asyncio.sleep(0)
            return

        def __call__(self, environ, start_response):
            self._startup_done.wait(timeout=30)
            body = environ.get("wsgi.input").read() if environ.get("wsgi.input") else b""

            async def handle_http():
                status_code = 500
                headers: List[Tuple[str, str]] = []
                chunks: List[bytes] = []

                server_protocol = environ.get("SERVER_PROTOCOL", "HTTP/1.1")
                http_version = server_protocol.split("/")[-1]
                raw_path = environ.get("PATH_INFO", "")
                path = "/mcp" if raw_path == "/mcp/" else raw_path
                query = environ.get("QUERY_STRING", "")
                headers_list: list[tuple[bytes, bytes]] = []
                forwarded_proto: Optional[str] = None
                for k, v in list(environ.items()):
                    if k.startswith("HTTP_"):
                        name_str = k[5:].replace("_", "-").lower()
                        if name_str == "x-forwarded-proto":
                            forwarded_proto = str(v).split(",", 1)[0].strip().lower()
                        headers_list.append((name_str.encode("latin-1"), str(v).encode("latin-1")))
                if environ.get("CONTENT_TYPE"):
                    headers_list.append((b"content-type", environ["CONTENT_TYPE"].encode("latin-1")))
                if environ.get("CONTENT_LENGTH"):
                    headers_list.append((b"content-length", environ["CONTENT_LENGTH"].encode("latin-1")))

                scheme = forwarded_proto if forwarded_proto in {"https", "http"} else environ.get("wsgi.url_scheme", "https")
                scope = {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": http_version,
                    "method": environ.get("REQUEST_METHOD", "GET"),
                    "scheme": scheme,
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
    try:
        return WsgiResponse.from_app(wsgi_app, req.environ)
    except Exception:
        logger.exception("Unhandled error in MCP handler")
        return WsgiResponse("Internal Server Error", status=500)


@https_fn.on_request()
def health(req: https_fn.Request) -> https_fn.Response:
    return WsgiResponse("ok", status=200, content_type="text/plain")
