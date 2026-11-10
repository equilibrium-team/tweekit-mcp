import argparse
import asyncio
import base64
import errno
import ipaddress
import json
import logging
import mimetypes
import os
import re
import socket
from pathlib import Path
from typing import Annotated, Any, Dict, FrozenSet, Iterable, List, Optional
from urllib.parse import quote, quote_plus, urljoin, urlparse

import httpcore
import httpx
import uvicorn
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers, get_http_request
from fastmcp.utilities.types import File, Image
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.middleware import Middleware

CLOUD_BASE_URL = "https://dapp.tweekit.io/tweekit/api/image/"
LOCAL_MINER_BASE_URL = "http://127.0.0.1:16377/api/image/"
LOCAL_MINER_KESTREL_URL = "http://127.0.0.1:5000/api/image/"
LOCAL_MINER_MEDIAGEN_URL = "http://127.0.0.1:8088/mgen/TweekIT.ms"
BASE_URL = os.getenv("TWEEKIT_API_BASE_URL", CLOUD_BASE_URL).rstrip("/") + "/"

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.WARNING)

SERVER_VERSION = "1.8.3"
_ACTIVE_TRANSPORT = "stdio"

DEFAULT_MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024  # 25 MiB remote download cap
DEFAULT_MAX_LOCAL_FILE_BYTES = 50 * 1024 * 1024  # 50 MiB local input cap
DEFAULT_MAX_BLOB_CHARS = 70 * 1024 * 1024  # ~50 MiB base64 payload cap
MAX_REDIRECT_HOPS = 5

_DOC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_FORMAT_TOKEN_RE = re.compile(r"^[A-Za-z0-9]{1,16}$")

_LOOPBACK_MINER_HOSTS: FrozenSet[str] = frozenset({"127.0.0.1", "::1", "localhost"})

_BLOCKED_HOSTNAMES: FrozenSet[str] = frozenset({
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata",
    "metadata.google.internal",
    "instance-data",
})
_BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
_NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")
_NAT64_LOCAL = ipaddress.ip_network("64:ff9b:1::/48")

_SAFE_FETCH_HEADERS: FrozenSet[str] = frozenset({
    "accept",
    "accept-language",
    "cache-control",
    "if-modified-since",
    "if-none-match",
    "range",
    "user-agent",
})

_SENSITIVE_PATH_SEGMENTS: FrozenSet[str] = frozenset({
    ".ssh",
    ".aws",
    ".gnupg",
    ".kube",
    ".docker",
    ".git",
    ".hg",
    ".svn",
    ".config",
    ".vscode",
    ".idea",
    ".github",
    ".claude",
    ".cursor",
    ".gemini",
    "etc",
})
_SENSITIVE_FILENAMES: FrozenSet[str] = frozenset({
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".bashrc",
    ".bash_profile",
    ".zshrc",
    ".zprofile",
    ".profile",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "authorized_keys",
    "known_hosts",
    "credentials",
})
_SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".kdbx", ".jks")
_BLOCKED_OUTPUT_EXTENSIONS: FrozenSet[str] = frozenset({
    "sh", "bash", "zsh", "ps1", "bat", "cmd", "com", "exe", "msi", "dll",
    "so", "dylib", "py", "pyc", "pyo", "js", "mjs", "cjs", "ts", "jsx",
    "tsx", "php", "rb", "pl", "lua", "jar", "war", "ear", "app", "scr",
})

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


class _NormalizeMcpPathMiddleware:
    """Normalize trailing-slash `/mcp/` requests in-place and honor `X-Forwarded-Proto`."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") == "http":
            mutated: Optional[Dict[str, Any]] = None
            path = scope.get("path", "")
            if path == "/mcp/":
                mutated = dict(scope)
                mutated["path"] = "/mcp"
                mutated["raw_path"] = b"/mcp"
            for raw_k, raw_v in scope.get("headers") or ():
                if raw_k.lower() == b"x-forwarded-proto":
                    proto = raw_v.decode("latin-1", errors="ignore").split(",", 1)[0].strip().lower()
                    if proto in {"https", "http"} and proto != (mutated or scope).get("scheme"):
                        if mutated is None:
                            mutated = dict(scope)
                        mutated["scheme"] = proto
                    break
            if mutated is not None:
                scope = mutated
        await self.app(scope, receive, send)


class _PinnedPublicDNSBackend(httpcore.AsyncNetworkBackend):
    """Connect exclusively to pre-validated public IP addresses to eliminate DNS-rebinding TOCTOU."""

    def __init__(self, inner: httpcore.AsyncNetworkBackend) -> None:
        self._inner = inner
        self._pinned: Dict[tuple[str, int], List[str]] = {}
        self.connected_targets: List[tuple[str, int]] = []

    def register(self, hostname: str, port: int, validated_ips: List[str]) -> None:
        clean_ips = [ip for ip in validated_ips if _is_public_ip(ip)]
        if not clean_ips:
            raise ValueError(f"No public IP addresses available to pin for '{hostname}'.")
        self._pinned[(hostname.lower().rstrip("."), port)] = clean_ips

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Optional[Iterable[Any]] = None,
    ) -> httpcore.AsyncNetworkStream:
        normalized_host = host.strip("[]").lower().rstrip(".")
        candidates = self._pinned.get((normalized_host, port))
        if not candidates:
            if _is_public_ip(normalized_host):
                candidates = [normalized_host]
            else:
                raise httpcore.ConnectError(f"Refusing unpinned outbound TCP connection to '{host}:{port}'.")

        last_err: Optional[Exception] = None
        for ip_addr in candidates:
            if not _is_public_ip(ip_addr):
                raise httpcore.ConnectError(f"Blocked non-public pinned IP '{ip_addr}'.")
            try:
                stream = await self._inner.connect_tcp(
                    ip_addr,
                    port,
                    timeout=timeout,
                    local_address=local_address,
                    socket_options=socket_options,
                )
                peer = stream.get_extra_info("server_addr")
                if isinstance(peer, tuple) and peer and isinstance(peer[0], str):
                    peer_ip = peer[0].split("%", 1)[0]
                    if not _is_public_ip(peer_ip):
                        await stream.aclose()
                        raise httpcore.ConnectError(f"Connected peer '{peer_ip}' is not a public IP address.")
                self.connected_targets.append((ip_addr, port))
                return stream
            except Exception as exc:
                last_err = exc

        if last_err is not None:
            raise last_err
        raise httpcore.ConnectError(f"Unable to connect to any validated IP for '{host}:{port}'.")

    async def connect_unix_socket(
        self,
        path: str,
        timeout: Optional[float] = None,
        socket_options: Optional[Iterable[Any]] = None,
    ) -> httpcore.AsyncNetworkStream:
        raise httpcore.ConnectError("Unix domain socket connections are disabled for remote URL fetching.")

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


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


def _validate_format_token(value: str, field_name: str = "format") -> str:
    cleaned = _normalize_extension(value)
    if not cleaned or not _FORMAT_TOKEN_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid {field_name}: must be 1-16 alphanumeric characters.")
    return cleaned


def _validate_doc_id(doc_id: str) -> str:
    cleaned = (doc_id or "").strip()
    if not cleaned or not _DOC_ID_RE.fullmatch(cleaned):
        raise ValueError("Invalid docId: must be 1-128 characters matching [A-Za-z0-9_-].")
    return cleaned


def _resolve_extension(url: str, override: Optional[str], content_type: Optional[str]) -> str:
    """Determine the best input extension for a downloaded file."""
    if override:
        candidate = _normalize_extension(override)
        if candidate and _FORMAT_TOKEN_RE.fullmatch(candidate):
            return candidate

    path_ext = _normalize_extension(Path(urlparse(url).path).suffix)
    if path_ext and _FORMAT_TOKEN_RE.fullmatch(path_ext):
        return path_ext

    if content_type:
        mime = content_type.split(";", 1)[0].strip()
        guessed = mimetypes.guess_extension(mime) or ""
        normalized = _normalize_extension(guessed)
        if normalized and _FORMAT_TOKEN_RE.fullmatch(normalized):
            return normalized
        if "/" in mime:
            subtype = _normalize_extension(mime.split("/")[-1])
            if subtype and _FORMAT_TOKEN_RE.fullmatch(subtype):
                return subtype

    return "bin"


def _extract_bearer(auth_header: Optional[str]) -> str:
    if not auth_header:
        return ""
    value = auth_header.strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return ""


def _is_truthy_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes"}


def _is_local_only_mode(*, base_url: Optional[str] = None) -> bool:
    """Return True when zero-egress local Miner Renderery mode is active.

    Zero-egress mode is active when `TWEEKIT_LOCAL_ONLY=1` is set, or automatically by default
    whenever `TWEEKIT_MINER_LOCAL=1` or an explicit local/on-prem Miner Renderery `base_url`
    (such as `TweekitDirectClient(local_miner=True)`) is active, unless `TWEEKIT_LOCAL_ONLY=0`
    is explicitly configured.
    """
    raw_local_only = os.getenv("TWEEKIT_LOCAL_ONLY")
    if raw_local_only is not None and raw_local_only.strip() != "":
        return raw_local_only.strip().lower() in {"1", "true", "yes"}
    if _is_truthy_env("TWEEKIT_MINER_LOCAL", "0"):
        return True
    if base_url and _is_local_or_onprem_api_url(base_url):
        return True
    return False


def _is_local_miner_enabled() -> bool:
    """Return True when TWEEKIT_MINER_LOCAL=1 or TWEEKIT_LOCAL_ONLY=1 routes to local Miner Renderery."""
    return _is_truthy_env("TWEEKIT_MINER_LOCAL", "0") or _is_truthy_env("TWEEKIT_LOCAL_ONLY", "0")


def _is_miner_noauth_enabled() -> bool:
    """Return True when TWEEKIT_MINER_NOAUTH=1 permits local NOAUTH;NODB Miner Renderery calls without cloud keys."""
    return _is_truthy_env("TWEEKIT_MINER_NOAUTH", "0")


def _get_allowed_onprem_hosts() -> FrozenSet[str]:
    """Return loopback hosts plus any operator-configured TWEEKIT_ONPREM_HOSTS for on-premises Miner Renderery nodes."""
    extra = {
        h.strip().lower().strip("[]").rstrip(".")
        for h in os.getenv("TWEEKIT_ONPREM_HOSTS", "").split(",")
        if h.strip() and h.strip().lower().strip("[]") not in {"0.0.0.0", "::"}
    }
    return _LOOPBACK_MINER_HOSTS | frozenset(extra)


def _is_local_or_onprem_api_url(url: str) -> bool:
    """Return True if `url` targets a loopback or allowlisted on-premises Miner Renderery host."""
    parsed = urlparse((url or "").strip())
    hostname = (parsed.hostname or "").strip().lower().strip("[]").rstrip(".")
    if not hostname or hostname in {"0.0.0.0", "::"}:
        return False
    if hostname in _get_allowed_onprem_hosts():
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _resolve_api_base_url(override_base_url: Optional[str] = None) -> str:
    """Resolve and validate the TweekIT API or On-Premises Miner Renderery base URL."""
    env_override = os.getenv("TWEEKIT_API_BASE_URL", "").strip()
    if override_base_url and override_base_url.strip():
        raw_url = override_base_url.strip()
    elif env_override:
        raw_url = env_override
    elif _is_local_miner_enabled() and BASE_URL.rstrip("/") == CLOUD_BASE_URL.rstrip("/"):
        raw_url = LOCAL_MINER_BASE_URL
    else:
        raw_url = BASE_URL

    normalized = raw_url.rstrip("/") + "/"
    parsed = urlparse(normalized)
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"https", "http"}:
        raise ValueError("Invalid TWEEKIT_API_BASE_URL scheme: must be 'https://' or local/on-prem 'http://'.")
    if parsed.username or parsed.password:
        raise ValueError("TWEEKIT_API_BASE_URL must not contain embedded userinfo credentials.")
    hostname = (parsed.hostname or "").strip()
    if not hostname:
        raise ValueError("TWEEKIT_API_BASE_URL is missing a valid hostname.")
    if hostname.lower().strip("[]") in {"0.0.0.0", "::"}:
        raise ValueError(
            f"Wildcard listener address '{hostname}' is not a valid client target and must not be used for "
            "unauthenticated NOAUTH Miner Renderery endpoints; bind and connect via loopback (127.0.0.1 / ::1)."
        )

    is_onprem = _is_local_or_onprem_api_url(normalized)
    if scheme == "http" and not is_onprem:
        raise ValueError(
            f"Plain HTTP TWEEKIT_API_BASE_URL ('{hostname}') is only permitted for localhost "
            "(127.0.0.1 / ::1 / localhost) or hosts explicitly listed in TWEEKIT_ONPREM_HOSTS."
        )
    if _is_local_only_mode() and not is_onprem:
        raise ValueError(
            f"TWEEKIT_LOCAL_ONLY=1 / TWEEKIT_MINER_LOCAL=1 requires a localhost or TWEEKIT_ONPREM_HOSTS Miner Renderery endpoint "
            f"(got external host '{hostname}'); third-party cloud egress is disabled."
        )
    return normalized


def _assert_outbound_internet_allowed(
    tool_name: str,
    *,
    base_url: Optional[str] = None,
    allow_remote_fetch_override: bool = False,
) -> None:
    """Block outbound internet tools (`convert_url`, `fetch`, `search`) in zero-egress local Miner Renderery mode."""
    if allow_remote_fetch_override or _is_truthy_env("TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY", "0"):
        return
    if _is_local_only_mode(base_url=base_url):
        raise ValueError(
            f"Tool '{tool_name}' is disabled in zero-egress local Miner Renderery mode "
            "(TWEEKIT_LOCAL_ONLY=1 / TWEEKIT_MINER_LOCAL=1 / local_miner=True). "
            "Set TWEEKIT_ALLOW_REMOTE_FETCH_IN_LOCAL_ONLY=1 to permit outbound HTTPS requests."
        )


def _resolve_credentials(
    provided_key: Optional[str] = None,
    provided_secret: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
) -> tuple[str, str]:
    """Resolve TweekIT API credentials from SDK args, atomic HTTP header pairs, stdio env vars, or local NOAUTH Miner."""
    is_http = _ACTIVE_TRANSPORT == "streamable-http" or _has_active_http_request()
    if provided_key is not None or provided_secret is not None:
        api_key = (provided_key or os.getenv("TWEEKIT_API_KEY") or "").strip()
        api_secret = (provided_secret or os.getenv("TWEEKIT_API_SECRET") or "").strip()
    else:
        req_headers = get_http_headers(
            include={"apikey", "apisecret", "x-api-key", "x-api-secret", "authorization"}
        )
        header_key = (
            req_headers.get("apikey")
            or req_headers.get("x-api-key")
            or _extract_bearer(req_headers.get("authorization"))
            or ""
        ).strip()
        header_secret = (
            req_headers.get("apisecret")
            or req_headers.get("x-api-secret")
            or ""
        ).strip()
        if header_key or header_secret:
            if not (header_key and header_secret):
                raise RuntimeError(
                    "Incomplete TweekIT HTTP header credentials: supply both ApiKey and ApiSecret headers."
                )
            return header_key, header_secret

        allow_http_env = _is_truthy_env("TWEEKIT_ALLOW_ENV_CREDENTIALS_OVER_HTTP", "0")
        if is_http and not allow_http_env:
            raise RuntimeError(
                "Missing TweekIT HTTP header credentials: supply both ApiKey and ApiSecret headers."
            )

        api_key = (os.getenv("TWEEKIT_API_KEY") or "").strip()
        api_secret = (os.getenv("TWEEKIT_API_SECRET") or "").strip()

    if not api_key and not api_secret and _is_miner_noauth_enabled() and not is_http:
        resolved_base = _resolve_api_base_url(base_url)
        if _is_local_or_onprem_api_url(resolved_base):
            return "local-miner", "local-miner"

    missing = []
    if not api_key:
        missing.append("TWEEKIT_API_KEY")
    if not api_secret:
        missing.append("TWEEKIT_API_SECRET")
    if missing:
        raise RuntimeError(
            f"Missing TweekIT credentials ({', '.join(missing)}). "
            "Configure TWEEKIT_API_KEY/TWEEKIT_API_SECRET in environment variables or HTTP ApiKey/ApiSecret headers "
            "(or set TWEEKIT_MINER_NOAUTH=1 when targeting a local NOAUTH Miner Renderery)."
        )
    return api_key, api_secret


def _is_public_ip(raw_ip: str) -> bool:
    """Return True only when `raw_ip` is a globally routable unicast IP address (including embedded v4 checks)."""
    try:
        ip = ipaddress.ip_address(raw_ip)
    except ValueError:
        return False

    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            return _is_public_ip(str(ip.ipv4_mapped))
        if ip.sixtofour is not None:
            return _is_public_ip(str(ip.sixtofour))
        if ip.teredo is not None:
            server_v4, client_v4 = ip.teredo
            return _is_public_ip(str(server_v4)) and _is_public_ip(str(client_v4))
        if ip in _NAT64_WELL_KNOWN or ip in _NAT64_LOCAL:
            embedded_v4 = ipaddress.IPv4Address(ip.packed[-4:])
            return _is_public_ip(str(embedded_v4))

    if (
        not ip.is_global
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    if isinstance(ip, ipaddress.IPv4Address) and ip in _CGNAT_NETWORK:
        return False

    return True


async def _resolve_host_ips(hostname: str, port: int) -> List[str]:
    """Resolve all A/AAAA socket addresses for `hostname` asynchronously."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    ips: List[str] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr and isinstance(sockaddr[0], str):
            addr = sockaddr[0].split("%", 1)[0]
            if addr not in ips:
                ips.append(addr)
    return ips


async def _validate_public_https_url(url: str) -> tuple[str, str, int, List[str]]:
    """Validate that `url` uses HTTPS and resolves exclusively to public IPs, returning pinned IPs."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("Unsupported URL scheme: only 'https://' URLs are permitted.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded userinfo credentials are not permitted.")
    hostname = (parsed.hostname or "").strip().rstrip(".").lower()
    if not hostname:
        raise ValueError("URL is missing a valid hostname.")
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(_BLOCKED_HOST_SUFFIXES):
        raise ValueError(f"Blocked internal or local hostname: '{hostname}'.")

    try:
        port = parsed.port or 443
    except ValueError as exc:
        raise ValueError("URL contains an invalid port.") from exc

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        ip_str = str(literal_ip)
        if not _is_public_ip(ip_str):
            raise ValueError(f"Blocked non-public IP address: '{hostname}'.")
        return url.strip(), hostname, port, [ip_str]

    try:
        resolved_ips = await _resolve_host_ips(hostname, port)
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve hostname '{hostname}': {exc}") from exc

    if not resolved_ips:
        raise ValueError(f"Hostname '{hostname}' did not resolve to any IP addresses.")
    for ip_str in resolved_ips:
        if not _is_public_ip(ip_str):
            raise ValueError(f"Hostname '{hostname}' resolves to a blocked non-public IP address.")

    return url.strip(), hostname, port, resolved_ips


def _sanitize_fetch_headers(
    fetch_headers: Optional[Dict[str, str]],
    *,
    hostname: str,
    allow_auth_headers: bool = False,
) -> Dict[str, str]:
    """Validate optional outbound fetch headers against a strict allowlist."""
    sanitized: Dict[str, str] = {
        "User-Agent": f"tweekit-mcp/{SERVER_VERSION} (+https://github.com/equilibrium-team/tweekit-mcp)"
    }
    if not fetch_headers:
        return sanitized
    if len(fetch_headers) > 16:
        raise ValueError("Too many fetchHeaders supplied (maximum 16).")

    allowed_auth_hosts = {
        h.strip().lower()
        for h in os.getenv("TWEEKIT_ALLOWED_AUTH_HOSTS", "").split(",")
        if h.strip()
    }

    for raw_k, raw_v in fetch_headers.items():
        key = str(raw_k).strip()
        val = str(raw_v).strip()
        if not key or "\r" in key or "\n" in key or "\r" in val or "\n" in val:
            raise ValueError("Invalid control characters in fetchHeaders.")
        if len(val) > 2048:
            raise ValueError(f"Header '{key}' exceeds maximum length.")
        lower_k = key.lower()
        if lower_k == "authorization":
            if not (allow_auth_headers or hostname in allowed_auth_hosts):
                raise ValueError(
                    "Forwarding 'Authorization' in fetchHeaders is disabled by default to prevent credential "
                    "exfiltration. Add the target domain to TWEEKIT_ALLOWED_AUTH_HOSTS if required."
                )
            sanitized["Authorization"] = val
        elif lower_k == "user-agent":
            sanitized["User-Agent"] = val
        elif lower_k in _SAFE_FETCH_HEADERS:
            sanitized[key] = val
        else:
            raise ValueError(
                f"Disallowed fetchHeader '{key}'. Allowed headers: {', '.join(sorted(_SAFE_FETCH_HEADERS))}."
            )
    return sanitized


async def _safe_fetch_remote(
    url: str,
    *,
    fetch_headers: Optional[Dict[str, str]] = None,
    allow_auth_headers: bool = False,
    max_bytes: Optional[int] = None,
) -> tuple[bytes, str, int, str]:
    """Fetch a remote HTTPS resource with connect-time IP pinning on every hop and a streaming size cap."""
    byte_limit = max_bytes or int(os.getenv("TWEEKIT_MAX_DOWNLOAD_BYTES", str(DEFAULT_MAX_DOWNLOAD_BYTES)))
    current_url, initial_host, initial_port, initial_ips = await _validate_public_https_url(url)
    req_headers = _sanitize_fetch_headers(
        fetch_headers,
        hostname=initial_host,
        allow_auth_headers=allow_auth_headers,
    )
    initial_origin = ("https", initial_host, initial_port)

    timeout = httpx.Timeout(20.0, read=60.0)
    transport = httpx.AsyncHTTPTransport(trust_env=False)
    pool = getattr(transport, "_pool", None)
    inner_backend = getattr(pool, "_network_backend", None)
    if pool is None or inner_backend is None:
        raise RuntimeError("Incompatible httpx/httpcore transport layout: unable to install DNS IP pinning.")
    pinned_backend = _PinnedPublicDNSBackend(inner_backend)
    pool._network_backend = pinned_backend
    pinned_backend.register(initial_host, initial_port, initial_ips)

    async with httpx.AsyncClient(transport=transport, timeout=timeout, follow_redirects=False) as client:
        for hop in range(MAX_REDIRECT_HOPS + 1):
            if hop > 0:
                current_url, hop_host, hop_port, hop_ips = await _validate_public_https_url(current_url)
                pinned_backend.register(hop_host, hop_port, hop_ips)
                hop_origin = ("https", hop_host, hop_port)
                if hop_origin != initial_origin:
                    req_headers.pop("Authorization", None)

            async with client.stream("GET", current_url, headers=req_headers) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    if hop >= MAX_REDIRECT_HOPS:
                        raise ValueError(f"Exceeded maximum redirect limit ({MAX_REDIRECT_HOPS}).")
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirect response missing Location header.")
                    current_url = urljoin(current_url, location)
                    continue

                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > byte_limit:
                            raise ValueError(f"Remote resource exceeds maximum allowed size ({byte_limit} bytes).")
                    except ValueError as exc:
                        if "exceeds maximum" in str(exc):
                            raise

                buf = bytearray()
                async for chunk in response.aiter_bytes():
                    buf.extend(chunk)
                    if len(buf) > byte_limit:
                        raise ValueError(f"Remote resource exceeds maximum allowed size ({byte_limit} bytes).")

                content_type = response.headers.get("content-type") or ""
                return bytes(buf), content_type, response.status_code, current_url

    raise ValueError(f"Exceeded maximum redirect limit ({MAX_REDIRECT_HOPS}).")


def _has_active_http_request() -> bool:
    try:
        get_http_request()
        return True
    except RuntimeError:
        return False


def _is_local_files_enabled() -> bool:
    """Local file access is opt-in only (`TWEEKIT_ALLOW_LOCAL_FILES=1`) and always disabled over HTTP."""
    if _ACTIVE_TRANSPORT == "streamable-http" or _has_active_http_request():
        return False
    return os.getenv("TWEEKIT_ALLOW_LOCAL_FILES", "0").strip().lower() in {"1", "true", "yes"}


def _get_allowed_local_dirs() -> List[Path]:
    """Return explicitly configured canonical workspace directories permitted for local reads/writes."""
    raw = os.getenv("TWEEKIT_ALLOWED_DIRS", "").strip()
    if not raw:
        raise ValueError(
            "TWEEKIT_ALLOWED_DIRS must be explicitly set to one or more workspace directories "
            "when TWEEKIT_ALLOW_LOCAL_FILES=1."
        )
    candidates = [p.strip() for p in raw.split(os.pathsep) if p.strip()]
    allowed: List[Path] = []
    for entry in candidates:
        resolved = Path(entry).expanduser().resolve()
        if resolved == Path(resolved.anchor):
            raise ValueError("TWEEKIT_ALLOWED_DIRS may not contain the filesystem root directory.")
        if resolved.is_dir():
            allowed.append(resolved)
    if not allowed:
        raise ValueError("No valid existing workspace directory found in TWEEKIT_ALLOWED_DIRS.")
    return allowed


def _is_sensitive_relative_path(target: Path, allowed_root: Path) -> bool:
    """Return True if `target` (relative to `allowed_root`) touches sensitive dotfiles or credentials."""
    lower_name = target.name.lower()
    if lower_name in _SENSITIVE_FILENAMES or lower_name.startswith(".env."):
        return True
    if lower_name.endswith(_SENSITIVE_SUFFIXES):
        return True
    rel = target.relative_to(allowed_root)
    for part in rel.parts:
        if part.lower() in _SENSITIVE_PATH_SEGMENTS:
            return True
    return False


def _assert_no_symlinks_under_root(raw_path: Path, allowed_dirs: List[Path]) -> None:
    """Reject any symlink on the leaf or intermediate components inside the workspace."""
    if raw_path.is_symlink():
        raise ValueError("Symbolic links are not permitted in local file paths.")
    cursor = raw_path.parent
    stop_roots = set(allowed_dirs)
    while cursor != cursor.parent and cursor not in stop_roots:
        if cursor.is_symlink():
            raise ValueError("Symbolic links are not permitted in local directory paths.")
        cursor = cursor.parent


def _match_allowed_root(resolved: Path, allowed_dirs: List[Path]) -> Optional[Path]:
    for root in allowed_dirs:
        if resolved.is_relative_to(root):
            return root
    return None


def _validate_local_read_path(file_path: str, allowed_dirs: List[Path]) -> Path:
    raw = Path(file_path).expanduser()
    _assert_no_symlinks_under_root(raw, allowed_dirs)
    try:
        resolved = raw.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: '{file_path}'") from exc

    if not resolved.is_file():
        raise ValueError(f"Input path is not a regular file: '{file_path}'")
    matched_root = _match_allowed_root(resolved, allowed_dirs)
    if matched_root is None:
        raise ValueError(
            "Input file_path is outside the allowed workspace directory. "
            "Configure TWEEKIT_ALLOWED_DIRS to permit this directory."
        )
    if _is_sensitive_relative_path(resolved, matched_root):
        raise ValueError("Reading sensitive credential, configuration, or dotfile paths is prohibited.")

    max_bytes = int(os.getenv("TWEEKIT_MAX_LOCAL_FILE_BYTES", str(DEFAULT_MAX_LOCAL_FILE_BYTES)))
    size = resolved.stat().st_size
    if size > max_bytes:
        raise ValueError(f"Input file exceeds maximum allowed size ({max_bytes} bytes).")
    return resolved


def _validate_local_write_path(output_path: str, allowed_dirs: List[Path]) -> Path:
    raw = Path(output_path).expanduser()
    # Always inspect lstat via is_symlink() unconditionally so dangling symlinks are rejected.
    _assert_no_symlinks_under_root(raw, allowed_dirs)

    probe = raw.parent
    missing_parts: List[str] = []
    while not probe.exists():
        if probe.is_symlink():
            raise ValueError("Symbolic links are not permitted in output_path parent directories.")
        if probe == probe.parent:
            break
        missing_parts.append(probe.name)
        probe = probe.parent
    if probe.is_symlink():
        raise ValueError("Symbolic links are not permitted in output_path parent directories.")

    resolved_parent = probe.resolve(strict=True)
    for part in reversed(missing_parts):
        resolved_parent = resolved_parent / part
    resolved_dest = resolved_parent / raw.name

    if resolved_dest.is_symlink():
        raise ValueError("Symbolic links are not permitted for output_path.")

    matched_root = _match_allowed_root(resolved_dest, allowed_dirs)
    if matched_root is None:
        raise ValueError(
            "Output path is outside the allowed workspace directory. "
            "Configure TWEEKIT_ALLOWED_DIRS to permit this directory."
        )
    if _is_sensitive_relative_path(resolved_dest, matched_root):
        raise ValueError("Writing to sensitive credential, configuration, or dotfile paths is prohibited.")

    out_ext = _normalize_extension(resolved_dest.suffix)
    if not out_ext or out_ext in _BLOCKED_OUTPUT_EXTENSIONS or out_ext not in EXTENSIVE_SUPPORTED_EXTENSIONS:
        raise ValueError(f"Disallowed or unsafe output file extension: '.{out_ext or ''}'.")

    return resolved_dest


def _read_bytes_safely(src: Path, *, enforce_sandbox: bool) -> bytes:
    """Read `src` bytes using `O_NOFOLLOW` when sandboxed so symlinks swapped post-check fail closed."""
    if not enforce_sandbox:
        return src.read_bytes()
    max_bytes = int(os.getenv("TWEEKIT_MAX_LOCAL_FILE_BYTES", str(DEFAULT_MAX_LOCAL_FILE_BYTES)))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(str(src), flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("Symbolic links are not permitted in local file paths.") from exc
        raise
    with os.fdopen(fd, "rb") as fp:
        data = fp.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"Input file exceeds maximum allowed size ({max_bytes} bytes).")
    return data


def _write_bytes_safely(dest: Path, data: bytes, *, allow_overwrite: bool) -> None:
    """Write `data` to `dest` refusing symlinks (`O_NOFOLLOW`) and exclusive-create unless overwrite is enabled."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise ValueError("Symbolic links are not permitted for output_path.")

    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    flags |= os.O_TRUNC if allow_overwrite else os.O_EXCL
    try:
        fd = os.open(str(dest), flags, 0o644)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("Symbolic links are not permitted for output_path.") from exc
        raise

    with os.fdopen(fd, "wb") as fp:
        fp.write(data)


def _extract_error_details(response: Optional[httpx.Response]) -> str:
    if response is None:
        return ""
    hints = {
        k: v
        for k, v in (response.headers or {}).items()
        if (
            k.lower().startswith("x-mediagen")
            or k.lower().startswith("x-tweekit")
            or k.lower().startswith("x-cpucoinminer")
        )
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
        logger.debug("Response body was not JSON when extracting error details.")
    text = response.text.strip() if response.text else ""
    if hints and not text:
        text = json.dumps(hints)
    return text


async def _version_impl(*, base_url: Optional[str] = None) -> str:
    """Resolve and probe the current version of the TweekIT API or On-Premises Miner Renderery."""
    try:
        target_base_url = _resolve_api_base_url(base_url)
    except ValueError as exc:
        return f"unavailable (configuration error: {exc})"
    url = f"{target_base_url}version"
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
        return "unavailable (network error)"
    except Exception:
        logger.exception("Unexpected error checking TweekIT version")
        return "unavailable (unexpected error)"


@mcp.resource("config://tweekit-version")
async def version() -> str:
    """Get current version of the TweekIT API or On-Premises Miner Renderery."""
    return await _version_impl()


@mcp.resource("config://tweekit-mcp-version")
async def mcp_version() -> str:
    """Return the TweekIT MCP server version."""
    return SERVER_VERSION


@mcp.resource("config://tweekit-runtime-mode")
async def runtime_mode() -> str:
    """Return JSON runtime introspection describing Cloud CGN vs. On-Premises Miner Renderery mode."""
    try:
        target_base_url = _resolve_api_base_url()
        is_onprem = _is_local_or_onprem_api_url(target_base_url)
    except ValueError as exc:
        return json.dumps(
            {
                "server_version": SERVER_VERSION,
                "transport": _ACTIVE_TRANSPORT,
                "error": str(exc),
            }
        )
    return json.dumps(
        {
            "server_version": SERVER_VERSION,
            "transport": _ACTIVE_TRANSPORT,
            "execution_mode": "onprem-miner-renderery" if is_onprem else "cloud-cgn",
            "api_base_url": target_base_url,
            "local_only_zero_egress": _is_local_only_mode(),
            "local_files_enabled": _is_local_files_enabled(),
            "miner_noauth_loopback": _is_miner_noauth_enabled(),
        }
    )


async def _doctype_impl(
    apiKey: str,
    apiSecret: str,
    extension: str = "*",
    *,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    cleaned_ext = "*" if (extension or "").strip() in {"", "*"} else _validate_format_token(extension, "extension")
    try:
        target_base_url = _resolve_api_base_url(base_url)
    except ValueError as exc:
        return {"error": str(exc)}
    url = f"{target_base_url}doctype"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                url,
                headers={"ApiKey": apiKey, "ApiSecret": apiSecret},
                params={"extension": cleaned_ext},
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"result": data}
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP error fetching supported file formats given '%s': %s", cleaned_ext, e)
            return {"error": f"Failed to fetch supported formats. Status: {e.response.status_code}"}
        except httpx.RequestError as e:
            logger.error("Network error fetching supported file formats given '%s': %s", cleaned_ext, e)
            return {"error": "Network error communicating with TweekIT."}
        except Exception:
            logger.exception("Unexpected error in doctype")
            return {"error": "An unexpected internal error occurred."}


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
    extension: Annotated[str, Field(description="File extension to inspect; use '*' to list all supported inputs.")] = "*",
) -> Dict[str, Any]:
    """Retrieve supported file formats or map a file extension to its TweekIT document type.

    Authentication is read exclusively from environment variables (`TWEEKIT_API_KEY` /
    `TWEEKIT_API_SECRET`) or MCP HTTP request headers (`ApiKey` / `ApiSecret`) — never place
    API secrets in prompts or tool arguments.
    """
    try:
        key, secret = _resolve_credentials()
        return await _doctype_impl(apiKey=key, apiSecret=secret, extension=extension)
    except (RuntimeError, ValueError) as exc:
        return {"error": str(exc)}


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
    """Validate whether a file format is supported by TweekIT and recommend the optimal AI-ready output format."""
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
    bgColor: str = "",
    *,
    base_url: Optional[str] = None,
) -> Any:
    try:
        safe_inext = _validate_format_token(inext, "inext")
        safe_outfmt = _validate_format_token(outfmt, "outfmt")
        url = _resolve_api_base_url(base_url)
    except ValueError as exc:
        return {"error": str(exc)}

    if not blob or len(blob) > DEFAULT_MAX_BLOB_CHARS:
        return {"error": "Invalid or oversized base64 payload (`blob`)."}

    bg = 0
    if bgColor:
        hexstr = bgColor.lstrip("#")
        try:
            bg = int(hexstr, 16)
        except ValueError:
            bg = 0

    async with httpx.AsyncClient(default_encoding="ascii", timeout=60.0) as client:
        try:
            client.headers["ApiKey"] = apiKey
            client.headers["ApiSecret"] = apiSecret
            response = await client.post(
                url,
                json={
                    "Fmt": safe_outfmt,
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
                    "DocDataType": safe_inext,
                    "DocData": blob,
                },
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type") or ""
            lowered_ct = content_type.lower()
            if lowered_ct.startswith("image/"):
                image_format = lowered_ct.split("/")[-1].split(";")[0].strip()
                return Image(data=response.content, format=image_format)
            if lowered_ct == "application/pdf":
                return File(data=response.content, format="pdf")
            if "json" in lowered_ct:
                try:
                    return response.json()
                except Exception:
                    logger.debug("Failed to parse JSON body from conversion response.")
            if lowered_ct.startswith("application/") or lowered_ct == "application/octet-stream":
                return File(data=response.content, format=safe_outfmt)

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
            error_payload["tweekitPayload"] = {
                "DocDataType": safe_inext,
                "Fmt": safe_outfmt,
            }
            logger.warning("TweekIT convert error (%s): %s", status, message or str(e))
            return error_payload
        except httpx.RequestError as e:
            logger.error("Network error calling TweekIT convert: %s", e)
            return {"error": "Network error"}
        except Exception:
            logger.exception("Unexpected error in _convert_impl")
            return {"error": "An unexpected internal error occurred."}


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
    """Convert a base64-encoded document payload with TweekIT (Cloud CGN or On-Premises Miner Renderery).

    Credentials are read securely from `TWEEKIT_API_KEY` / `TWEEKIT_API_SECRET` environment
    variables or HTTP `ApiKey` / `ApiSecret` headers. Set `TWEEKIT_API_BASE_URL=http://127.0.0.1:16377/api/image/`
    and `TWEEKIT_LOCAL_ONLY=1` for air-gapped localhost Miner Renderery processing.
    """
    try:
        key, secret = _resolve_credentials()
    except (RuntimeError, ValueError) as exc:
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
    *,
    allow_auth_headers: bool = False,
    base_url: Optional[str] = None,
    allow_remote_fetch: bool = False,
) -> Any:
    """Download a validated public HTTPS document (with connect-time IP pinning) and convert it via TweekIT."""
    try:
        _assert_outbound_internet_allowed(
            "convert_url",
            base_url=base_url,
            allow_remote_fetch_override=allow_remote_fetch,
        )
        raw_bytes, content_type, _, final_url = await _safe_fetch_remote(
            url,
            fetch_headers=fetchHeaders,
            allow_auth_headers=allow_auth_headers,
        )
    except ValueError as exc:
        return {"error": str(exc)}
    except httpx.HTTPStatusError as e:
        status = getattr(e.response, "status_code", "unknown")
        message = _extract_error_details(e.response)
        error_payload: Dict[str, Any] = {
            "error": f"Failed to download remote content. Status: {status}",
        }
        if message:
            error_payload["details"] = message
        logger.warning("HTTP error downloading '%s': status=%s", url, status)
        return error_payload
    except httpx.RequestError as e:
        logger.error("Network error downloading '%s': %s", url, e)
        return {"error": "Network error downloading remote content."}
    except Exception:
        logger.exception("Unexpected error downloading '%s'", url)
        return {"error": "Unexpected error downloading remote content."}

    if not raw_bytes:
        return {"error": "Downloaded content was empty."}

    resolved_inext = _resolve_extension(final_url, inext, content_type)
    blob = base64.b64encode(raw_bytes).decode("ascii")

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
        base_url=base_url,
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
    url: Annotated[str, Field(description="Public HTTPS download URL for the source document or image.")],
    outfmt: Annotated[str, Field(description="Requested output format to send as Fmt.")],
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
    fetchHeaders: Annotated[
        Optional[Dict[str, str]],
        Field(
            description=(
                "Optional allowlisted non-credential HTTP headers "
                "(Accept, Accept-Language, Cache-Control, If-Modified-Since, If-None-Match, Range, User-Agent)."
            )
        ),
    ] = None,
) -> Any:
    """Download a public HTTPS file (with connect-time IP pinning, redirect, and size limits) and convert via TweekIT."""
    try:
        _assert_outbound_internet_allowed("convert_url")
        key, secret = _resolve_credentials()
    except (RuntimeError, ValueError) as exc:
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
        allow_auth_headers=False,
    )


async def _convert_file_impl(
    apiKey: str,
    apiSecret: str,
    file_path: str,
    outfmt: str,
    output_path: Optional[str] = None,
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
    *,
    enforce_sandbox: bool = True,
    base_url: Optional[str] = None,
) -> Any:
    """Convert a local file on disk with opt-in workspace confinement, `O_NOFOLLOW` protection, and optional localhost-only Miner Renderery routing."""
    resolved_dest: Optional[Path] = None
    allow_overwrite = not enforce_sandbox
    try:
        target_base_url = _resolve_api_base_url(base_url)
    except ValueError as exc:
        return {"error": str(exc)}

    if _is_truthy_env("TWEEKIT_REQUIRE_LOCAL_MINER_FOR_FILES", "0") and not _is_local_or_onprem_api_url(target_base_url):
        return {
            "error": (
                "TWEEKIT_REQUIRE_LOCAL_MINER_FOR_FILES=1 requires a localhost or TWEEKIT_ONPREM_HOSTS Miner Renderery "
                "endpoint (e.g. TWEEKIT_API_BASE_URL=http://127.0.0.1:16377/api/image/) so local files never leave the host."
            )
        }

    if enforce_sandbox:
        if not _is_local_files_enabled():
            return {
                "error": (
                    "Local filesystem conversion is disabled by default for security. "
                    "Set TWEEKIT_ALLOW_LOCAL_FILES=1 and TWEEKIT_ALLOWED_DIRS=<workspace> on local stdio servers to opt in "
                    "(and optionally TWEEKIT_LOCAL_ONLY=1 with a localhost Miner Renderery for zero cloud egress)."
                )
            }
        allow_overwrite = _is_truthy_env("TWEEKIT_ALLOW_OVERWRITE", "0")
        try:
            allowed_dirs = _get_allowed_local_dirs()
            src = _validate_local_read_path(file_path, allowed_dirs)
            if output_path:
                resolved_dest = _validate_local_write_path(output_path, allowed_dirs)
                if resolved_dest.exists() and not allow_overwrite:
                    return {
                        "error": (
                            f"Refusing to overwrite existing file '{resolved_dest.name}'. "
                            "Choose a new output_path or set TWEEKIT_ALLOW_OVERWRITE=1."
                        )
                    }
        except ValueError as exc:
            return {"error": str(exc)}
    else:
        src = Path(file_path).expanduser()
        if not src.exists() or not src.is_file():
            return {"error": f"Input file not found: '{file_path}'"}
        if output_path:
            resolved_dest = Path(output_path).expanduser().resolve()

    try:
        raw_bytes = _read_bytes_safely(src, enforce_sandbox=enforce_sandbox)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Failed to read input file: {exc}"}

    if not raw_bytes:
        return {"error": "Input file is empty."}

    resolved_inext = _normalize_extension(inext or src.suffix) or "bin"
    blob = base64.b64encode(raw_bytes).decode("ascii")

    result = await _convert_impl(
        apiKey=key if (key := apiKey) else "",
        apiSecret=secret if (secret := apiSecret) else "",
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
        base_url=target_base_url,
    )

    if resolved_dest is not None and isinstance(result, (Image, File)) and getattr(result, "data", None) is not None:
        try:
            _write_bytes_safely(resolved_dest, result.data, allow_overwrite=allow_overwrite)  # type: ignore[arg-type]
            return {
                "status": "ok",
                "input_path": str(src.resolve()),
                "output_path": str(resolved_dest),
                "input_extension": resolved_inext,
                "output_format": getattr(result, "format", outfmt),
                "size_bytes": len(result.data),  # type: ignore[arg-type]
                "execution_mode": "onprem-miner-renderery" if _is_local_or_onprem_api_url(target_base_url) else "cloud-cgn",
            }
        except FileExistsError:
            return {
                "error": (
                    f"Refusing to overwrite existing file '{resolved_dest.name}'. "
                    "Choose a new output_path or set TWEEKIT_ALLOW_OVERWRITE=1."
                )
            }
        except ValueError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": f"Failed to write output file: {exc}"}

    return result


@mcp.tool(
    annotations=ToolAnnotations(
        title="Convert Local Workspace File (Opt-In)",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def convert_file(
    file_path: Annotated[str, Field(description="Path within TWEEKIT_ALLOWED_DIRS to the input document or image (requires TWEEKIT_ALLOW_LOCAL_FILES=1 and TWEEKIT_ALLOWED_DIRS).")],
    outfmt: Annotated[str, Field(description="Requested output format (e.g., pdf, png, webp, txt).")],
    output_path: Annotated[Optional[str], Field(description="Optional destination path within TWEEKIT_ALLOWED_DIRS (refuses symlinks and existing files unless TWEEKIT_ALLOW_OVERWRITE=1).")] = None,
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
    """Convert a local workspace file when explicitly opted in (`TWEEKIT_ALLOW_LOCAL_FILES=1`).

    Disabled by default and over HTTP, strictly confined to `TWEEKIT_ALLOWED_DIRS` with symlink
    rejection (`lstat` + `O_NOFOLLOW`), dotfile/credential blocking, and non-overwrite protection.
    For zero cloud egress, set `TWEEKIT_LOCAL_ONLY=1` (or `TWEEKIT_REQUIRE_LOCAL_MINER_FOR_FILES=1`)
    with an On-Premises Miner Renderery (`TWEEKIT_API_BASE_URL=http://127.0.0.1:16377/api/image/`).
    """
    if not _is_local_files_enabled():
        return {
            "error": (
                "Local filesystem conversion is disabled by default (TWEEKIT_ALLOW_LOCAL_FILES=0). "
                "Set TWEEKIT_ALLOW_LOCAL_FILES=1 and TWEEKIT_ALLOWED_DIRS=<workspace> on local stdio servers to opt in."
            )
        }

    try:
        key, secret = _resolve_credentials()
    except (RuntimeError, ValueError) as exc:
        return {"error": str(exc)}

    return await _convert_file_impl(
        apiKey=key,
        apiSecret=secret,
        file_path=file_path,
        outfmt=outfmt,
        output_path=output_path,
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
        enforce_sandbox=True,
    )


async def _delete_document_impl(
    apiKey: str,
    apiSecret: str,
    docId: str,
    *,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    safe_doc_id = _validate_doc_id(docId)
    try:
        target_base_url = _resolve_api_base_url(base_url)
    except ValueError as exc:
        return {"error": str(exc)}
    url = f"{target_base_url}{quote(safe_doc_id, safe='')}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.delete(url, headers={"ApiKey": apiKey, "ApiSecret": apiSecret})
            response.raise_for_status()
            try:
                return response.json()
            except Exception:
                return {"message": "Document deleted successfully", "docId": safe_doc_id}
        except httpx.HTTPStatusError as e:
            details = _extract_error_details(e.response)
            return {"error": f"HTTP {e.response.status_code} deleting document", "details": details}
        except httpx.RequestError:
            return {"error": "Network error communicating with TweekIT."}
        except Exception:
            logger.exception("Unexpected error in delete_document")
            return {"error": "Unexpected internal error."}


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
    docId: Annotated[str, Field(description="The alphanumeric DocId returned from a prior upload to delete.")],
) -> Dict[str, Any]:
    """Immediately delete an uploaded TweekIT document by DocId before its 20-minute auto-expiry."""
    try:
        key, secret = _resolve_credentials()
        return await _delete_document_impl(apiKey=key, apiSecret=secret, docId=docId)
    except (RuntimeError, ValueError) as exc:
        return {"error": str(exc)}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Fetch & Normalize Public HTTPS URL",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def fetch(
    url: Annotated[str, Field(description="Public HTTPS URL to retrieve and normalize.")],
) -> Any:
    """Fetch a public HTTPS URL (with connect-time IP pinning, redirect, and size limits) and return content."""
    try:
        _assert_outbound_internet_allowed("fetch")
        raw_bytes, content_type, status_code, final_url = await _safe_fetch_remote(url)
    except ValueError as exc:
        return {"error": str(exc)}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except httpx.RequestError:
        return {"error": "Network error fetching URL."}
    except Exception:
        logger.exception("Unexpected error in fetch")
        return {"error": "Unexpected internal error."}

    ct = content_type.lower()
    if ct.startswith("image/"):
        return Image(data=raw_bytes, format=ct.split("/")[-1].split(";")[0].strip())
    if ct.startswith("application/pdf"):
        return File(data=raw_bytes, format="pdf")
    if ct.startswith("text/") or "json" in ct:
        return {
            "url": final_url,
            "status": status_code,
            "content_type": ct,
            "text": raw_bytes.decode("utf-8", errors="replace"),
        }
    return File(data=raw_bytes, format="bin")


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
    max_results: Annotated[int, Field(description="Maximum number of results to return (1-10).")] = 5,
) -> Dict[str, Any]:
    """Simple web search using DuckDuckGo HTML endpoint."""
    try:
        _assert_outbound_internet_allowed("search")
    except ValueError as exc:
        return {"error": str(exc)}

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

        items: List[Dict[str, str]] = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = m.group(1)
            title = re.sub("<.*?>", "", m.group(2))
            start = m.end()
            snippet_match = re.search(
                r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(.*?)</div>',
                html[start : start + 2000],
                re.I | re.S,
            )
            snippet_html = (
                snippet_match.group(1)
                if snippet_match and snippet_match.group(1)
                else (snippet_match.group(2) if snippet_match and snippet_match.group(2) else "")
            )
            snippet = re.sub("<.*?>", "", snippet_html)
            items.append({"title": title.strip(), "url": href, "snippet": snippet.strip()})
            if len(items) >= max_results:
                break

        return {"query": query, "results": items}
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except httpx.RequestError:
        return {"error": "Network error executing search."}
    except Exception:
        logger.exception("Unexpected error in search")
        return {"error": "Unexpected internal error."}


def build_streamable_http_app():
    """Build the FastMCP Streamable HTTP Starlette app with `/mcp/` path normalization and host guard."""
    return mcp.http_app(
        path="/mcp",
        stateless_http=True,
        host_origin_protection="auto",
        middleware=[Middleware(_NormalizeMcpPathMiddleware)],
    )


def _parse_args() -> argparse.Namespace:
    default_host = os.getenv("HOST", "0.0.0.0" if os.getenv("K_SERVICE") else "127.0.0.1")
    parser = argparse.ArgumentParser(description="Run the TweekIT MCP server.")
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "stdio"],
        default=os.getenv("MCP_TRANSPORT", "streamable-http"),
        help="Transport to expose (default: streamable-http).",
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help="Host for streamable-http transport (default: 127.0.0.1 locally, 0.0.0.0 in Cloud Run/Docker).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port for streamable-http transport (default: 8080).",
    )
    parser.add_argument(
        "--api-base-url",
        default=None,
        help="Override TweekIT API or On-Premises Miner Renderery base URL (e.g., http://127.0.0.1:16377/api/image/).",
    )
    parser.add_argument(
        "--local-miner",
        action="store_true",
        help="Target the local On-Premises Miner Renderery (http://127.0.0.1:16377/api/image/) and enforce TWEEKIT_LOCAL_ONLY=1.",
    )
    return parser.parse_args()


async def _serve_http(host: str, port: int) -> None:
    app = build_streamable_http_app()
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level="warning",
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


def _apply_startup_cli_flags(args: argparse.Namespace) -> str:
    """Apply CLI flags to process environment and validate resolved API base URL.

    Raises ValueError if `--local-miner` conflicts with an explicit `TWEEKIT_LOCAL_ONLY=0`
    or `TWEEKIT_MINER_LOCAL=0` setting, or if the resulting API base URL violates
    local-only / transport-security policies.
    """
    global BASE_URL
    if getattr(args, "local_miner", False):
        explicit_local_only = os.getenv("TWEEKIT_LOCAL_ONLY", "").strip().lower()
        if explicit_local_only in {"0", "false", "no", "off"}:
            raise ValueError(
                "--local-miner conflicts with explicit TWEEKIT_LOCAL_ONLY=0; refusing to start with disabled local-only guard."
            )
        explicit_miner_local = os.getenv("TWEEKIT_MINER_LOCAL", "").strip().lower()
        if explicit_miner_local in {"0", "false", "no", "off"}:
            raise ValueError(
                "--local-miner conflicts with explicit TWEEKIT_MINER_LOCAL=0; refusing to start with disabled local miner routing."
            )
        os.environ["TWEEKIT_MINER_LOCAL"] = "1"
        os.environ["TWEEKIT_LOCAL_ONLY"] = "1"
    if getattr(args, "api_base_url", None):
        os.environ["TWEEKIT_API_BASE_URL"] = args.api_base_url
    BASE_URL = _resolve_api_base_url()
    return BASE_URL


def main() -> None:
    global _ACTIVE_TRANSPORT
    args = _parse_args()
    _ACTIVE_TRANSPORT = args.transport
    try:
        _apply_startup_cli_flags(args)
    except ValueError as exc:
        logger.error("Invalid TweekIT startup configuration: %s", exc)
        raise SystemExit(2) from exc

    if args.transport == "streamable-http":
        logger.info("TweekIT MCP server starting (HTTP) on %s:%s", args.host, args.port)
    else:
        logger.info("TweekIT MCP server starting (stdio)")

    try:
        if args.transport == "streamable-http":
            asyncio.run(_serve_http(args.host, args.port))
        else:
            asyncio.run(mcp.run_async(transport="stdio", show_banner=False))
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error("An error occurred while running the server: %s", e)
        raise
    finally:
        logger.info("Server shutdown complete.")


if __name__ == "__main__":
    main()
