"""Build deterministically-damaged PDFs. Each function applies one specific,
named damage to an in-memory clean base PDF. The byte offset(s) modified are
documented in each function and surfaced via the fixture's description.

The base is generated with reportlab's `invariant=1` flag so the substrate
bytes are stable across regenerations; the corruption mutators are pure
byte operations and therefore naturally deterministic. CI's no-drift check
depends on this.
"""

from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec,
)


def _clean_base() -> bytes:
    """A small, deterministic clean PDF used as the corruption substrate."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setTitle("pdfbin.net fixture base (clean)")
    c.setFont("Helvetica", 14)
    c.drawString(72, LETTER[1] - 100, "pdfbin.net base PDF (clean substrate)")
    c.drawString(72, LETTER[1] - 130, "Used by health.py to derive corrupt variants.")
    c.showPage()
    c.save()
    return buf.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _record(id_: str, data: bytes, page_count: int, health_value: Health,
            description: str) -> FixtureRecord:
    return FixtureRecord(
        id=id_,
        size_bytes=len(data),
        sha256=_hash(data),
        page_count=page_count,
        description=description,
        health=health_value,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        source_script=f"generate/builders/health.py:{id_.replace('-', '_')}",
    )


def _xref_truncated(base: bytes) -> bytes:
    """Truncate the file at the position of the xref table header."""
    idx = base.rfind(b"xref")
    if idx < 0:
        raise RuntimeError("base PDF has no xref")
    return base[:idx]


def _header_truncated(base: bytes) -> bytes:
    """Remove the %PDF-1.x line (8 bytes typical)."""
    nl = base.index(b"\n") + 1
    return base[nl:]


def _stream_length_mismatch(base: bytes) -> bytes:
    """Find the first /Length N stream and rewrite N to N+99 (oversized)."""
    pattern = re.compile(rb"/Length\s+(\d+)")
    m = pattern.search(base)
    if not m:
        raise RuntimeError("no /Length found in base")
    original = m.group(0)
    new_len = int(m.group(1)) + 99
    replacement = f"/Length {new_len}".encode()
    return base.replace(original, replacement, 1)


def _object_generation_mismatch(base: bytes) -> bytes:
    """Rewrite the first `N 0 obj` to `N 1 obj`. xref still says gen 0."""
    m = re.search(rb"(\d+) 0 obj", base)
    if not m:
        raise RuntimeError("no '0 obj' found")
    return base.replace(m.group(0), m.group(0).replace(b" 0 obj", b" 1 obj"), 1)


def _trailer_missing(base: bytes) -> bytes:
    """Remove the trailer dict (from 'trailer' to 'startxref')."""
    t = base.rfind(b"trailer")
    sx = base.rfind(b"startxref")
    if t < 0 or sx < 0:
        raise RuntimeError("trailer/startxref missing in base")
    return base[:t] + base[sx:]


def _eof_missing(base: bytes) -> bytes:
    """Strip the %%EOF marker."""
    return base.replace(b"%%EOF", b"", 1)


def _byte_flipped_mid_stream(base: bytes) -> bytes:
    """Flip a byte ~midway through a content stream."""
    idx = base.find(b"stream\n")
    if idx < 0:
        raise RuntimeError("no stream found")
    flip_at = idx + 100
    if flip_at >= len(base):
        flip_at = idx + 20
    out = bytearray(base)
    out[flip_at] ^= 0xFF
    return bytes(out)


def build_all(static_dir: Path) -> list[FixtureRecord]:
    base = _clean_base()
    fixtures = [
        ("xref-truncated", _xref_truncated, Health.CORRUPT_XREF_TRUNCATED,
         "PDF byte-truncated at the start of the xref table. Parsers without xref-recovery will fail."),
        ("header-truncated", _header_truncated, Health.CORRUPT_HEADER_TRUNCATED,
         "First line (%PDF-1.7) removed. Parsers that key on the header fail to detect a PDF."),
        ("stream-length-mismatch", _stream_length_mismatch, Health.CORRUPT_STREAM_LENGTH_MISMATCH,
         "One stream object's /Length is overstated by 99 bytes."),
        ("object-generation-mismatch", _object_generation_mismatch, Health.CORRUPT_OBJECT_GENERATION_MISMATCH,
         "First object's header says generation 1; xref says generation 0."),
        ("trailer-missing", _trailer_missing, Health.CORRUPT_TRAILER_MISSING,
         "Trailer dictionary removed; startxref present but points to nothing useful."),
        ("eof-missing", _eof_missing, Health.CORRUPT_EOF_MISSING,
         "%%EOF marker stripped. Parsers that key on it cannot find the end."),
        ("byte-flipped-mid-stream", _byte_flipped_mid_stream, Health.CORRUPT_BYTE_FLIPPED,
         "One byte XOR-flipped mid-content-stream. Likely renders pages with garbage."),
    ]
    records: list[FixtureRecord] = []
    for id_, mutator, health_value, desc in fixtures:
        data = mutator(base)
        path = static_dir / f"{id_}.pdf"
        path.write_bytes(data)
        records.append(_record(id_, data, 1, health_value, desc))
    return records
