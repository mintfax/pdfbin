import pytest
from pathlib import Path

from generate.builders import documents


SOURCES_DIR = Path("generate/sources")
HAS_IRS = (SOURCES_DIR / "irs-1040-blank.pdf").exists()


def test_builds_nine_document_fixtures(tmp_path):
    if not HAS_IRS:
        pytest.skip("Missing generate/sources/irs-1040-blank.pdf - see Task 13 step 1.")
    records = documents.build_all(tmp_path)
    expected = {
        "fax-cover-letter-clean", "invoice-letter-clean",
        "receipt-letter-clean", "irs-1040-blank",
        "bank-statement-letter-clean", "contract-nda-letter-clean",
        "lab-report-letter-clean",
        # Cross-axis (document + scanned):
        "fax-cover-letter-scanned-noisy",
        "receipt-scanned-noisy-300dpi",
    }
    assert {r.id for r in records} == expected


def test_irs_1040_is_imported_verbatim(tmp_path):
    if not HAS_IRS:
        pytest.skip("Missing IRS source PDF.")
    documents.build_all(tmp_path)
    src = (SOURCES_DIR / "irs-1040-blank.pdf").read_bytes()
    out = (tmp_path / "irs-1040-blank.pdf").read_bytes()
    assert src == out
