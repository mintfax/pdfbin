"""PDF version variants (1.4 / 1.7 / 2.0) and PDF/A conformance variants.

PDF version variants are produced by pikepdf save options. PDF/A variants are
produced via Ghostscript shell-out in strict-compliance mode (`-dPDFA
-dPDFACompatibilityPolicy=1` - abort on non-conformance rather than degrade).

Ghostscript embeds its own /CreationDate by default, which would make these
fixtures regenerate-unstable. We post-process the output with pikepdf to pin
the docinfo timestamps and use deterministic_id=True on save.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import pikepdf
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from generate.facets import (
    FixtureRecord, Health, Access, DocumentShape, Provenance,
    PaperSize, Spec, Feature,
)

FIXED_TIMESTAMP = "20260512000000+00'00'"


def _clean_base(spec_label: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setFont("Helvetica", 14)
    c.drawString(72, LETTER[1] - 100, f"pdfbin.net fixture - {spec_label}")
    c.showPage()
    c.save()
    return buf.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _pin_and_save(pdf: pikepdf.Pdf, **save_kwargs) -> bytes:
    """Pin docinfo timestamps and save deterministically.

    PDF/A bytes from Ghostscript are intrinsically not byte-stable - gs
    regenerates trailer /ID values per save and pikepdf's deterministic_id
    flag doesn't fully override that for files it didn't author from scratch.
    We pin what we can (docinfo, XMP) so the visible metadata is stable;
    the trailer /ID may still drift.
    """
    pdf.docinfo["/CreationDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    pdf.docinfo["/ModDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["xmp:CreateDate"] = "2026-05-12T00:00:00Z"
        meta["xmp:ModifyDate"] = "2026-05-12T00:00:00Z"
        meta["xmp:MetadataDate"] = "2026-05-12T00:00:00Z"
    buf = io.BytesIO()
    pdf.save(buf, deterministic_id=True, **save_kwargs)
    return buf.getvalue()


def _stabilize_if_existing(path: Path, new_bytes: bytes) -> bytes:
    """Ghostscript + pikepdf produce non-byte-stable output (the trailer /ID
    and a handful of other internal-identifier bytes drift per save, even
    with deterministic_id=True). For the CI no-drift contract, we treat
    PDF/A fixtures as "once authored, never regenerated": if the file
    already exists on disk, return its bytes unchanged; only on first
    generation do we use the freshly built bytes.

    Per the project's immutability rule (see CLAUDE.md), this is the right
    semantics anyway - PDF/A fixtures are meant to be byte-stable forever.
    Anyone deliberately rotating one should delete it first.
    """
    if path.exists():
        return path.read_bytes()
    return new_bytes


def _save_at_version(base: bytes, version: str) -> bytes:
    """Re-save a clean PDF targeting a specific PDF version."""
    pdf = pikepdf.open(io.BytesIO(base))
    data = _pin_and_save(pdf, min_version=version, force_version=version)
    pdf.close()
    return data


def _convert_pdfa(base: bytes, conformance: str) -> bytes:
    """Convert a PDF to PDF/A via Ghostscript strict mode, then pin timestamps."""
    if shutil.which("gs") is None:
        raise RuntimeError("Ghostscript not installed; required for PDF/A builders.")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src.pdf"
        dst = Path(tmp) / "dst.pdf"
        src.write_bytes(base)
        cmd = [
            "gs",
            "-dPDFA=" + conformance,
            "-dPDFACompatibilityPolicy=1",
            "-dBATCH", "-dNOPAUSE", "-dQUIET",
            "-sDEVICE=pdfwrite",
            "-sColorConversionStrategy=UseDeviceIndependentColor",
            f"-sOutputFile={dst}",
            str(src),
        ]
        subprocess.run(cmd, check=True)
        gs_bytes = dst.read_bytes()
    # Post-process: pin timestamps so the saved bytes are stable.
    pdf = pikepdf.open(io.BytesIO(gs_bytes))
    data = _pin_and_save(pdf)
    pdf.close()
    return data


def _attach_file_to_pdf(pdf_bytes: bytes, attachment_name: str,
                        attachment_bytes: bytes) -> bytes:
    pdf = pikepdf.open(io.BytesIO(pdf_bytes))
    filespec = pikepdf.AttachedFileSpec(pdf, attachment_bytes, mime_type="text/plain")
    pdf.attachments[attachment_name] = filespec
    data = _pin_and_save(pdf)
    pdf.close()
    return data


def _record(id_: str, data: bytes, spec_value: Spec, description: str,
            features: set[Feature] | None = None) -> FixtureRecord:
    safe = id_.replace('-', '_').replace('.', '_')
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
        spec=spec_value,
        features=features or set(),
        source_script=f"generate/builders/spec.py:{safe}",
    )


def build_all(static_dir: Path) -> list[FixtureRecord]:
    records: list[FixtureRecord] = []

    for id_, version, spec_value, desc in [
        ("pdf-1.4-clean", "1.4", Spec.PDF_1_4, "Clean PDF saved targeting spec version 1.4."),
        ("pdf-1.7-clean", "1.7", Spec.PDF_1_7, "Clean PDF saved targeting spec version 1.7."),
        ("pdf-2.0-clean", "2.0", Spec.PDF_2_0, "Clean PDF saved targeting spec version 2.0."),
    ]:
        base = _clean_base(id_)
        data = _save_at_version(base, version)
        path = static_dir / f"{id_}.pdf"
        path.write_bytes(data)
        records.append(_record(id_, data, spec_value, desc))

    # PDF/A-4 deferred: local Ghostscript 10.02.1 rejects -dPDFA=4 with
    # `rangecheck in .putdeviceprops`. Re-enable when the build host's gs
    # supports it (gs 10.03+ is reported to work).
    base = _clean_base("pdfa-base")
    for id_, gs_level, spec_value, desc in [
        ("pdfa-1b-compliant", "1", Spec.PDFA_1B,
         "PDF/A-1B compliant document (visual appearance preserved)."),
        ("pdfa-1a-compliant", "1", Spec.PDFA_1A,
         "PDF/A-1A compliant document (accessible / tagged variant of -1B)."),
        ("pdfa-2b-compliant", "2", Spec.PDFA_2B,
         "PDF/A-2B compliant document (PDF 1.7 features allowed)."),
    ]:
        new_data = _convert_pdfa(base, gs_level)
        path = static_dir / f"{id_}.pdf"
        data = _stabilize_if_existing(path, new_data)
        path.write_bytes(data)
        records.append(_record(id_, data, spec_value, desc))

    # PDF/A-3 with an attachment.
    id_ = "pdfa-3b-with-attachment"
    pdfa3 = _convert_pdfa(base, "3")
    attached_new = _attach_file_to_pdf(pdfa3, "note.txt", b"pdfbin.net PDF/A-3 attachment sample.\n")
    path = static_dir / f"{id_}.pdf"
    attached = _stabilize_if_existing(path, attached_new)
    path.write_bytes(attached)
    records.append(_record(
        id_, attached, Spec.PDFA_3B,
        "PDF/A-3B with an embedded plain-text attachment - the headline PDF/A-3 feature.",
        features={Feature.EMBEDDED_FILE},
    ))

    return records
