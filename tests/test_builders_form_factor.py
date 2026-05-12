from pathlib import Path
import pypdf
from generate.builders import form_factor
from generate.facets import PaperSize


def test_builds_nine_clean_form_factor_fixtures(tmp_path):
    records = form_factor.build_all(tmp_path)
    ids = {r.id for r in records}
    expected = {
        "clean-a4-1page",
        "clean-letter-1page",
        "clean-jis-b5-1page",
        "clean-a4-3page",
        "clean-letter-3page",
        "clean-100-pages",
        "clean-500-pages",
        "clean-mixed-orientation",
        "clean-paper-sizes-mixed",
    }
    assert ids == expected
    for r in records:
        path = tmp_path / f"{r.id}.pdf"
        assert path.exists()
        reader = pypdf.PdfReader(str(path))
        assert len(reader.pages) == r.page_count


def test_jis_b5_dimensions(tmp_path):
    records = form_factor.build_all(tmp_path)
    jis = next(r for r in records if r.id == "clean-jis-b5-1page")
    assert jis.paper_size == PaperSize.JIS_B5
    reader = pypdf.PdfReader(str(tmp_path / "clean-jis-b5-1page.pdf"))
    box = reader.pages[0].mediabox
    # JIS B5 is 182x257mm = 515.91 x 728.5 pts. Tolerance for rounding.
    assert abs(float(box.width) - 515.91) < 2
    assert abs(float(box.height) - 728.5) < 2
