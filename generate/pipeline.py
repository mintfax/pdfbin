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

# Builder modules in stable execution order. Each module exposes
# `build_all(static_dir: Path) -> list[FixtureRecord]`.
# Filled in as builder tasks land.
BUILDER_MODULES: list[str] = [
    "generate.builders.form_factor",
    "generate.builders.size",
    "generate.builders.health",
    "generate.builders.access",
]


def run_pipeline(static_dir: Path) -> list[FixtureRecord]:
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
    return records


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--static-dir", type=Path, default=Path("static"))
    args = p.parse_args()
    records = run_pipeline(args.static_dir)
    print(f"emitted {len(records)} fixtures + catalog/llms/openapi to {args.static_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
