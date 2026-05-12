import json
from pathlib import Path
from generate.facets import FixtureRecord, Health, Access, DocumentShape, Provenance, PaperSize, Spec
from generate.catalog import emit_catalog, emit_llms_txt, emit_openapi


def _sample_record():
    return FixtureRecord(
        id="clean-letter-1page",
        size_bytes=1234,
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


def test_catalog_json_has_required_top_level(tmp_path):
    out = tmp_path / "catalog.json"
    emit_catalog([_sample_record()], out)
    data = json.loads(out.read_text())
    assert data["schema_version"] == "1.0.0"
    assert data["site"] == "pdfbin.net"
    assert data["license_default"] == "CC0-1.0"
    assert data["fixture_count"] == 1
    assert "health" in data["facet_axes"]
    assert data["fixtures"][0]["id"] == "clean-letter-1page"
    assert data["fixtures"][0]["facets"]["health"] == "valid"


def test_llms_txt_mentions_url_contract_and_categories(tmp_path):
    out = tmp_path / "llms.txt"
    emit_llms_txt([_sample_record()], out)
    text = out.read_text()
    assert "pdfbin.net" in text
    assert "immutable" in text.lower()
    assert "CC0" in text
    assert "/catalog.json" in text


def test_openapi_json_lists_fixture_paths(tmp_path):
    out = tmp_path / "openapi.json"
    emit_openapi([_sample_record()], out)
    data = json.loads(out.read_text())
    assert data["openapi"].startswith("3.")
    assert "/clean-letter-1page.pdf" in data["paths"]
    method = data["paths"]["/clean-letter-1page.pdf"]["get"]
    assert "application/pdf" in method["responses"]["200"]["content"]
