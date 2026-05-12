"""AcroForm fixtures: empty, partially-filled, fully-filled.

The 'signed' variant is deferred to v1.1. A real signed PDF requires a
non-trivial signing stack (pyhanko + cryptography + an ephemeral cert) and
the resulting signature wouldn't verify anyway (self-signed, no trusted
CA). The Feature.SIGNED enum stays reserved for that future fixture.

All three current fixtures expose a three-field AcroForm (name, email,
phone). The partially-filled and fully-filled variants pre-populate field
values via reportlab's `canvas.acroForm.textfield(value=...)`.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec, Feature,
)


def _make_form_pdf(field_values: dict[str, str]) -> bytes:
    """Generate a PDF containing three AcroForm text fields. Pre-fill those
    listed in `field_values`."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setFont("Helvetica", 14)
    c.drawString(72, LETTER[1] - 80, "pdfbin.net AcroForm fixture")
    c.setFont("Helvetica", 10)
    c.drawString(72, LETTER[1] - 110, "Three text fields below. Tab to navigate.")

    form = c.acroForm
    y = LETTER[1] - 180
    for name in ("name", "email", "phone"):
        c.drawString(72, y + 4, f"{name}:")
        form.textfield(
            name=name,
            tooltip=name,
            x=160, y=y, width=240, height=20,
            value=field_values.get(name, ""),
            borderColor=Color(0.5, 0.5, 0.5),
            fillColor=Color(1, 1, 1),
            forceBorder=True,
        )
        y -= 40

    c.showPage()
    c.save()
    return buf.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _record(id_: str, data: bytes, description: str,
            features: set[Feature]) -> FixtureRecord:
    return FixtureRecord(
        id=id_,
        size_bytes=len(data),
        sha256=_hash(data),
        page_count=1,
        description=description,
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=features,
        source_script=f"generate/builders/features.py:{id_.replace('-', '_')}",
    )


def build_all(static_dir: Path) -> list[FixtureRecord]:
    records: list[FixtureRecord] = []

    empty = _make_form_pdf({})
    (static_dir / "acroform-empty.pdf").write_bytes(empty)
    records.append(_record(
        "acroform-empty", empty,
        "PDF with three empty AcroForm text fields (name, email, phone).",
        {Feature.ACROFORM},
    ))

    partial = _make_form_pdf({"name": "Jane Doe"})
    (static_dir / "acroform-partially-filled.pdf").write_bytes(partial)
    records.append(_record(
        "acroform-partially-filled", partial,
        "AcroForm with the name field filled; email and phone left empty.",
        {Feature.ACROFORM},
    ))

    full = _make_form_pdf({
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
    })
    (static_dir / "acroform-fully-filled.pdf").write_bytes(full)
    records.append(_record(
        "acroform-fully-filled", full,
        "AcroForm with all three fields filled (name, email, phone).",
        {Feature.ACROFORM},
    ))

    return records
