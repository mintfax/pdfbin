"""Document-shape fixtures: fax cover, invoice, receipt, IRS 1040,
bank statement, contract NDA, lab report. Includes two cross-axis variants
(document + scanned) demonstrating the multi-facet model.

All synthesized entities use fake names (Jane Doe / Acme Widgets / Globex
Corp). The IRS 1040 is imported verbatim from generate/sources/irs-1040-blank.pdf
- see PROVENANCE.md for chain of custody.

Determinism: every reportlab Canvas / SimpleDocTemplate uses invariant=1 (or
its platypus equivalent via canvasmaker) so timestamps and internal IDs are
pinned. scan_pdf calls pass the fixture id as the noise seed.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pypdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec,
)
from generate.scanning import ScanProfile, scan_pdf


SOURCES = Path("generate/sources")


def _invariant_canvas(*args, **kwargs):
    """Canvasmaker that pins reportlab's timestamps/IDs - for SimpleDocTemplate."""
    kwargs["invariant"] = 1
    return Canvas(*args, **kwargs)


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _record(id_, data, page_count, shape, provenance, paper_size,
            description, scan_quality=None):
    return FixtureRecord(
        id=id_,
        size_bytes=len(data),
        sha256=_hash(data),
        page_count=page_count,
        description=description,
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=shape,
        provenance=provenance,
        paper_size=paper_size,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        scan_quality=scan_quality,
        source_script=f"generate/builders/documents.py:{id_.replace('-', '_')}",
    )


def _fax_cover() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)
    w, h = LETTER
    c.setFont("Helvetica-Bold", 26)
    c.drawString(72, h - 90, "FAX COVER SHEET")
    c.setFont("Helvetica", 12)
    y = h - 150
    for label, value in [
        ("To:", "John Smith"), ("From:", "Jane Doe"),
        ("Company:", "Acme Widgets Inc."),
        ("Fax:", "+1-555-0100"), ("Pages:", "3 (including this cover)"),
        ("Date:", "2026-05-12"),
        ("Re:", "Q2 inventory reconciliation"),
    ]:
        c.drawString(72, y, label)
        c.drawString(180, y, value)
        y -= 28
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(72, 100, "This fax is for testing only. CC0-1.0.")
    c.showPage()
    c.save()
    return buf.getvalue()


def _invoice() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, canvasmaker=_invariant_canvas)
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("<b>INVOICE</b>", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Acme Widgets Inc. <br/>123 Main St <br/>Springfield, IL", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Bill To: Globex Corp.", styles["Normal"]),
        Spacer(1, 12),
        Table(
            [["Description", "Qty", "Price", "Total"],
             ["Widget Type A", "10", "$5.00", "$50.00"],
             ["Widget Type B", "4", "$12.50", "$50.00"],
             ["Shipping", "1", "$10.00", "$10.00"],
             ["", "", "Total", "$110.00"]],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ])
        ),
    ]
    doc.build(flow)
    return buf.getvalue()


def _receipt() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)
    w, h = LETTER
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, h - 80, "Acme Coffee Shop")
    c.setFont("Helvetica", 10)
    c.drawString(72, h - 100, "Receipt #100023 - 2026-05-12 09:14")
    y = h - 140
    for line, price in [("Latte", "$4.50"), ("Croissant", "$3.25"), ("Tip", "$1.00")]:
        c.drawString(72, y, line)
        c.drawRightString(w - 72, y, price)
        y -= 16
    c.line(72, y - 4, w - 72, y - 4)
    c.drawString(72, y - 24, "Total")
    c.drawRightString(w - 72, y - 24, "$8.75")
    c.showPage()
    c.save()
    return buf.getvalue()


def _bank_statement() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, canvasmaker=_invariant_canvas)
    styles = getSampleStyleSheet()
    rows = [["Date", "Description", "Amount", "Balance"]]
    for d, desc, amt, bal in [
        ("2026-04-15", "Opening balance", "", "$1,250.00"),
        ("2026-04-18", "Direct deposit", "+$3,400.00", "$4,650.00"),
        ("2026-04-22", "Rent", "-$1,800.00", "$2,850.00"),
        ("2026-04-30", "Closing balance", "", "$2,850.00"),
    ]:
        rows.append([d, desc, amt, bal])
    flow = [
        Paragraph("<b>Globex Bank - Account Statement</b>", styles["Title"]),
        Paragraph("Account #****1234 - Period: 2026-04-01 to 2026-04-30", styles["Normal"]),
        Spacer(1, 12),
        Table(rows, style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ])),
    ]
    doc.build(flow)
    return buf.getvalue()


def _contract_nda() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, canvasmaker=_invariant_canvas)
    styles = getSampleStyleSheet()
    body = (
        "This Mutual Non-Disclosure Agreement is entered into between Acme "
        "Widgets Inc. ('Discloser') and Globex Corp. ('Recipient') as of "
        "2026-05-12. The parties agree to maintain in confidence all "
        "non-public information disclosed in connection with discussions of "
        "a potential commercial relationship..."
    ) * 3
    flow = [
        Paragraph("<b>MUTUAL NON-DISCLOSURE AGREEMENT</b>", styles["Title"]),
        Spacer(1, 24),
        Paragraph(body, styles["BodyText"]),
        Spacer(1, 36),
        Paragraph("________________________________", styles["Normal"]),
        Paragraph("Jane Doe, Acme Widgets Inc.", styles["Normal"]),
    ]
    doc.build(flow)
    return buf.getvalue()


def _lab_report() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, canvasmaker=_invariant_canvas)
    styles = getSampleStyleSheet()
    flow = [
        Paragraph("<b>Globex Diagnostics Lab Report</b>", styles["Title"]),
        Paragraph("Patient: John Doe - DOB: 1980-01-01 - Collected: 2026-05-10",
                  styles["Normal"]),
        Spacer(1, 12),
        Table(
            [["Test", "Result", "Reference", "Flag"],
             ["Hemoglobin", "14.2 g/dL", "13.5 - 17.5", ""],
             ["Glucose", "112 mg/dL", "70 - 99", "HIGH"],
             ["Cholesterol", "190 mg/dL", "<200", ""]],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ])
        ),
    ]
    doc.build(flow)
    return buf.getvalue()


def build_all(static_dir: Path) -> list[FixtureRecord]:
    out: list[FixtureRecord] = []

    digital_native_shapes = [
        ("fax-cover-letter-clean", _fax_cover(), DocumentShape.FAX_COVER_SHEET,
         "Fax cover sheet on US Letter (To/From/Company/Fax/Pages/Date/Re). Synthesized."),
        ("invoice-letter-clean", _invoice(), DocumentShape.INVOICE,
         "Invoice on US Letter with line items and totals. Synthesized."),
        ("receipt-letter-clean", _receipt(), DocumentShape.RECEIPT,
         "Coffee-shop receipt on US Letter. Synthesized."),
        ("bank-statement-letter-clean", _bank_statement(), DocumentShape.BANK_STATEMENT,
         "Bank account statement on US Letter. Synthesized."),
        ("contract-nda-letter-clean", _contract_nda(), DocumentShape.CONTRACT_NDA,
         "Mutual non-disclosure agreement on US Letter. Synthesized."),
        ("lab-report-letter-clean", _lab_report(), DocumentShape.LAB_REPORT,
         "Diagnostics lab report on US Letter. Synthesized."),
    ]

    # reportlab's SimpleDocTemplate (platypus) doesn't produce fully byte-stable
    # output across regenerations even with invariant=1 via canvasmaker. We use
    # the project-wide "once authored, never regenerated" pattern: if a fixture
    # already exists on disk, keep those bytes. Delete to deliberately rotate.
    for id_, new_data, shape, desc in digital_native_shapes:
        path = static_dir / f"{id_}.pdf"
        if path.exists():
            data = path.read_bytes()
        else:
            data = new_data
            path.write_bytes(data)
        out.append(_record(id_, data, 1, shape, Provenance.DIGITAL_NATIVE,
                           PaperSize.US_LETTER, desc))

    # IRS 1040: imported verbatim.
    irs_src = SOURCES / "irs-1040-blank.pdf"
    irs_data = irs_src.read_bytes()
    (static_dir / "irs-1040-blank.pdf").write_bytes(irs_data)
    pages = len(pypdf.PdfReader(io.BytesIO(irs_data)).pages)
    out.append(_record(
        "irs-1040-blank", irs_data, pages, DocumentShape.IRS_1040,
        Provenance.DIGITAL_NATIVE, PaperSize.US_LETTER,
        "Blank IRS Form 1040, imported verbatim from irs.gov. US federal work, public domain."
    ))

    # Cross-axis: scanned fax cover.
    fc_clean = _fax_cover()
    fc_scanned = scan_pdf(fc_clean, ScanProfile(300, "high", 0),
                          seed="fax-cover-letter-scanned-noisy")
    (static_dir / "fax-cover-letter-scanned-noisy.pdf").write_bytes(fc_scanned)
    out.append(_record(
        "fax-cover-letter-scanned-noisy", fc_scanned, 1,
        DocumentShape.FAX_COVER_SHEET, Provenance.SCANNED_NOISY,
        PaperSize.US_LETTER,
        "Fax cover sheet rendered as a noisy 300 DPI scan - realistic faxed-document case.",
        scan_quality={"dpi": 300, "noise": "high", "skew_degrees": 0},
    ))

    # Cross-axis: scanned receipt.
    r_clean = _receipt()
    r_scanned = scan_pdf(r_clean, ScanProfile(300, "high", 0),
                         seed="receipt-scanned-noisy-300dpi")
    (static_dir / "receipt-scanned-noisy-300dpi.pdf").write_bytes(r_scanned)
    out.append(_record(
        "receipt-scanned-noisy-300dpi", r_scanned, 1,
        DocumentShape.RECEIPT, Provenance.SCANNED_NOISY,
        PaperSize.US_LETTER,
        "Receipt rendered as a noisy 300 DPI scan - classic crumpled-receipt OCR target.",
        scan_quality={"dpi": 300, "noise": "high", "skew_degrees": 0},
    ))

    return out
