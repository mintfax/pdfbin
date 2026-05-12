"""Byte-size-targeted clean PDFs. GH Pages caps at 100MB per file; we cap at 50MB.

Each fixture is a small reportlab-generated base PDF with a binary blob
attached via pikepdf's embedded-file mechanism. The blob is deterministic
(SHA-256 expansion of the fixture ID) so the saved bytes are stable across
regenerations - required for the CI no-drift check.

Memory peak per fixture is target_bytes (one bytearray allocation), not
5x via Python tuples. Because the padding is an embedded file, the
fixture's facets include features={Feature.EMBEDDED_FILE}.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pikepdf
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec, Feature,
)

# Fixed reference date so reportlab/pikepdf don't embed `time.time()` into
# CreationDate / ModDate. Without this, every regenerate would alter the
# PDF bytes and break CI's no-drift check.
FIXED_TIMESTAMP = "20260512000000+00'00'"
TARGETS_MB = [1, 10, 25, 50]


def _deterministic_bytes(seed: str, n: int) -> bytes:
    """Generate n bytes from a seed string via SHA-256 counter expansion.

    Same seed → same bytes, every time. Different seeds → unrelated outputs.
    Peak memory is n bytes (one bytearray).
    """
    out = bytearray(n)
    counter = 0
    pos = 0
    while pos < n:
        block = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
        take = min(len(block), n - pos)
        out[pos:pos + take] = block[:take]
        pos += take
        counter += 1
    return bytes(out)


def _base_pdf(id_: str, mb: int) -> bytes:
    """Generate a small clean Letter PDF used as the base for size padding."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setTitle(f"pdfbin.net fixture: {id_}")
    c.setAuthor("pdfbin.net")
    c.setSubject("CC0 test fixture (size-targeted)")
    c.setFont("Helvetica", 18)
    c.drawString(72, LETTER[1] - 100, f"pdfbin.net fixture - {id_}")
    c.setFont("Helvetica", 12)
    c.drawString(72, LETTER[1] - 130, f"Size-targeted to approximately {mb} MB.")
    c.drawString(72, LETTER[1] - 150, "Padding via attached binary file (deterministic bytes).")
    c.drawString(72, LETTER[1] - 170, "CC0-1.0. See /catalog.json.")
    c.showPage()
    c.save()
    return buf.getvalue()


def _pad_with_attachment(base_pdf_bytes: bytes, target_bytes: int, seed: str) -> bytes:
    """Attach a deterministic blob sized to make the saved PDF approximate target_bytes."""
    pdf = pikepdf.open(io.BytesIO(base_pdf_bytes))
    chrome_estimate = len(base_pdf_bytes) + 2048
    payload_size = max(target_bytes - chrome_estimate, 0)
    blob = _deterministic_bytes(seed, payload_size)
    filespec = pikepdf.AttachedFileSpec(pdf, blob, mime_type="application/octet-stream")
    pdf.attachments["padding.bin"] = filespec
    # Pin timestamps so the saved PDF is byte-stable.
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["xmp:CreateDate"] = "2026-05-12T00:00:00Z"
        meta["xmp:ModifyDate"] = "2026-05-12T00:00:00Z"
    pdf.docinfo["/CreationDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    pdf.docinfo["/ModDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    out = io.BytesIO()
    pdf.save(out, deterministic_id=True)
    return out.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_all(static_dir: Path) -> list[FixtureRecord]:
    records: list[FixtureRecord] = []
    for mb in TARGETS_MB:
        id_ = f"clean-{mb}mb"
        base = _base_pdf(id_, mb)
        data = _pad_with_attachment(base, mb * 1_000_000, seed=id_)
        path = static_dir / f"{id_}.pdf"
        path.write_bytes(data)
        records.append(FixtureRecord(
            id=id_,
            size_bytes=len(data),
            sha256=_hash(data),
            page_count=1,
            description=f"Clean US Letter PDF padded to approximately {mb} MB via an attached random-bytes file (embedded-file feature).",
            health=Health.VALID,
            access=Access.OPEN,
            document_shape=DocumentShape.BLANK,
            provenance=Provenance.DIGITAL_NATIVE,
            paper_size=PaperSize.US_LETTER,
            orientation="portrait",
            spec=Spec.PDF_1_7,
            features={Feature.EMBEDDED_FILE},
            source_script=f"generate/builders/size.py:clean_{mb}mb",
        ))
    return records
