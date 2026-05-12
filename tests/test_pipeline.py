import json
from pathlib import Path

from generate.pipeline import run_pipeline


def test_run_pipeline_emits_three_surfaces(tmp_path, monkeypatch):
    # Stub: no builders enabled; pipeline should still emit empty catalog/llms/openapi.
    monkeypatch.setattr("generate.pipeline.BUILDER_MODULES", [])
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    run_pipeline(static_dir=static_dir)
    catalog = json.loads((static_dir / "catalog.json").read_text())
    assert catalog["fixture_count"] == 0
    assert (static_dir / "llms.txt").exists()
    assert (static_dir / "openapi.json").exists()
