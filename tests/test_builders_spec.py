import shutil
import pytest
import pypdf
from generate.builders import spec

gs_missing = pytest.mark.skipif(shutil.which("gs") is None, reason="ghostscript not installed")


def test_builds_seven_spec_fixtures(tmp_path):
    # PDF/A-4 deferred until Ghostscript on the build host supports
    # `-dPDFA=4` (current local gs 10.02.1 rejects it with rangecheck).
    records = spec.build_all(tmp_path)
    expected = {
        "pdf-1.4-clean", "pdf-1.7-clean", "pdf-2.0-clean",
        "pdfa-1b-compliant", "pdfa-1a-compliant",
        "pdfa-2b-compliant", "pdfa-3b-with-attachment",
    }
    assert {r.id for r in records} == expected


@gs_missing
def test_pdfa_3b_carries_attachment(tmp_path):
    spec.build_all(tmp_path)
    reader = pypdf.PdfReader(str(tmp_path / "pdfa-3b-with-attachment.pdf"))
    # Embedded files live in the document catalog.
    catalog = reader.trailer["/Root"]
    assert "/Names" in catalog or "/AF" in catalog
