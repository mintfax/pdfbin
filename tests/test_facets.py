import pytest
from pydantic import ValidationError
from generate.facets import FixtureRecord, Health, Access, DocumentShape, Provenance, PaperSize, Spec, Feature


def test_minimal_valid_record():
    r = FixtureRecord(
        id="clean-letter-1page",
        size_bytes=12345,
        sha256="a" * 64,
        page_count=1,
        description="Minimal clean Letter, one page.",
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        source_script="generate/builders/form_factor.py:clean_letter_1page",
    )
    assert r.id == "clean-letter-1page"
    assert r.facets_dict()["health"] == "valid"


def test_unknown_health_value_rejected():
    with pytest.raises(ValidationError):
        FixtureRecord(
            id="x", size_bytes=1, sha256="a"*64, page_count=1, description="x",
            health="corrupt-not-a-real-value",
            access=Access.OPEN, document_shape=DocumentShape.BLANK,
            provenance=Provenance.DIGITAL_NATIVE, paper_size=PaperSize.US_LETTER,
            orientation="portrait", spec=Spec.PDF_1_7, features=set(),
            source_script="x:y",
        )


def test_encrypted_record_carries_passwords():
    r = FixtureRecord(
        id="aes256-owner", size_bytes=2000, sha256="b"*64, page_count=1,
        description="AES-256 with owner password only.",
        health=Health.VALID,
        access=Access.ENCRYPTED_AES256_OWNER,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.DIGITAL_NATIVE,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        passwords={"owner": "ownerpass", "user": None},
        source_script="generate/builders/access.py:aes256_owner",
    )
    d = r.to_catalog_entry()
    assert d["facets"]["access"] == "encrypted-aes256-owner"
    assert d["facets"]["passwords"] == {"owner": "ownerpass", "user": None}


def test_scanned_record_carries_scan_quality():
    r = FixtureRecord(
        id="scanned-noisy-300dpi", size_bytes=300000, sha256="c"*64, page_count=1,
        description="Noisy 300 DPI scan.",
        health=Health.VALID,
        access=Access.OPEN,
        document_shape=DocumentShape.BLANK,
        provenance=Provenance.SCANNED_NOISY,
        paper_size=PaperSize.US_LETTER,
        orientation="portrait",
        spec=Spec.PDF_1_7,
        features=set(),
        scan_quality={"dpi": 300, "noise": "high", "skew_degrees": 0},
        source_script="generate/builders/provenance.py:scanned_noisy_300dpi",
    )
    d = r.to_catalog_entry()
    assert d["facets"]["scan_quality"]["dpi"] == 300
