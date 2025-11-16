import os
from urllib.parse import urljoin

import pytest
import httpx


BASE_URL = os.getenv("CHATGPT_PROXY_BASE_URL")
if BASE_URL:
    BASE_URL = BASE_URL.rstrip("/")
BEARER = os.getenv("CHATGPT_PROXY_BEARER") or os.getenv("TWEEKIT_API_KEY")


pytestmark = pytest.mark.skipif(
    not BASE_URL,
    reason="CHATGPT_PROXY_BASE_URL is not set; skipping live ChatGPT proxy tests.",
)


def _get(path: str, *, headers: dict[str, str] | None = None, params: dict | None = None) -> httpx.Response:
    url = urljoin(f"{BASE_URL}/", path.lstrip("/"))
    response = httpx.get(url, headers=headers, params=params, timeout=30.0)
    response.raise_for_status()
    return response


def _post(path: str, json: dict, *, headers: dict[str, str] | None = None) -> httpx.Response:
    url = urljoin(f"{BASE_URL}/", path.lstrip("/"))
    response = httpx.post(url, json=json, headers=headers, timeout=30.0)
    response.raise_for_status()
    return response


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    if not BEARER:
        pytest.skip("CHATGPT_PROXY_BEARER or TWEEKIT_API_KEY environment variable required")
    return {"Authorization": f"Bearer {BEARER}"}


def test_manifest_exposes_openapi() -> None:
    resp = _get("/.well-known/ai-plugin.json")
    manifest = resp.json()
    assert manifest["name_for_model"] == "tweekit"
    api_url = manifest["api"]["url"]
    # Sanity check that the manifest's URL matches the proxy hostname.
    assert api_url.startswith(BASE_URL), f"Manifest api.url ({api_url}) does not match {BASE_URL}"

    schema_resp = httpx.get(api_url, timeout=30.0)
    schema_resp.raise_for_status()
    openapi = schema_resp.json()
    for path in ("/version", "/doctype", "/convert"):
        assert path in openapi["paths"], f"{path} missing from OpenAPI document"


def test_version_endpoint(auth_headers: dict[str, str]) -> None:
    resp = _get("/version", headers=auth_headers)
    body = resp.json()
    assert "version" in body
    assert isinstance(body["version"], str)


def test_doctype_endpoint(auth_headers: dict[str, str]) -> None:
    resp = _get("/doctype", headers=auth_headers, params={"ext": "pdf"})
    data = resp.json()
    assert isinstance(data, (dict, list))


def test_convert_endpoint(auth_headers: dict[str, str]) -> None:
    payload = {
        "inext": "png",
        "outfmt": "png",
        "blob": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAn0B9n6zkS4AAAAASUVORK5CYII=",
    }
    resp = _post("/convert", json=payload, headers=auth_headers)
    # convert returns either JSON metadata or a binary payload; we just assert success here.
    assert resp.status_code == 200
