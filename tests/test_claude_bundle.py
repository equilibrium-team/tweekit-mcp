import json
from pathlib import Path
from zipfile import ZipFile

from scripts.build_claude_bundle import build_bundle


def test_build_bundle_overrides(tmp_path):
    manifest_path = Path("claude/manifest.json")
    output_path = tmp_path / "tweekit.mcpb"

    bundle_path = build_bundle(
        manifest_path=manifest_path,
        output_path=output_path,
        server_url="https://override.example/mcp",
        version="2.0.0",
    )

    assert bundle_path.exists()

    with ZipFile(bundle_path, "r") as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["entry_point"]["url"] == "https://override.example/mcp"
        assert manifest["version"] == "2.0.0"
        assert "built_at" in manifest["metadata"]
        assert "README.md" in bundle.namelist()
