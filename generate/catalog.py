"""Emit catalog.json, llms.txt, openapi.json from a list of FixtureRecord."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from generate.facets import FixtureRecord, facet_axes_vocabulary

SCHEMA_VERSION = "1.0.0"
BASE_URL = "https://pdfbin.net"


def emit_catalog(records: list[FixtureRecord], path: Path) -> None:
    doc = {
        "schema_version": SCHEMA_VERSION,
        "site": "pdfbin.net",
        "license_default": "CC0-1.0",
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "fixture_count": len(records),
        "facet_axes": facet_axes_vocabulary(),
        "fixtures": [r.to_catalog_entry(BASE_URL) for r in records],
    }
    path.write_text(json.dumps(doc, indent=2, sort_keys=False))


def emit_llms_txt(records: list[FixtureRecord], path: Path) -> None:
    body = f"""# pdfbin.net

A free CC0 library of test PDFs. Each PDF lives at a stable flat URL and
is designed to exercise one or more specific behaviors - clean, corrupt
in a known way, encrypted, large, PDF/A conformant, scanned, form-bearing,
shaped like a real document (fax cover, invoice, IRS 1040, ...), or any
combination.

## URL contract

Every PDF lives at https://pdfbin.net/<id>.pdf. Bytes are immutable; the
URL is the version. If a PDF turns out to be wrong, a new ID ships and the
old one stays available, marked status: deprecated in catalog.json.

## Discovery

- /catalog.json - typed catalog: every fixture's facets, sha256,
  page_count, license, lifecycle (added/status/superseded_by)
- /openapi.json - OpenAPI 3.1 spec with every fixture as a GET endpoint

## Facet axes

- health         valid / corrupt-{{xref-truncated, header-truncated, ...}}
- access         open / encrypted-{{aes256-owner, aes128-user, ...}}
- document_shape blank / fax-cover-sheet / invoice / receipt / irs-1040 /
                 bank-statement / contract-nda / lab-report
- provenance     digital-native / scanned-{{clean, noisy, skewed, ...}}
- paper_size     DIN-A4 / US-Letter / JIS-B5 / mixed
- spec           PDF-1.4 / PDF-1.7 / PDF-2.0 / PDF/A-1B ... PDF/A-4
- features       acroform / signed / embedded-file

## Conventions

Encrypted PDFs use owner="ownerpass", user="userpass" unless an encrypted
fixture's catalog entry says otherwise.

Total fixtures: {len(records)}.

## License

All fixtures CC0-1.0. Site code MIT. Source: github.com/mintfax/pdfbin
"""
    path.write_text(body)


def emit_openapi(records: list[FixtureRecord], path: Path) -> None:
    paths: dict[str, dict] = {}
    for r in records:
        paths[f"/{r.id}.pdf"] = {
            "get": {
                "summary": r.description,
                "tags": [
                    f"health:{r.health.value}",
                    f"document_shape:{r.document_shape.value}",
                    f"provenance:{r.provenance.value}",
                    f"spec:{r.spec.value}",
                ],
                "responses": {
                    "200": {
                        "description": "PDF fixture (CC0)",
                        "content": {
                            "application/pdf": {
                                "schema": {"type": "string", "format": "binary"}
                            }
                        },
                    }
                },
            }
        }
    doc = {
        "openapi": "3.1.0",
        "info": {
            "title": "pdfbin.net",
            "version": "1.0.0",
            "description": "Free CC0 PDF fixtures at stable flat URLs",
            "license": {"name": "CC0-1.0", "identifier": "CC0-1.0"},
        },
        "servers": [{"url": BASE_URL}],
        "paths": paths,
    }
    path.write_text(json.dumps(doc, indent=2, sort_keys=False))
