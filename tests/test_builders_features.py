import pypdf
from generate.builders import features


def test_builds_three_features_fixtures(tmp_path):
    # acroform-signed deferred to v1.1 (requires pyhanko + cryptography
    # for real digital signing - see docstring in generate/builders/features.py).
    records = features.build_all(tmp_path)
    expected = {"acroform-empty", "acroform-partially-filled",
                "acroform-fully-filled"}
    assert {r.id for r in records} == expected


def test_acroform_empty_has_form_fields(tmp_path):
    features.build_all(tmp_path)
    reader = pypdf.PdfReader(str(tmp_path / "acroform-empty.pdf"))
    fields = reader.get_fields() or {}
    assert len(fields) >= 1


def test_acroform_partially_filled_has_one_value(tmp_path):
    features.build_all(tmp_path)
    reader = pypdf.PdfReader(str(tmp_path / "acroform-partially-filled.pdf"))
    fields = reader.get_fields() or {}
    filled = [k for k, v in fields.items() if v.get("/V")]
    assert len(filled) == 1
