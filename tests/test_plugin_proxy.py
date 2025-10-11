import base64

import respx
from fastapi.testclient import TestClient
from httpx import Response


@respx.mock
def test_version_endpoint(proxy_app):
    client = TestClient(proxy_app)
    respx.get("https://api.test/version").mock(return_value=Response(200, text="1.2.3"))

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "1.2.3"}


@respx.mock
def test_doctype_endpoint(proxy_app):
    client = TestClient(proxy_app)
    respx.get("https://api.test/doctype").mock(
        return_value=Response(200, json={"ext": "pdf", "mime": "application/pdf"})
    )

    response = client.get("/doctype", params={"ext": "pdf"})

    assert response.status_code == 200
    assert response.json()["ext"] == "pdf"


@respx.mock
def test_convert_returns_json(proxy_app):
    client = TestClient(proxy_app)
    respx.post("https://api.test/").mock(
        return_value=Response(200, json={"status": "ok", "outfmt": "txt"})
    )

    payload = {
        "inext": "pdf",
        "outfmt": "txt",
        "blob": base64.b64encode(b"data").decode("ascii"),
    }
    response = client.post("/convert", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@respx.mock
def test_convert_returns_binary(proxy_app):
    client = TestClient(proxy_app)
    binary = b"PDFDATA"
    respx.post("https://api.test/").mock(
        return_value=Response(
            200,
            content=binary,
            headers={"content-type": "application/pdf"},
        )
    )

    payload = {
        "inext": "pdf",
        "outfmt": "pdf",
        "blob": base64.b64encode(b"data").decode("ascii"),
    }
    response = client.post("/convert", json=payload)

    assert response.status_code == 200
    assert response.content == binary
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]


def test_manifest_defaults(proxy_module):
    client = TestClient(proxy_module.app)

    response = client.get("/.well-known/ai-plugin.json")

    assert response.status_code == 200
    manifest = response.json()
    assert manifest["name_for_model"] == "tweekit"
    assert manifest["api"]["url"] == "https://plugin.test/openapi.json"
    assert manifest["logo_url"] == "https://plugin.test/logo.png"
