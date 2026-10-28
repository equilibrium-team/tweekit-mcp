import argparse
import asyncio
import base64
import json
import logging
import mimetypes
import os
import re
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import httpx
from fastmcp import FastMCP
from fastmcp.utilities.types import File, Image
from mcp.types import ToolAnnotations
from typing import Any, Dict, FrozenSet, List, Optional, Set, Annotated
from pydantic import Field

BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
#BASE_URL = "http://localhost:16377/api/image/"

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.WARNING)

SERVER_VERSION = "1.8.0"

mcp = FastMCP("TweekIT")

# Comprehensive format taxonomy aligned with Maitrix AI Hub & TweekIT MediaRich engine.
FORMAT_TAXONOMY: Dict[str, FrozenSet[str]] = {
    "raster_image": frozenset({
        "jpg", "jpeg", "jpe", "png", "webp", "gif", "bmp", "tiff", "tif",
        "ico", "cur", "pcx", "tga", "pbm", "pgm", "ppm", "pnm", "sgi",
        "rgb", "bw", "ras", "sun", "xbm", "xpm", "wbmp", "heic", "heif",
        "avif", "jp2", "j2k", "jpx", "jxr", "wdp", "hdp", "exr", "hdr",
        "dds", "iff", "lbm", "pct", "pic", "pict", "mac", "fpx", "sct",
        "cut", "img", "rla", "rle", "sff", "dcx", "jb2", "jbig2",
    }),
    "design_vector_cad": frozenset({
        "psd", "psb", "ai", "eps", "ps", "svg", "svgz", "cdr", "cmx",
        "wmf", "emf", "cgm", "fig", "plt", "hpgl", "igs", "iges", "dwg",
        "dxf", "dwf", "dgn", "stl", "obj", "3ds", "dae", "u3d",
    }),
    "camera_raw": frozenset({
        "raw", "crw", "cr2", "cr3", "nef", "nrw", "arw", "srf", "sr2",
        "dng", "orf", "rw2", "pef", "ptx", "raf", "x3f", "erf", "mef",
        "mos", "mrw", "kdc", "dcr", "3fr", "fff", "iiq", "rwl", "srw",
        "bay", "bmq", "cine", "cs1", "ia", "kc2", "mdc", "pxn", "qtk",
        "rdc", "sti",
    }),
    "document": frozenset({
        "pdf", "doc", "docx", "docm", "dot", "dotx", "dotm", "rtf", "txt",
        "text", "md", "markdown", "odt", "ott", "fodt", "pages", "wpd",
        "wp", "wp5", "wp6", "wps", "wri", "abw", "zabw", "lwp", "sam",
        "sdw", "sxw", "vor", "hwp", "hwpx", "oxps", "xps", "djvu", "djv",
        "tex", "latex", "man", "troff", "nroff",
    }),
    "spreadsheet": frozenset({
        "xls", "xlsx", "xlsm", "xlsb", "xlt", "xltx", "xltm", "xlw",
        "csv", "tsv", "ods", "ots", "fods", "numbers", "dif", "slk",
        "sylk", "wk1", "wk3", "wk4", "wks", "123", "wb1", "wb2", "wb3",
        "wq1", "wq2", "sdc", "sxc", "gnm", "gnumeric", "pxl",
    }),
    "presentation": frozenset({
        "ppt", "pptx", "pptm", "pps", "ppsx", "ppsm", "pot", "potx",
        "potm", "odp", "otp", "fodp", "key", "keynote", "sdd", "sdp",
        "sxi", "shw",
    }),
    "diagram_publishing": frozenset({
        "vsd", "vsdx", "vsdm", "vss", "vssx", "vst", "vstx", "pub",
        "fm", "mif", "indd", "idml", "pmd", "qxp", "qxd", "sla", "scd",
    }),
    "ebook_help": frozenset({
        "epub", "mobi", "azw", "azw3", "fb2", "lit", "pdb", "prc",
        "lrf", "tcr", "chm", "hlp",
    }),
    "email_message": frozenset({
        "eml", "msg", "mbox", "vcf", "ics",
    }),
    "web_code_data": frozenset({
        "html", "htm", "xhtml", "mht", "mhtml", "xml", "xsl", "xslt",
        "json", "yaml", "yml", "toml", "ini", "cfg", "conf", "log",
        "sql", "py", "js", "ts", "jsx", "tsx", "java", "c", "cpp",
        "h", "hpp", "cs", "go", "rs", "rb", "php", "swift", "kt",
        "scala", "sh", "bash", "zsh", "ps1", "bat", "cmd", "css",
        "scss", "less", "r", "m", "pl", "lua",
    }),
    "archive": frozenset({
        "zip", "tar", "gz", "tgz", "bz2", "tbz2", "xz", "txz", "7z",
        "rar", "cab", "iso", "jar", "war", "ear", "cpio", "ar", "z",
        "lz", "lzma", "zst",
    }),
    "audio_video": frozenset({
        "mp4", "m4v", "mov", "avi", "wmv", "flv", "mkv", "webm", "mpeg",
        "mpg", "m2v", "3gp", "3g2", "ogv", "vob", "mts", "m2ts", "asf",
        "rm", "rmvb", "swf", "mp3", "wav", "flac", "aac", "m4a", "ogg",
        "oga", "opus", "wma", "aiff", "aif", "au", "snd", "mid", "midi",
        "amr",
    }),
}

EXTENSIVE_SUPPORTED_EXTENSIONS: FrozenSet[str] = frozenset().union(*FORMAT_TAXONOMY.values())

AI_PROVIDER_PROFILES: Dict[str, Dict[str, Any]] = {
    "claude": {
        "display_name": "Anthropic Claude",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "md", "csv", "html", "json", "xml"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "openai": {
        "display_name": "OpenAI (GPT-4o / GPT-4.1 / o-series)",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "gif", "webp", "pdf", "txt", "md", "csv", "json"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "gemini": {
        "display_name": "Google Gemini",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "webp", "heic", "heif", "pdf", "txt", "md", "csv", "html", "json", "xml", "mp3", "wav", "mp4", "webm"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "mistral": {
        "display_name": "Mistral AI",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "webp", "pdf", "txt", "md", "csv", "json"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "grok": {
        "display_name": "xAI Grok",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "webp", "pdf", "txt", "md", "csv", "json"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "txt", "md", "csv", "json"}),
        "image_target": "png",
        "document_target": "png",
        "fallback_target": "png",
    },
    "openrouter": {
        "display_name": "OpenRouter / Maitrix AI Hub",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "webp", "pdf", "txt", "md", "csv", "json"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
    "default": {
        "display_name": "Universal AI Ingestion Default",
        "native_extensions": frozenset({"png", "jpg", "jpeg", "pdf", "txt"}),
        "image_target": "png",
        "document_target": "pdf",
        "fallback_target": "pdf",
    },
}


def _extract_extension_from_input(filename_or_ext: str) -> str:
    """Extract and normalize a file extension from a filename, URL, path, or bare extension."""
    cleaned = (filename_or_ext or "").strip()
    if not cleaned:
        return ""
    if "://" in cleaned or "?" in cleaned or "#" in cleaned:
        parsed_path = urlparse(cleaned).path
        if parsed_path:
            cleaned = parsed_path
    if "." in cleaned and not cleaned.startswith("."):
        suffix = Path(cleaned).suffix
        if suffix:
            return suffix.lstrip(".").lower()
    return cleaned.lstrip(".").lower()


def recommend_ai_format(filename_or_ext: str, target_provider: str = "default") -> Dict[str, Any]:
    """Classify an input file/extension and recommend the optimal AI-ready output format."""
    raw_ext = _extract_extension_from_input(filename_or_ext)
    normalized_ext = _normalize_extension(raw_ext)
    provider_key = (target_provider or "default").strip().lower()
    profile = AI_PROVIDER_PROFILES.get(provider_key, AI_PROVIDER_PROFILES["default"])

    category = "unknown"
    for cat_name, ext_set in FORMAT_TAXONOMY.items():
        if raw_ext in ext_set or normalized_ext in ext_set:
            category = cat_name
            break

    is_supported = (raw_ext in EXTENSIVE_SUPPORTED_EXTENSIONS) or (normalized_ext in EXTENSIVE_SUPPORTED_EXTENSIONS)
    native_supported = (raw_ext in profile["native_extensions"]) or (normalized_ext in profile["native_extensions"])

    visual_categories = {"raster_image", "design_vector_cad", "camera_raw"}
    if category in visual_categories:
        recommended_outfmt = profile["image_target"]
    elif category in {"document", "spreadsheet", "presentation", "diagram_publishing", "ebook_help", "email_message", "web_code_data"}:
        recommended_outfmt = profile["document_target"]
    else:
        recommended_outfmt = profile["fallback_target"]

    return {
        "input": filename_or_ext,
        "extension": raw_ext,
        "normalized_extension": normalized_ext,
        "supported": is_supported,
        "category": category,
        "target_provider": provider_key if provider_key in AI_PROVIDER_PROFILES else "default",
        "provider_display_name": profile["display_name"],
        "native_ai_supported": native_supported,
        "needs_conversion": bool(is_supported and not native_supported),
        "recommended_outfmt": recommended_outfmt,
        "suggested_params": {
            "inext": normalized_ext or raw_ext or "bin",
            "outfmt": recommended_outfmt,
            "noRasterize": recommended_outfmt == "pdf",
            "alpha": recommended_outfmt in {"png", "webp"},
        },
    }


def preflight_check(filename_or_ext: str, target_provider: str = "default") -> Dict[str, Any]:
    """Alias for recommend_ai_format used for preflight validation in AI Hub workflows."""
    return recommend_ai_format(filename_or_ext, target_provider=target_provider)

# Remapping table so files with the alternate versions of known filename extensions aren't rejected.
# (Though I think MediaRich already supports these, so I don't know why this is here....)
_EXTENSION_ALIASES: Dict[str, str] = {
    "jpeg": "jpg",
    "jpe": "jpg",
    "tif": "tiff",
    "htm": "html",
}


def _normalize_extension(ext: str) -> str:
    normalized = ext.strip().lower().lstrip(".")
    if not normalized:
        return ""
    return _EXTENSION_ALIASES.get(normalized, normalized)


def _resolve_extension(url: str, override: Optional[str], content_type: Optional[str]) -> str:
    """Determine the best input extension for a downloaded file."""
    if override:
        candidate = _normalize_extension(override)
        if candidate:
            return candidate

    path_ext = _normalize_extension(Path(urlparse(url).path).suffix)
    if path_ext:
        return path_ext

    if content_type:
        mime = content_type.split(";", 1)[0].strip()
        guessed = mimetypes.guess_extension(mime) or ""
        normalized = _normalize_extension(guessed)
        if normalized:
            return normalized
        if "/" in mime:
            subtype = _normalize_extension(mime.split("/")[-1])
            if subtype:
                return subtype

    return "bin"


def _resolve_credentials(provided_key: Optional[str], provided_secret: Optional[str]) -> tuple[str, str]:
    api_key = (provided_key or os.getenv("TWEEKIT_API_KEY") or "").strip()
    api_secret = (provided_secret or os.getenv("TWEEKIT_API_SECRET") or "").strip()
    missing = []
    if not api_key:
        missing.append("TWEEKIT_API_KEY")
    if not api_secret:
        missing.append("TWEEKIT_API_SECRET")
    if missing:
        raise RuntimeError(f"Missing TweekIT credentials: {', '.join(missing)}")
    return api_key, api_secret


def _extract_error_details(response: Optional[httpx.Response]) -> str:
    if response is None:
        return ""
    hints = {
        k: v
        for k, v in (response.headers or {}).items()
        if k.lower().startswith("x-mediagen") or k.lower().startswith("x-tweekit")
    }

    try:
        data = response.json()
        if isinstance(data, dict):
            message = data.get("message") or data.get("error")
            if hints:
                data["debugHeaders"] = hints
            return message or json.dumps(data)
        if isinstance(data, list):
            return json.dumps(data)
    except Exception:
        pass
    text = response.text.strip() if response.text else ""
    if hints and not text:
        text = json.dumps(hints)
    return text

@mcp.resource("config://tweekit-version")
async def version() -> str:
    """Get current version of the TweekIT API."""
    url = f"{BASE_URL}version"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            body = (response.text or "").strip()
            return body or "unknown"
    except httpx.HTTPStatusError as e:
        logger.warning("TweekIT version probe failed: status=%s", getattr(e.response, "status_code", "unknown"))
        details = _extract_error_details(e.response)
        return f"unavailable (http {getattr(e.response, 'status_code', 'unknown')}{': ' + details if details else ''})"
    except httpx.RequestError as e:
        logger.error("Network error checking TweekIT version: %s", e)
        return f"unavailable (network error: {e})"
    except Exception as e:
        logger.exception("Unexpected error checking TweekIT version")
        return f"unavailable (unexpected error: {e})"


@mcp.resource("config://tweekit-mcp-version")
async def mcp_version() -> str:
    """Return the TweekIT MCP server version."""
    return SERVER_VERSION

@mcp.tool(
    annotations=ToolAnnotations(
        title="Inspect Supported Document Types",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def doctype(
    apiKey: Annotated[Optional[str], Field(description="TweekIT API key passed via the ApiKey header. Defaults to the TWEEKIT_API_KEY environment variable when omitted.")] = None,
    apiSecret: Annotated[Optional[str], Field(description="TweekIT API secret paired with the apiKey. Defaults to the TWEEKIT_API_SECRET environment variable when omitted.")] = None,
    extension: Annotated[str, Field(description="File extension to inspect; use '*' to list all supported inputs.")] = "*",
) -> Dict[str, Any]:
    """
    Retrieve a list of supported file formats or map a file extension to its document type.

    Args:
        apiKey (str): The API key for authentication. Falls back to TWEEKIT_API_KEY when omitted.
        apiSecret (str): The API secret for authentication. Falls back to TWEEKIT_API_SECRET when omitted.
        extension (str): The file extension to query (e.g., 'jpg', 'pdf') or leave off or use '*' to return all supported input formats.

    Returns:
        Dict[str, Any]: A dictionary containing the supported file formats or an error message.
    """
    try:
        key, secret = _resolve_credentials(apiKey, apiSecret)
    except RuntimeError as exc:
        return {"error": str(exc)}

    url = f"{BASE_URL}doctype"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers={"ApiKey": key, "ApiSecret": secret}, params={"extension": extension})
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            if isinstance(data, dict):
                return data
            else:
                return {"result": data}

        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error fetching supported file formats given '%s': %s", extension, e)
            return {"error": f"Failed to fetch user data. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error("Network error fetching supported file formats given '%s': %s", extension, e)
            return {"error": f"Network error: {e}"}
        except Exception as e:
            logger.exception("An unexpected error occurred in doctype: %s", e)
            return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool(
    annotations=ToolAnnotations(
        title="AI Hub Preflight & Format Recommendation",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def preflight(
    filename_or_ext: Annotated[str, Field(description="Input filename, path, or extension to validate (e.g., 'scan.psd', 'report.xls', 'dwg').")],
    target_provider: Annotated[str, Field(description="Target AI provider/hub profile ('claude', 'openai', 'gemini', 'mistral', 'grok', 'deepseek', 'openrouter', or 'default').")] = "default",
) -> Dict[str, Any]:
    """Validate whether a file format is supported by TweekIT and recommend the optimal AI-ready output format.

    Designed for AI Hub preflight checks (such as Maitrix AI Hub, Claude, OpenAI, and Gemini pipelines)
    to determine whether an incoming file needs TweekIT normalization and which output format (`pdf`, `png`,
    `webp`, `txt`) and parameters to use.
    """
    return recommend_ai_format(filename_or_ext, target_provider=target_provider)


async def _convert_impl(
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

            content_type = response.headers.get("content-type") or ""
            lowered_ct = content_type.lower()
            if lowered_ct.startswith("image/"):
                image_format = lowered_ct.split("/")[-1]
                return Image(data=response.content, format=image_format)
            if lowered_ct == "application/pdf":
                return File(data=response.content, format="pdf")
            if "json" in lowered_ct:
                try:
                    return response.json()
                except Exception:
                    pass
            if lowered_ct.startswith("application/") or lowered_ct == "application/octet-stream":
                ext = outfmt.lower().strip(".") or "bin"
                return File(data=response.content, format=ext)

            # Attempt to surface TweekIT error payloads even if content type is unexpected
            error_details = _extract_error_details(response)
            if error_details:
                return {"error": error_details}

            return {"error": f"Unsupported content type in response: '{content_type or 'unknown'}'"}

        except httpx.HTTPStatusError as e:
            message = _extract_error_details(e.response)
            status = getattr(e.response, "status_code", "unknown")
            error_payload: Dict[str, Any] = {
                "error": f"HTTP {status} from TweekIT",
            }
            if message:
                error_payload["details"] = message
            if e.request is not None and (e.request.headers.get("content-type") or "").startswith("application/json"):
                payload_bytes = None
                try:
                    payload_bytes = e.request.content  # type: ignore[attr-defined]
                except AttributeError:
                    try:
                        payload_bytes = e.request.read()
                    except Exception:
                        payload_bytes = None
                payload_json = None
                if payload_bytes:
                    try:
                        payload_json = json.loads(payload_bytes.decode("utf-8"))
                    except Exception:
                        payload_json = None
                if isinstance(payload_json, dict):
                    error_payload["tweekitPayload"] = {
                        "DocDataType": payload_json.get("DocDataType"),
                        "Fmt": payload_json.get("Fmt"),
                    }
            logger.warning("TweekIT convert error (%s): %s", status, message or str(e))
            return error_payload
        except httpx.RequestError as e:
            logger.error("Network error fetching document from %s: %s", url, e)
            return {"error": "Network error"}
        except Exception as e:
            logger.exception("An unexpected error occurred in _convert_impl: %s", e)
            return {"error": f"An unexpected error occurred: {e}"}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Convert Base64 Document",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def convert(
    inext: Annotated[str, Field(description="Input file extension (e.g., pdf, docx, png).")],
    outfmt: Annotated[str, Field(description="Requested output format to send as Fmt.")],
    blob: Annotated[str, Field(description="Base64 encoded document payload (DocData).")],
    apiKey: Annotated[Optional[str], Field(description="TweekIT API key passed via the ApiKey header. Defaults to the TWEEKIT_API_KEY environment variable when omitted.")] = None,
    apiSecret: Annotated[Optional[str], Field(description="TweekIT API secret paired with the apiKey. Defaults to the TWEEKIT_API_SECRET environment variable when omitted.")] = None,
    noRasterize: Annotated[bool, Field(description="Forward to TweekIT to disable rasterization when supported.")] = False,
    width: Annotated[int, Field(description="Optional pixel width for the converted output.")] = 0,
    height: Annotated[int, Field(description="Optional pixel height for the converted output.")] = 0,
    x1: Annotated[int, Field(description="Left crop coordinate in source pixels.")] = 0,
    y1: Annotated[int, Field(description="Top crop coordinate in source pixels.")] = 0,
    x2: Annotated[int, Field(description="Right crop coordinate in source pixels.")] = 0,
    y2: Annotated[int, Field(description="Bottom crop coordinate in source pixels.")] = 0,
    page: Annotated[int, Field(description="Page number to convert for multi-page inputs.")] = 1,
    alpha: Annotated[bool, Field(description="Preserve alpha transparency when producing raster formats.")] = True,
    bgColor: Annotated[str, Field(description="Background color (hex RGB) to composite behind transparent pixels.")] = "",
) -> Any:
    """Convert an uploaded document payload with TweekIT.

    The file must already be base64 encoded (see `blob`). The conversion can be
    resized and cropped by providing optional geometry parameters. For raster
    outputs, set `alpha`/`bgColor` to control transparency handling.

    Args:
        inext: Source file extension such as `pdf`, `docx`, or `png`.
        outfmt: Desired output format (`Fmt` in the API body).
        blob: Base64 encoded document payload (`DocData`).
        apiKey: TweekIT API key (`ApiKey` header). Falls back to `TWEEKIT_API_KEY` env var.
        apiSecret: TweekIT API secret (`ApiSecret` header). Falls back to `TWEEKIT_API_SECRET` env var.
        noRasterize: Forwarded to TweekIT to skip rasterization when possible.
        width: Optional pixel width to request in the output.
        height: Optional pixel height to request in the output.
        x1: Left crop coordinate in source pixels.
        y1: Top crop coordinate in source pixels.
        x2: Right crop coordinate in source pixels.
        y2: Bottom crop coordinate in source pixels.
        page: Page number to extract for multipage inputs.
        alpha: Whether the output should preserve alpha transparency.
        bgColor: Background color to composite behind transparent pixels.

    Returns:
        A FastMCP `Image` or `File` payload, or an error description.
    """
    try:
        key, secret = _resolve_credentials(apiKey, apiSecret)
    except RuntimeError as exc:
        return {"error": str(exc)}

    return await _convert_impl(
        apiKey=key,
        apiSecret=secret,
        inext=inext,
        outfmt=outfmt,
        blob=blob,
        noRasterize=noRasterize,
        width=width,
        height=height,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        page=page,
        alpha=alpha,
        bgColor=bgColor,
    )


async def _convert_url_impl(
    apiKey: str,
    apiSecret: str,
    url: str,
    outfmt: str,
    inext: Optional[str] = None,
    noRasterize: bool = False,
    width: int = 0,
    height: int = 0,
    x1: int = 0,
    y1: int = 0,
    x2: int = 0,
    y2: int = 0,
    page: int = 1,
    alpha: bool = True,
    bgColor: str = "",
    fetchHeaders: Optional[Dict[str, str]] = None,
) -> Any:
    """Download a remote document and convert it via TweekIT."""

    headers = None
    if fetchHeaders:
        headers = {str(k): str(v) for k, v in fetchHeaders.items()}

    timeout = httpx.Timeout(20.0, read=60.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        status = getattr(e.response, "status_code", "unknown")
        message = _extract_error_details(e.response)
        error_payload = {
            "error": f"Failed to download remote content. Status: {status}",
        }
        if message:
            error_payload["details"] = message
        logger.warning("HTTP error downloading '%s': status=%s details=%s", url, status, message)
        return error_payload
    except httpx.RequestError as e:
        logger.error("Network error downloading '%s': %s", url, e)
        return {"error": f"Network error downloading remote content: {e}"}
    except Exception as e:
        logger.exception("Unexpected error downloading '%s'", url)
        return {"error": f"Unexpected error downloading remote content: {e}"}

    if not response.content:
        return {"error": "Downloaded content was empty."}

    resolved_inext = _resolve_extension(url, inext, response.headers.get("content-type"))
    blob = base64.b64encode(response.content).decode("ascii")

    return await _convert_impl(
        apiKey=apiKey,
        apiSecret=apiSecret,
        inext=resolved_inext,
        outfmt=outfmt,
        blob=blob,
        noRasterize=noRasterize,
        width=width,
        height=height,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        page=page,
        alpha=alpha,
        bgColor=bgColor,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Convert Remote URL Document",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def convert_url(
    url: Annotated[str, Field(description="Direct download URL for the source document or image.")],
    outfmt: Annotated[str, Field(description="Requested output format to send as Fmt.")],
    apiKey: Annotated[Optional[str], Field(description="TweekIT API key passed via the ApiKey header. Defaults to the TWEEKIT_API_KEY environment variable when omitted.")] = None,
    apiSecret: Annotated[Optional[str], Field(description="TweekIT API secret paired with the apiKey. Defaults to the TWEEKIT_API_SECRET environment variable when omitted.")] = None,
    inext: Annotated[Optional[str], Field(description="Override for the detected input extension (e.g., pdf).")] = None,
    noRasterize: Annotated[bool, Field(description="Forward to TweekIT to disable rasterization when supported.")] = False,
    width: Annotated[int, Field(description="Optional pixel width for the converted output.")] = 0,
    height: Annotated[int, Field(description="Optional pixel height for the converted output.")] = 0,
    x1: Annotated[int, Field(description="Left crop coordinate in source pixels.")] = 0,
    y1: Annotated[int, Field(description="Top crop coordinate in source pixels.")] = 0,
    x2: Annotated[int, Field(description="Right crop coordinate in source pixels.")] = 0,
    y2: Annotated[int, Field(description="Bottom crop coordinate in source pixels.")] = 0,
    page: Annotated[int, Field(description="Page number to convert for multi-page inputs.")] = 1,
    alpha: Annotated[bool, Field(description="Preserve alpha transparency when producing raster formats.")] = True,
    bgColor: Annotated[str, Field(description="Background color (hex RGB) to composite behind transparent pixels.")] = "",
    fetchHeaders: Annotated[Optional[Dict[str, str]], Field(description="Optional HTTP headers to include when downloading the URL.")] = None,
) -> Any:
    """Download a remote file and convert it with TweekIT in one step.

    This helper first fetches `url`, infers the input extension when possible,
    and then forwards the bytes to `convert`. Supply `fetchHeaders` when the
    remote resource needs authentication or custom headers.

    Args:
        url: Direct download URL for the source document or image.
        outfmt: Desired output format (`Fmt`).
        apiKey: TweekIT API key (`ApiKey` header). Falls back to `TWEEKIT_API_KEY` env var.
        apiSecret: TweekIT API secret (`ApiSecret` header). Falls back to `TWEEKIT_API_SECRET` env var.
        inext: Optional override for the source extension if it cannot be
            detected from the URL or response headers.
        noRasterize: Forwarded to TweekIT to skip rasterization when possible.
        width: Optional pixel width to request in the output.
        height: Optional pixel height to request in the output.
        x1: Left crop coordinate in source pixels.
        y1: Top crop coordinate in source pixels.
        x2: Right crop coordinate in source pixels.
        y2: Bottom crop coordinate in source pixels.
        page: Page number to extract for multipage inputs.
        alpha: Whether the output should preserve alpha transparency.
        bgColor: Background color to composite behind transparent pixels.
        fetchHeaders: Optional mapping of HTTP headers to include when fetching.

    Returns:
        A FastMCP `Image` or `File` payload, or an error description.
    """
    try:
        key, secret = _resolve_credentials(apiKey, apiSecret)
    except RuntimeError as exc:
        return {"error": str(exc)}

    return await _convert_url_impl(
        apiKey=key,
        apiSecret=secret,
        url=url,
        outfmt=outfmt,
        inext=inext,
        noRasterize=noRasterize,
        width=width,
        height=height,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        page=page,
        alpha=alpha,
        bgColor=bgColor,
        fetchHeaders=fetchHeaders,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Convert Local File",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def convert_file(
    file_path: Annotated[str, Field(description="Local filesystem path to the input document or image.")],
    outfmt: Annotated[str, Field(description="Requested output format (e.g., pdf, png, webp, txt).")],
    output_path: Annotated[Optional[str], Field(description="Optional local filesystem path to write the converted output directly to disk.")] = None,
    apiKey: Annotated[Optional[str], Field(description="TweekIT API key passed via the ApiKey header. Defaults to TWEEKIT_API_KEY when omitted.")] = None,
    apiSecret: Annotated[Optional[str], Field(description="TweekIT API secret paired with the apiKey. Defaults to TWEEKIT_API_SECRET when omitted.")] = None,
    inext: Annotated[Optional[str], Field(description="Override for the input file extension (inferred from file_path when omitted).")] = None,
    noRasterize: Annotated[bool, Field(description="Forward to TweekIT to disable rasterization when supported.")] = False,
    width: Annotated[int, Field(description="Optional pixel width for the converted output.")] = 0,
    height: Annotated[int, Field(description="Optional pixel height for the converted output.")] = 0,
    x1: Annotated[int, Field(description="Left crop coordinate in source pixels.")] = 0,
    y1: Annotated[int, Field(description="Top crop coordinate in source pixels.")] = 0,
    x2: Annotated[int, Field(description="Right crop coordinate in source pixels.")] = 0,
    y2: Annotated[int, Field(description="Bottom crop coordinate in source pixels.")] = 0,
    page: Annotated[int, Field(description="Page number to convert for multi-page inputs.")] = 1,
    alpha: Annotated[bool, Field(description="Preserve alpha transparency when producing raster formats.")] = True,
    bgColor: Annotated[str, Field(description="Background color (hex RGB) to composite behind transparent pixels.")] = "",
) -> Any:
    """Convert a local file on disk with TweekIT without base64-encoding into the LLM prompt context.

    When `output_path` is provided and conversion returns binary media (`Image` or `File`),
    the converted bytes are written directly to `output_path` and a compact JSON receipt is returned.
    Otherwise, returns a FastMCP `Image` or `File` payload directly.
    """
    if os.getenv("TWEEKIT_ALLOW_LOCAL_FILES", "1").strip().lower() in {"0", "false", "no"}:
        return {"error": "Local filesystem conversion is disabled on this server (TWEEKIT_ALLOW_LOCAL_FILES=0)."}

    try:
        key, secret = _resolve_credentials(apiKey, apiSecret)
    except RuntimeError as exc:
        return {"error": str(exc)}

    src = Path(file_path).expanduser()
    if not src.exists() or not src.is_file():
        return {"error": f"Input file not found: '{file_path}'"}

    try:
        raw_bytes = src.read_bytes()
    except Exception as exc:
        return {"error": f"Failed to read input file '{file_path}': {exc}"}

    if not raw_bytes:
        return {"error": f"Input file '{file_path}' is empty."}

    resolved_inext = _normalize_extension(inext or src.suffix) or "bin"
    blob = base64.b64encode(raw_bytes).decode("ascii")

    result = await _convert_impl(
        apiKey=key,
        apiSecret=secret,
        inext=resolved_inext,
        outfmt=outfmt,
        blob=blob,
        noRasterize=noRasterize,
        width=width,
        height=height,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        page=page,
        alpha=alpha,
        bgColor=bgColor,
    )

    if output_path and isinstance(result, (Image, File)) and getattr(result, "data", None) is not None:
        dest = Path(output_path).expanduser()
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(result.data)  # type: ignore[arg-type]
            return {
                "status": "ok",
                "input_path": str(src.resolve()),
                "output_path": str(dest.resolve()),
                "input_extension": resolved_inext,
                "output_format": getattr(result, "format", outfmt),
                "size_bytes": len(result.data),  # type: ignore[arg-type]
            }
        except Exception as exc:
            return {"error": f"Failed to write output file '{output_path}': {exc}"}

    return result


@mcp.tool(
    annotations=ToolAnnotations(
        title="Delete Uploaded Document",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def delete_document(
    docId: Annotated[str, Field(description="The DocId returned from a prior upload to delete.")],
    apiKey: Annotated[Optional[str], Field(description="TweekIT API key passed via the ApiKey header. Defaults to the TWEEKIT_API_KEY environment variable when omitted.")] = None,
    apiSecret: Annotated[Optional[str], Field(description="TweekIT API secret paired with the apiKey. Defaults to the TWEEKIT_API_SECRET environment variable when omitted.")] = None,
) -> Dict[str, Any]:
    """Immediately delete a document and all associated files by DocId.

    Use this when an AI workflow needs to explicitly clean up an uploaded document
    before its 20-minute auto-expiry — for example, when a user cancels mid-workflow.
    This is only needed when using the REST API upload flow directly; the MCP
    convert tools handle their own cleanup automatically.

    Args:
        docId: The document ID returned from a prior REST API upload call.
        apiKey: TweekIT API key (`ApiKey` header). Falls back to `TWEEKIT_API_KEY` env var.
        apiSecret: TweekIT API secret (`ApiSecret` header). Falls back to `TWEEKIT_API_SECRET` env var.

    Returns:
        A dict confirming deletion, or an error description.
    """
    try:
        key, secret = _resolve_credentials(apiKey, apiSecret)
    except RuntimeError as exc:
        return {"error": str(exc)}

    url = f"{BASE_URL}{docId}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.delete(url, headers={"ApiKey": key, "ApiSecret": secret})
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return {"message": "Document deleted successfully", "docId": docId}
        except httpx.HTTPStatusError as e:
            details = _extract_error_details(e.response)
            return {"error": f"HTTP {e.response.status_code} deleting document", "details": details}
        except httpx.RequestError as e:
            return {"error": f"Network error: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Fetch & Normalize URL",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def fetch(
    url: Annotated[str, Field(description="HTTP or HTTPS URL to retrieve and normalize.")],
) -> Any:
    """Fetch a URL and return content.

    - Images return as FastMCP Image.
    - PDFs return as File(format="pdf").
    - Text/JSON return as a JSON payload with metadata and text.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return {"error": "Unsupported URL scheme. Use http or https."}

    headers = {
        "User-Agent": f"tweekit-mcp/{SERVER_VERSION} (+https://github.com/equilibrium-team/tweekit-mcp)"
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


@mcp.tool(
    annotations=ToolAnnotations(
        title="Web Search (DuckDuckGo)",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def search(
    query: Annotated[str, Field(description="Search keywords to send to DuckDuckGo.")],
    max_results: Annotated[int, Field(description="Maximum number of results to return (1-10).")]=5,
) -> Dict[str, Any]:
    """Simple web search using DuckDuckGo HTML endpoint.

    Returns a list of {title, url, snippet} objects. Best‑effort parsing.
    """
    max_results = max(1, min(int(max_results), 10))
    q = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={q}"
    headers = {
        "User-Agent": f"tweekit-mcp/{SERVER_VERSION} (+https://github.com/equilibrium-team/tweekit-mcp)",
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the TweekIT MCP server.")
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "stdio"],
        default=os.getenv("MCP_TRANSPORT", "streamable-http"),
        help="Transport to expose (default: streamable-http).",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host for streamable-http transport (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port for streamable-http transport (default: 8080).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.transport == "streamable-http":
        logger.info("🚀 TweekIT MCP server starting (HTTP) on %s:%s", args.host, args.port)
    else:
        logger.info("🚀 TweekIT MCP server starting (stdio)")

    rpc_kwargs = {}
    if args.transport == "streamable-http":
        rpc_kwargs.update({
            "host": args.host,
            "port": args.port,
            "stateless_http": True,
        })

    try:
        asyncio.run(
            mcp.run_async(
                transport=args.transport,
                show_banner=False,
                **rpc_kwargs,
            )
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error("An error occurred while running the server: %s", e)
        raise
    finally:
        logger.info("Server shutdown complete.")


if __name__ == "__main__":
    main()
