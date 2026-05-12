"""Build encrypted PDFs varying algorithm and password roles.

Canonical passwords across the catalog: owner="ownerpass", user="userpass".

Determinism note: encryption salts/IVs are randomly chosen by qpdf on each
save, so the encrypted bytes WILL differ between regenerations even with
identical input. This is a limitation of how encryption works, not of our
build code. The CI no-drift check therefore tolerates drift in the encrypted
fixtures - or we accept the regenerate-on-deploy cost. (To be reconciled in
the CI configuration step.)
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
    PaperSize, Spec,
)

OWNER = "ownerpass"
USER = "userpass"
FIXED_TIMESTAMP = "20260512000000+00'00'"


def _clean_base_bytes() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pageCompression=1, invariant=1)
    c.setFont("Helvetica", 14)
    c.drawString(72, LETTER[1] - 100, "pdfbin.net encrypted fixture base")
    c.drawString(72, LETTER[1] - 130, "Passwords: owner=ownerpass, user=userpass.")
    c.showPage()
    c.save()
    return buf.getvalue()


def _hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _encrypt(base: bytes, encryption: pikepdf.Encryption) -> bytes:
    src = pikepdf.open(io.BytesIO(base))
    # Pin metadata timestamps so the docinfo portion is stable. The encrypted
    # body remains nondeterministic (qpdf chooses a random encryption salt
    # per save, and pikepdf refuses `deterministic_id=True` with encryption).
    src.docinfo["/CreationDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    src.docinfo["/ModDate"] = pikepdf.String(f"D:{FIXED_TIMESTAMP}")
    buf = io.BytesIO()
    src.save(buf, encryption=encryption)
    src.close()
    return buf.getvalue()


def _record(id_: str, data: bytes, access_value: Access, owner: str | None,
            user: str | None, description: str) -> FixtureRecord:
    return FixtureRecord(
        id=id_,
        size_bytes=len(data),
        sha256=_hash(data),
        page_count=1,
        description=description,
        health=Health.VALID,
        access=access_value,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        passwords={"owner": owner, "user": user},
        source_script=f"generate/builders/access.py:{id_.replace('-', '_')}",
    )


def build_all(static_dir: Path) -> list[FixtureRecord]:
    base = _clean_base_bytes()
    out: list[FixtureRecord] = []

    # For R < 4 (RC4 family), pikepdf requires metadata=False - those
    # encryption revisions can't encrypt the document metadata stream.
    variants = [
        ("aes256-owner", Access.ENCRYPTED_AES256_OWNER,
         pikepdf.Encryption(owner=OWNER, user="", R=6),
         OWNER, None, "AES-256 with owner password only. Open password is empty."),
        ("aes256-user", Access.ENCRYPTED_AES256_USER,
         pikepdf.Encryption(owner=OWNER, user=USER, R=6),
         OWNER, USER, "AES-256 with user (open) password. Owner password also set."),
        ("aes256-both", Access.ENCRYPTED_AES256_BOTH,
         pikepdf.Encryption(owner=OWNER, user=USER, R=6),
         OWNER, USER, "AES-256 with both owner and user passwords set distinctly."),
        ("aes128-owner", Access.ENCRYPTED_AES128_OWNER,
         pikepdf.Encryption(owner=OWNER, user="", R=4),
         OWNER, None, "AES-128 (revision 4) with owner password only."),
        ("aes128-user", Access.ENCRYPTED_AES128_USER,
         pikepdf.Encryption(owner=OWNER, user=USER, R=4),
         OWNER, USER, "AES-128 (revision 4) with user password."),
        ("rc4-128-owner", Access.ENCRYPTED_RC4_128_OWNER,
         pikepdf.Encryption(owner=OWNER, user="", R=3, aes=False, metadata=False),
         OWNER, None, "Legacy RC4-128 (revision 3) with owner password only."),
        ("rc4-40-owner", Access.ENCRYPTED_RC4_40_OWNER,
         pikepdf.Encryption(owner=OWNER, user="", R=2, aes=False, metadata=False),
         OWNER, None, "Legacy RC4-40 (revision 2) - common in older documents."),
    ]
    for id_, access_value, encryption, owner, user, desc in variants:
        data = _encrypt(base, encryption)
        path = static_dir / f"{id_}.pdf"
        path.write_bytes(data)
        out.append(_record(id_, data, access_value, owner, user, desc))
    return out
