from generate.builders import size


def test_builds_four_size_fixtures(tmp_path):
    records = size.build_all(tmp_path)
    expected_ids = {"clean-1mb", "clean-10mb", "clean-25mb", "clean-50mb"}
    assert {r.id for r in records} == expected_ids


def test_each_size_fixture_is_at_least_target_minus_10pct(tmp_path):
    records = size.build_all(tmp_path)
    targets = {"clean-1mb": 1_000_000, "clean-10mb": 10_000_000,
               "clean-25mb": 25_000_000, "clean-50mb": 50_000_000}
    for r in records:
        target = targets[r.id]
        assert r.size_bytes >= target * 0.9, f"{r.id} ({r.size_bytes}) below target {target}"
        assert r.size_bytes <= target * 1.5, f"{r.id} ({r.size_bytes}) above 1.5x target {target}"
