import json
from pathlib import Path
from zipfile import ZipFile

import scripts.build_claude_bundle
from scripts.build_claude_bundle import build_bundle


def test_build_bundle_overrides(tmp_path, monkeypatch):
    # Mock _vendor_dependencies to prevent downloading files over network
    monkeypatch.setattr(scripts.build_claude_bundle, "_vendor_dependencies", lambda target_dir: target_dir.mkdir(parents=True, exist_ok=True))

    # Mock _stage_server_files to just write a dummy file
    def mock_stage_server_files(server_dir):
        server_dir.mkdir(parents=True, exist_ok=True)
        (server_dir / "server.py").write_text("# dummy")
    monkeypatch.setattr(scripts.build_claude_bundle, "_stage_server_files", mock_stage_server_files)

    manifest_path = Path("claude/manifest.json")
    output_path = tmp_path / "tweekit.mcpb"

    bundle_path = build_bundle(
        manifest_path=manifest_path,
        output_path=output_path,
        version="2.0.0",
    )

    assert bundle_path.exists()

    with ZipFile(bundle_path, "r") as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["version"] == "2.0.0"
        assert "server/server.py" in bundle.namelist()
