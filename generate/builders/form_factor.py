"""Build clean PDFs varying paper size, page count, and orientation.

Foundational builder - many other builders use the canonical clean Letter
or A4 base produced here via the internal `_make_clean()` helper.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec
)

JIS_B5_MM = (182, 257)
JIS_B5_PTS = (JIS_B5_MM[0] * 72 / 25.4, JIS_B5_MM[1] * 72 / 25.4)


def _draw_page(c: canvas.Canvas, w: float, h: float, page_no: int, label: str) -> None:
    c.setFont("Helvetica", 18)
    c.drawString(72, h - 100, f"pdfbin.net fixture - {label}")
    c.setFont("Helvetica", 12)
    c.drawString(72, h - 130, f"Page {page_no}")
    c.drawString(72, h - 150, "CC0-1.0. Bytes immutable. See /catalog.json.")
    c.showPage()


def _write_pdf(path: Path, pages: list[tuple[float, float, str]], label: str) -> None:
    """`pages` is a list of (width, height, orientation_hint) tuples."""
    c = canvas.Canvas(str(path), pageCompression=1)
    c.setTitle(f"pdfbin.net fixture: {label}")
    c.setAuthor("pdfbin.net")
    c.setSubject("CC0 test fixture")
    for i, (w, h, _) in enumerate(pages, start=1):
        c.setPageSize((w, h))
        _draw_page(c, w, h, i, label)
    c.save()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(path: Path, id_: str, page_count: int, paper_size: PaperSize,
            orientation: str, description: str) -> FixtureRecord:
    return FixtureRecord(
        id=id_,
        size_bytes=path.stat().st_size,
        sha256=_hash(path),
        page_count=page_count,
        description=description,
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=paper_size,
        orientation=orientation,
        spec=Spec.PDF_1_7,
        features=set(),
        source_script=f"generate/builders/form_factor.py:{id_.replace('-', '_')}",
    )


def build_all(static_dir: Path) -> list[FixtureRecord]:
    records: list[FixtureRecord] = []

    # Single-page baselines per paper-size family.
    for id_, size, paper, desc in [
        ("clean-a4-1page", A4, PaperSize.DIN_A4,
         "Clean DIN A4 (210x297mm), single portrait page, body text."),
        ("clean-letter-1page", LETTER, PaperSize.US_LETTER,
         "Clean US Letter (8.5x11in), single portrait page, body text."),
        ("clean-jis-b5-1page", JIS_B5_PTS, PaperSize.JIS_B5,
         "Clean JIS B5 (182x257mm) - not ISO B5. Single portrait page."),
    ]:
        path = static_dir / f"{id_}.pdf"
        _write_pdf(path, [(size[0], size[1], "portrait")], id_)
        records.append(_record(path, id_, 1, paper, "portrait", desc))

    # 3-page DIN A4 and US Letter.
    for id_, size, paper, desc in [
        ("clean-a4-3page", A4, PaperSize.DIN_A4, "Clean DIN A4, three portrait pages."),
        ("clean-letter-3page", LETTER, PaperSize.US_LETTER, "Clean US Letter, three portrait pages."),
    ]:
        path = static_dir / f"{id_}.pdf"
        _write_pdf(path, [(size[0], size[1], "portrait")] * 3, id_)
        records.append(_record(path, id_, 3, paper, "portrait", desc))

    # 100- and 500-page US Letter.
    for id_, count, desc in [
        ("clean-100-pages", 100, "Clean US Letter, 100 portrait pages."),
        ("clean-500-pages", 500, "Clean US Letter, 500 portrait pages."),
    ]:
        path = static_dir / f"{id_}.pdf"
        _write_pdf(path, [(LETTER[0], LETTER[1], "portrait")] * count, id_)
        records.append(_record(path, id_, count, PaperSize.US_LETTER, "portrait", desc))

    # Mixed orientation (5 pages alternating).
    path = static_dir / "clean-mixed-orientation.pdf"
    pages = []
    for i in range(5):
        if i % 2 == 0:
            pages.append((LETTER[0], LETTER[1], "portrait"))
        else:
            pages.append((LETTER[1], LETTER[0], "landscape"))
    _write_pdf(path, pages, "clean-mixed-orientation")
    records.append(_record(path, "clean-mixed-orientation", 5,
                           PaperSize.US_LETTER, "mixed",
                           "US Letter, alternating portrait and landscape across 5 pages."))

    # Mixed paper sizes (a4 + letter + jis-b5).
    path = static_dir / "clean-paper-sizes-mixed.pdf"
    pages = [
        (A4[0], A4[1], "portrait"),
        (LETTER[0], LETTER[1], "portrait"),
        (JIS_B5_PTS[0], JIS_B5_PTS[1], "portrait"),
    ]
    _write_pdf(path, pages, "clean-paper-sizes-mixed")
    records.append(_record(path, "clean-paper-sizes-mixed", 3,
                           PaperSize.MIXED, "portrait",
                           "Mixed paper sizes: A4, US Letter, and JIS B5 in one document."))

    return records
