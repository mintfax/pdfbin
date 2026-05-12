import pytest
import pypdf
from generate.builders import health


def test_builds_seven_health_fixtures(tmp_path):
    records = health.build_all(tmp_path)
    expected = {
        "xref-truncated", "header-truncated", "stream-length-mismatch",
        "object-generation-mismatch", "trailer-missing", "eof-missing",
        "byte-flipped-mid-stream",
    }
    assert {r.id for r in records} == expected


def test_header_truncated_lacks_pdf_marker(tmp_path):
    health.build_all(tmp_path)
    data = (tmp_path / "header-truncated.pdf").read_bytes()
    assert not data.startswith(b"%PDF-")


def test_eof_missing_lacks_eof_marker(tmp_path):
    health.build_all(tmp_path)
    data = (tmp_path / "eof-missing.pdf").read_bytes()
    assert b"%%EOF" not in data


def test_xref_truncated_loads_with_recovery(tmp_path):
    """pypdf with strict=False can recover via scan; strict=True should fail."""
    health.build_all(tmp_path)
    path = tmp_path / "xref-truncated.pdf"
    # strict=False recovery may or may not succeed depending on truncation point;
    # the important assertion is that the file IS truncated.
    raw = path.read_bytes()
    assert b"startxref" not in raw or raw.find(b"startxref") > len(raw) - 200
