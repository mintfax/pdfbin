from generate.builders import provenance


def test_builds_five_provenance_fixtures(tmp_path):
    records = provenance.build_all(tmp_path)
    expected = {
        "scanned-clean-300dpi", "scanned-clean-200dpi",
        "scanned-noisy-300dpi", "scanned-skewed-3deg",
        "scanned-skewed-noisy",
    }
    assert {r.id for r in records} == expected


def test_provenance_records_carry_scan_quality(tmp_path):
    records = provenance.build_all(tmp_path)
    record_300 = next(r for r in records if r.id == "scanned-clean-300dpi")
    assert record_300.scan_quality == {"dpi": 300, "noise": None, "skew_degrees": 0}
