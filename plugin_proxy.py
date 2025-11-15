import os
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

DEFAULT_BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
BASE_URL = os.getenv("TWEEKIT_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"
DEFAULT_API_KEY = os.getenv("TWEEKIT_API_KEY")
DEFAULT_API_SECRET = os.getenv("TWEEKIT_API_SECRET")
PUBLIC_BASE_URL = os.getenv("PLUGIN_PUBLIC_BASE_URL")
LOGO_URL = os.getenv("PLUGIN_LOGO_URL")

app = FastAPI(
    title="TweekIT API Proxy",
    version="1.0.0",
    description="REST proxy exposing TweekIT MCP tools for ChatGPT plugin integration.",
)


class ConvertRequest(BaseModel):
    apiKey: Optional[str] = Field(None, description="API key for TweekIT authentication.")
    apiSecret: Optional[str] = Field(None, description="API secret for TweekIT authentication.")
    inext: str = Field(..., description="Input document extension (e.g. jpg, png, pdf).")
    outfmt: str = Field(..., description="Desired output format (e.g. png, pdf).")
    blob: str = Field(..., description="Base64 encoded document payload.")
    width: int = Field(0, description="Optional resize width in pixels.")
    height: int = Field(0, description="Optional resize height in pixels.")
    page: int = Field(1, description="Page number for multi-page inputs.")
    bgcolor: str = Field("", description="Background color for transparent documents (hex RGB).")


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
    if token.lower().startswith("bearer "):
        return token[7:].strip()
    return token.strip()


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
    api_key = header_key or body_key
    api_secret = header_secret or body_secret
    if bearer:
        api_key = bearer
    if allow_defaults:
        api_key = api_key or DEFAULT_API_KEY
        api_secret = api_secret or DEFAULT_API_SECRET
    else:
        if api_key and not api_secret and DEFAULT_API_SECRET:
            api_secret = DEFAULT_API_SECRET
        if api_secret and not api_key and DEFAULT_API_KEY:
            api_key = DEFAULT_API_KEY
    if required and (not api_key or not api_secret):
        raise HTTPException(status_code=401, detail="Missing TweekIT API credentials.")
    return api_key, api_secret


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
    return {
        "version": None,
        "detail": "Provide Authorization bearer token to fetch TweekIT upstream version.",
    }


@app.get("/doctype", summary="List supported document types or resolve an extension.")
async def get_doctype(
    ext: str = Query(..., description="File extension to inspect (e.g. pdf, png)."),
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(
        api_key,
        api_secret,
        authorization,
        allow_defaults=False,
    )
    headers = {"ApiKey": key, "ApiSecret": secret}
    response = await _call_tweekit("doctype", headers=headers, params={"ext": ext})
    return response.json()


@app.post("/convert", summary="Convert an encoded document to the requested format.")
async def post_convert(
    payload: ConvertRequest,
    api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    api_secret: Optional[str] = Header(None, alias="X-Api-Secret"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    key, secret = _resolve_credentials(
        api_key,
        api_secret,
        authorization,
        payload.apiKey,
        payload.apiSecret,
        allow_defaults=False,
    )
    headers = {"ApiKey": key, "ApiSecret": secret}
    body = {
        "Fmt": payload.outfmt,
        "Width": payload.width,
        "Height": payload.height,
        "BgColor": payload.bgcolor,
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


@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_manifest(request: Request):
    base_url = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    manifest = {
        "schema_version": "v1",
        "name_for_human": "TweekIT Converter",
        "name_for_model": "tweekit",
        "description_for_human": "Convert and normalize files for AI ingestion via TweekIT.",
        "description_for_model": (
            "Use TweekIT to inspect supported document types and convert uploaded documents into AI-ready formats."
        ),
        "auth": {
            "type": "service_http",
            "authorization_type": "bearer",
            "instructions": (
                "Set the Authorization header to 'Bearer <token>' where the token is your TweekIT API key. "
                "Optionally supply X-Api-Secret for partner accounts or configure default credentials server-side."
            ),
        },
        "api": {
            "type": "openapi",
            "url": f"{base_url}/openapi.json",
            "is_user_authenticated": True,
        },
        "logo_url": LOGO_URL or f"{base_url}/logo.png",
        "contact_email": "support@tweekit.com",
        "legal_info_url": "https://tweekit.com/legal",
    }
    return JSONResponse(manifest)
