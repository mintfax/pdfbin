"""Single entry point. Runs every builder, validates records, emits surfaces.

Usage:
    python -m generate.pipeline                     # default: writes to ./static
    python -m generate.pipeline --static-dir /tmp/x # custom output dir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generate.facets import FixtureRecord
from generate.catalog import emit_catalog, emit_llms_txt, emit_openapi


def emit_preview_stubs(records: list[FixtureRecord], content_dir: Path) -> None:
    """Write one content/preview/<id>.md frontmatter stub per fixture.

    These stubs trigger Hugo to render a per-PDF preview page at
    /preview/<id>/ using layouts/_default/preview.html. Stale stubs (whose
    fixture no longer exists) are removed so deletions propagate.
    """
    preview_dir = content_dir / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    valid_ids = {r.id for r in records}
    for existing in preview_dir.glob("*.md"):
        # Preserve _index.md (section page) and any other underscore-prefixed
        # Hugo special files; only sweep generated per-fixture stubs.
        if existing.name.startswith("_"):
            continue
        if existing.stem not in valid_ids:
            existing.unlink()
    for r in records:
        stub = preview_dir / f"{r.id}.md"
        description = r.description.replace('"', '\\"')
        stub.write_text(
            "---\n"
            f'title: "{r.id}.pdf - pdfbin.net"\n'
            f'description: "{description}"\n'
            "layout: preview\n"
            f"fixture_id: {r.id}\n"
            "---\n"
        )

# Builder modules in stable execution order. Each module exposes
# `build_all(static_dir: Path) -> list[FixtureRecord]`.
# Filled in as builder tasks land.
BUILDER_MODULES: list[str] = [
    "generate.builders.form_factor",
    "generate.builders.size",
    "generate.builders.health",
    "generate.builders.access",
    "generate.builders.spec",
    "generate.builders.features",
    "generate.builders.provenance",
    "generate.builders.documents",
]


def run_pipeline(static_dir: Path, content_dir: Path | None = None) -> list[FixtureRecord]:
    """Run every registered builder, sort records by id, emit all discovery surfaces."""
    static_dir.mkdir(parents=True, exist_ok=True)
    records: list[FixtureRecord] = []
    for module_path in BUILDER_MODULES:
        module = __import__(module_path, fromlist=["build_all"])
        for record in module.build_all(static_dir):
            # pydantic already validated during construction; re-affirm type.
            assert isinstance(record, FixtureRecord)
            records.append(record)
    records.sort(key=lambda r: r.id)
    emit_catalog(records, static_dir / "catalog.json")
    emit_llms_txt(records, static_dir / "llms.txt")
    emit_openapi(records, static_dir / "openapi.json")
    if content_dir is not None:
        emit_preview_stubs(records, content_dir)
    return records


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--static-dir", type=Path, default=Path("static"))
    p.add_argument("--content-dir", type=Path, default=Path("content"))
    args = p.parse_args()
    records = run_pipeline(args.static_dir, args.content_dir)
    print(f"emitted {len(records)} fixtures + catalog/llms/openapi to {args.static_dir}; "
          f"{len(records)} preview stubs to {args.content_dir}/preview/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
