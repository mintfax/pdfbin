"""Scanned variants of a clean Letter base, without any document shape.

Each fixture is the same base PDF run through scan_pdf() with a different
ScanProfile (dpi + noise level + skew degrees). The base canvas uses
invariant=1 for stable bytes, and scan_pdf is seeded by the fixture id so
the noise is deterministic.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec,
)
from generate.scanning import ScanProfile, scan_pdf


def _clean_letter_base() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setFont("Helvetica", 18)
    c.drawString(72, LETTER[1] - 100, "pdfbin.net scanned-variant base")
    c.setFont("Helvetica", 12)
    c.drawString(72, LETTER[1] - 130, "Source for provenance.py scans.")
    c.drawString(72, LETTER[1] - 150,
                 "Body text continues. Lorem ipsum dolor sit amet, "
                 "consectetur adipiscing elit.")
    c.showPage()
    c.save()
    return buf.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _record(id_: str, data: bytes, scan_quality: dict, description: str,
            provenance_value: Provenance) -> FixtureRecord:
    return FixtureRecord(
        id=id_,
        size_bytes=len(data),
        sha256=_hash(data),
        page_count=1,
        description=description,
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=provenance_value,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        scan_quality=scan_quality,
        source_script=f"generate/builders/provenance.py:{id_.replace('-', '_')}",
    )


def build_all(static_dir: Path) -> list[FixtureRecord]:
    base = _clean_letter_base()
    out: list[FixtureRecord] = []
    variants = [
        ("scanned-clean-300dpi", ScanProfile(300, "", 0),
         {"dpi": 300, "noise": None, "skew_degrees": 0},
         Provenance.SCANNED_CLEAN,
         "Clean 300 DPI scan of a generic Letter PDF."),
        ("scanned-clean-200dpi", ScanProfile(200, "", 0),
         {"dpi": 200, "noise": None, "skew_degrees": 0},
         Provenance.SCANNED_CLEAN,
         "Clean 200 DPI scan of a generic Letter PDF."),
        ("scanned-noisy-300dpi", ScanProfile(300, "high", 0),
         {"dpi": 300, "noise": "high", "skew_degrees": 0},
         Provenance.SCANNED_NOISY,
         "Noisy 300 DPI scan with high-density speckle noise."),
        ("scanned-skewed-3deg", ScanProfile(300, "", 3.0),
         {"dpi": 300, "noise": None, "skew_degrees": 3},
         Provenance.SCANNED_SKEWED,
         "Clean 300 DPI scan rotated 3 degrees."),
        ("scanned-skewed-noisy", ScanProfile(300, "high", 3.0),
         {"dpi": 300, "noise": "high", "skew_degrees": 3},
         Provenance.SCANNED_NOISY_SKEWED,
         "Noisy 3-degree skewed 300 DPI scan - hardest realistic case."),
    ]
    for id_, profile, sq, prov, desc in variants:
        data = scan_pdf(base, profile, seed=id_)
        path = static_dir / f"{id_}.pdf"
        path.write_bytes(data)
        out.append(_record(id_, data, sq, desc, prov))
    return out
