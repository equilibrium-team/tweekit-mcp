import base64
import os
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from server import _resolve_extension, recommend_ai_format

# --- Configuration ---
DEFAULT_BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
BASE_URL = os.getenv("TWEEKIT_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"
DEFAULT_API_KEY = os.getenv("TWEEKIT_API_KEY")
DEFAULT_API_SECRET = os.getenv("TWEEKIT_API_SECRET")
# This base URL should NOT have /mcp, as it's for the root API endpoints
PUBLIC_API_BASE_URL = os.getenv("PLUGIN_PUBLIC_BASE_URL", "").rstrip("/")
LOGO_URL = os.getenv("PLUGIN_LOGO_URL")

DEFAULT_CSP = (
    "default-src 'self'; "
    "connect-src 'self' https://*.tweekit.io https://tweekit.io https://html.duckduckgo.com https://duckduckgo.com; "
    "img-src 'self' data: https://*.tweekit.io https://tweekit.io;"
)

# --- FastAPI App Setup ---
# Main app for the root endpoints (/version, /doctype, /preflight, /convert, /convert-url, /documents/{doc_id})
app = FastAPI(
    title="TweekIT API Proxy",
    version="1.8.0",
    description="REST proxy exposing TweekIT MCP tools for OpenAI Apps SDK, ChatGPT Actions, and AI Hub integration.",
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if "Content-Security-Policy" not in response.headers:
        response.headers["Content-Security-Policy"] = DEFAULT_CSP
    return response


# A separate app for the manifest, which will be mounted under /mcp
mcp_manifest_app = FastAPI()


# --- Pydantic Models ---
class ConvertRequest(BaseModel):
    apiKey: Optional[str] = Field(None, description="API key for TweekIT authentication.")
    apiSecret: Optional[str] = Field(None, description="API secret for TweekIT authentication.")
    inext: str = Field(..., description="Input document extension (e.g. jpg, png, pdf).")
    outfmt: str = Field(..., description="Desired output format (e.g. png, pdf).")
    blob: str = Field(..., description="Base64 encoded document payload.")
    width: int = Field(0, description="Optional resize width in pixels.")
    height: int = Field(0, description="Optional resize height in pixels.")
    x1: int = Field(0, description="Left crop coordinate in source pixels.")
    y1: int = Field(0, description="Top crop coordinate in source pixels.")
    x2: int = Field(0, description="Right crop coordinate in source pixels.")
    y2: int = Field(0, description="Bottom crop coordinate in source pixels.")
    page: int = Field(1, description="Page number for multi-page inputs.")
    alpha: bool = Field(True, description="Preserve alpha transparency when producing raster formats.")
    noRasterize: bool = Field(False, description="Skip rasterization when supported.")
    bgcolor: str = Field("", description="Background color for transparent documents (hex RGB).")


class ConvertUrlRequest(BaseModel):
    apiKey: Optional[str] = Field(None, description="API key for TweekIT authentication.")
    apiSecret: Optional[str] = Field(None, description="API secret for TweekIT authentication.")
    url: str = Field(..., description="Direct download URL for the source document or image.")
    outfmt: str = Field(..., description="Desired output format (e.g. png, pdf).")
    inext: Optional[str] = Field(None, description="Optional override for the input extension.")
    width: int = Field(0, description="Optional resize width in pixels.")
    height: int = Field(0, description="Optional resize height in pixels.")
    x1: int = Field(0, description="Left crop coordinate in source pixels.")
    y1: int = Field(0, description="Top crop coordinate in source pixels.")
    x2: int = Field(0, description="Right crop coordinate in source pixels.")
    y2: int = Field(0, description="Bottom crop coordinate in source pixels.")
    page: int = Field(1, description="Page number for multi-page inputs.")
    alpha: bool = Field(True, description="Preserve alpha transparency when producing raster formats.")
    noRasterize: bool = Field(False, description="Skip rasterization when supported.")
    bgcolor: str = Field("", description="Background color for transparent documents (hex RGB).")
    fetchHeaders: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers when downloading the remote URL.")


# --- Helper Functions ---
async def _call_tweekit(endpoint: str, method: str = "GET", **kwargs):
    headers = kwargs.pop("headers", {})
    timeout = httpx.Timeout(20.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method, f"{BASE_URL}{endpoint}", headers=headers, **kwargs)
        response.raise_for_status()
        return response


def _extract_bearer(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return token[7:].strip() if token.lower().startswith("bearer ") else token.strip()


def _resolve_credentials(
    header_key: Optional[str],
    header_secret: Optional[str],
    authorization: Optional[str] = None,
    body_key: Optional[str] = None,
    body_secret: Optional[str] = None,
    *,
    allow_defaults: bool = True,
    required: bool = True,
) -> tuple[Optional[str], Optional[str]]:
    bearer = _extract_bearer(authorization)
    api_key = header_key or body_key or (bearer if bearer else None)
    api_secret = header_secret or body_secret
    if allow_defaults:
        api_key = api_key or DEFAULT_API_KEY
        api_secret = api_secret or DEFAULT_API_SECRET
    if required and (not api_key or not api_secret):
        raise HTTPException(status_code=401, detail="Missing TweekIT API credentials.")
    return api_key, api_secret


def _parse_bg_hex(bgcolor: str) -> int:
    if not bgcolor:
        return 0
    try:
        return int(bgcolor.lstrip("#"), 16)
    except ValueError:
        return 0


# --- Root API Endpoints ---
@app.get("/version", summary="Get the current TweekIT API version.")
async def get_version(
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(
        api_key,
        api_secret,
        authorization,
        allow_defaults=True,
        required=False,
    )
    if key and secret:
        headers = {"ApiKey": key, "ApiSecret": secret}
        response = await _call_tweekit("version", headers=headers)
        return {"version": response.text}
    return {"version": None, "detail": "Provide Authorization bearer token to fetch TweekIT upstream version."}


@app.get("/preflight", summary="Validate file format support and recommend AI-ready target format.")
async def get_preflight(
    filename_or_ext: str = Query(..., description="Filename, path, or extension to inspect (e.g. scan.psd, report.xls, dwg)."),
    target_provider: str = Query("default", description="Target AI provider ('claude', 'openai', 'gemini', 'mistral', 'grok', 'deepseek', 'openrouter', or 'default')."),
):
    return recommend_ai_format(filename_or_ext, target_provider=target_provider)


@app.get("/doctype", summary="List supported document types or resolve an extension.")
async def get_doctype(
    ext: Optional[str] = Query(None, description="File extension to inspect (e.g. pdf, png, or *)."),
    extension: Optional[str] = Query(None, description="Alias for ext (e.g. pdf, png, or *)."),
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    resolved_ext = ext or extension or "*"
    key, secret = _resolve_credentials(api_key, api_secret, authorization, allow_defaults=False)
    headers = {"ApiKey": key, "ApiSecret": secret}
    response = await _call_tweekit("doctype", headers=headers, params={"ext": resolved_ext})
    return response.json()


@app.post("/convert", summary="Convert an encoded document to the requested format.")
async def post_convert(
    payload: ConvertRequest,
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(
        api_key, api_secret, authorization, payload.apiKey, payload.apiSecret, allow_defaults=False
    )
    headers = {"ApiKey": key, "ApiSecret": secret}
    body = {
        "Fmt": payload.outfmt,
        "Width": payload.width,
        "Height": payload.height,
        "X1": payload.x1,
        "Y1": payload.y1,
        "X2": payload.x2,
        "Y2": payload.y2,
        "Bg": _parse_bg_hex(payload.bgcolor),
        "BgColor": payload.bgcolor,
        "Alpha": payload.alpha,
        "NoRasterize": payload.noRasterize,
        "Page": payload.page,
        "DocDataType": payload.inext,
        "DocData": payload.blob,
    }
    response = await _call_tweekit("", method="POST", headers=headers, json=body)
    content_type = response.headers.get("content-type", "").lower()
    if content_type.startswith("application/json"):
        return response.json()
    disp_filename = f"converted.{payload.outfmt.strip('.') or 'bin'}"
    return StreamingResponse(
        response.aiter_bytes(),
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{disp_filename}"'},
    )


@app.post("/convert-url", summary="Download a remote URL and convert it to the requested format.")
async def post_convert_url(
    payload: ConvertUrlRequest,
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(
        api_key, api_secret, authorization, payload.apiKey, payload.apiSecret, allow_defaults=False
    )
    if not payload.url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    fetch_headers = {str(k): str(v) for k, v in (payload.fetchHeaders or {}).items()} or None
    timeout = httpx.Timeout(20.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        dl_resp = await client.get(payload.url, headers=fetch_headers)
        dl_resp.raise_for_status()

    if not dl_resp.content:
        raise HTTPException(status_code=400, detail="Downloaded remote content was empty.")

    resolved_inext = _resolve_extension(payload.url, payload.inext, dl_resp.headers.get("content-type"))
    blob = base64.b64encode(dl_resp.content).decode("ascii")
    headers = {"ApiKey": key, "ApiSecret": secret}
    body = {
        "Fmt": payload.outfmt,
        "Width": payload.width,
        "Height": payload.height,
        "X1": payload.x1,
        "Y1": payload.y1,
        "X2": payload.x2,
        "Y2": payload.y2,
        "Bg": _parse_bg_hex(payload.bgcolor),
        "BgColor": payload.bgcolor,
        "Alpha": payload.alpha,
        "NoRasterize": payload.noRasterize,
        "Page": payload.page,
        "DocDataType": resolved_inext,
        "DocData": blob,
    }
    response = await _call_tweekit("", method="POST", headers=headers, json=body)
    content_type = response.headers.get("content-type", "").lower()
    if content_type.startswith("application/json"):
        return response.json()
    disp_filename = f"converted.{payload.outfmt.strip('.') or 'bin'}"
    return StreamingResponse(
        response.aiter_bytes(),
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{disp_filename}"'},
    )


@app.delete("/documents/{doc_id}", summary="Immediately delete an uploaded TweekIT document by DocId.")
async def delete_document_endpoint(
    doc_id: str,
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(api_key, api_secret, authorization, allow_defaults=False)
    headers = {"ApiKey": key, "ApiSecret": secret}
    response = await _call_tweekit(doc_id, method="DELETE", headers=headers)
    try:
        return response.json()
    except Exception:
        return {"message": "Document deleted successfully", "docId": doc_id}


# --- Manifest Endpoint (under /mcp) ---
@mcp_manifest_app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_manifest(request: Request):
    # The public URL for the API endpoints is the root of the service.
    # If PLUGIN_PUBLIC_BASE_URL is 'https://plugin.tweekit.io/mcp', we strip the '/mcp'.
    api_url = PUBLIC_API_BASE_URL.removesuffix("/mcp") or str(request.base_url).rstrip("/")

    manifest = {
        "schema_version": "v1",
        "name_for_human": "TweekIT Converter",
        "name_for_model": "tweekit",
        "description_for_human": "Convert and normalize 450+ file types for AI ingestion via TweekIT (AMPS dba Equilibrium).",
        "description_for_model": "Use TweekIT to run preflight format checks, inspect supported document types, and convert uploaded documents into AI-ready formats.",
        "auth": {
            "type": "service_http",
            "authorization_type": "bearer",
            "instructions": "Set the Authorization header to 'Bearer <token>' where the token is your TweekIT API key. Optionally supply X-Api-Secret for partner accounts or configure default credentials server-side.",
        },
        "api": {
            "type": "openapi",
            "url": f"{api_url}/openapi.json",
            "is_user_authenticated": True,
        },
        "logo_url": LOGO_URL or f"{api_url}/logo.png",
        "contact_email": "support@tweekit.io",
        "legal_info_url": "https://tweekit.io/privacy/",
    }
    return JSONResponse(manifest)


# Mount the manifest app at the /mcp prefix
app.mount("/mcp", mcp_manifest_app)
