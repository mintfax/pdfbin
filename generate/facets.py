"""Controlled vocabulary for fixture facets, plus typed record model.

Single source of truth for what values each facet axis may take. Builders
must use these enums; the catalog emitter relies on the enum membership for
validation. Adding a new value bumps the catalog schema_version.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class Health(str, Enum):
    VALID = "valid"
    CORRUPT_XREF_TRUNCATED = "corrupt-xref-truncated"
    CORRUPT_HEADER_TRUNCATED = "corrupt-header-truncated"
    CORRUPT_STREAM_LENGTH_MISMATCH = "corrupt-stream-length-mismatch"
    CORRUPT_OBJECT_GENERATION_MISMATCH = "corrupt-object-generation-mismatch"
    CORRUPT_TRAILER_MISSING = "corrupt-trailer-missing"
    CORRUPT_EOF_MISSING = "corrupt-eof-missing"
    CORRUPT_BYTE_FLIPPED = "corrupt-byte-flipped"


class Access(str, Enum):
    OPEN = "open"
    ENCRYPTED_AES256_OWNER = "encrypted-aes256-owner"
    ENCRYPTED_AES256_USER = "encrypted-aes256-user"
    ENCRYPTED_AES256_BOTH = "encrypted-aes256-both"
    ENCRYPTED_AES128_OWNER = "encrypted-aes128-owner"
    ENCRYPTED_AES128_USER = "encrypted-aes128-user"
    ENCRYPTED_RC4_128_OWNER = "encrypted-rc4-128-owner"
    ENCRYPTED_RC4_40_OWNER = "encrypted-rc4-40-owner"


class DocumentShape(str, Enum):
    BLANK = "blank"
    FAX_COVER_SHEET = "fax-cover-sheet"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    IRS_1040 = "irs-1040"
    BANK_STATEMENT = "bank-statement"
    CONTRACT_NDA = "contract-nda"
    LAB_REPORT = "lab-report"


class Provenance(str, Enum):
    DIGITAL_NATIVE = "digital-native"
    SCANNED_CLEAN = "scanned-clean"
    SCANNED_NOISY = "scanned-noisy"
    SCANNED_SKEWED = "scanned-skewed"
    SCANNED_NOISY_SKEWED = "scanned-noisy-skewed"


class PaperSize(str, Enum):
    DIN_A4 = "DIN-A4"
    US_LETTER = "US-Letter"
    JIS_B5 = "JIS-B5"
    MIXED = "mixed"


class Spec(str, Enum):
    PDF_1_4 = "PDF-1.4"
    PDF_1_7 = "PDF-1.7"
    PDF_2_0 = "PDF-2.0"
    PDFA_1B = "PDF/A-1B"
    PDFA_1A = "PDF/A-1A"
    PDFA_2B = "PDF/A-2B"
    PDFA_3B = "PDF/A-3B"
    PDFA_4 = "PDF/A-4"


class Feature(str, Enum):
    ACROFORM = "acroform"
    SIGNED = "signed"
    EMBEDDED_FILE = "embedded-file"


Orientation = Literal["portrait", "landscape", "mixed"]


class FixtureRecord(BaseModel):
    """Typed record emitted by every builder. Validated by the pipeline.

    The catalog entry serialization (`to_catalog_entry`) flattens facets
    into a nested `facets` object, which is the contract for catalog.json.
    """
    model_config = ConfigDict(use_enum_values=False)

    id: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    page_count: int = Field(ge=1)
    description: str = Field(min_length=1)
    health: Health
    access: Access
    document_shape: DocumentShape
    provenance: Provenance
    paper_size: PaperSize
    orientation: Orientation
    spec: Spec
    features: set[Feature]
    passwords: Optional[dict] = None        # {"owner": str|None, "user": str|None}
    scan_quality: Optional[dict] = None     # {"dpi": int, "noise": "low|high", "skew_degrees": int}
    source_script: str = Field(min_length=1)
    added: str = "2026-05-12"
    status: Literal["current", "deprecated"] = "current"
    superseded_by: Optional[str] = None

    def facets_dict(self) -> dict:
        d = {
            "health": self.health.value,
            "access": self.access.value,
            "document_shape": self.document_shape.value,
            "provenance": self.provenance.value,
            "paper_size": self.paper_size.value,
            "orientation": self.orientation,
            "spec": self.spec.value,
            "features": sorted(f.value for f in self.features),
        }
        if self.passwords is not None:
            d["passwords"] = self.passwords
        if self.scan_quality is not None:
            d["scan_quality"] = self.scan_quality
        return d

    def to_catalog_entry(self, base_url: str = "https://pdfbin.net") -> dict:
        return {
            "id": self.id,
            "url": f"{base_url}/{self.id}.pdf",
            "added": self.added,
            "status": self.status,
            "superseded_by": self.superseded_by,
            "license": "CC0-1.0",
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "page_count": self.page_count,
            "description": self.description,
            "facets": self.facets_dict(),
            "source_script": self.source_script,
        }


def facet_axes_vocabulary() -> dict[str, list[str]]:
    """Snapshot the controlled vocabularies; embedded in catalog.json."""
    return {
        "health": [m.value for m in Health],
        "access": [m.value for m in Access],
        "document_shape": [m.value for m in DocumentShape],
        "provenance": [m.value for m in Provenance],
        "paper_size": [m.value for m in PaperSize],
        "spec": [m.value for m in Spec],
        "features": [m.value for m in Feature],
    }
