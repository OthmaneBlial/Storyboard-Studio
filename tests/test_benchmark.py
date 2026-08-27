import json

import pytest

from storyboard_studio.benchmark import compare_reports, load_benchmark_suite, run_benchmark


def test_public_suite_has_ten_strict_synthetic_cases():
    suite = load_benchmark_suite("benchmarks/decision-v1/suite.json")

    assert suite.synthetic_only is True
    assert suite.license == "CC0-1.0"
    assert len(suite.cases) == 10
    assert len({case.id for case in suite.cases}) == 10
    assert all(case.copy_density_risks is not None for case in suite.cases)


def test_suite_loader_rejects_duplicate_json_keys(tmp_path):
    source = tmp_path / "duplicate.json"
    source.write_text('{"schema_version":"1","schema_version":"1"}', encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_benchmark_suite(source)


def test_benchmark_writes_two_inspectable_lanes_without_network(tmp_path):
    complete = load_benchmark_suite("benchmarks/decision-v1/suite.json")
    one_case = complete.model_copy(update={"cases": complete.cases[:1]})
    suite_path = tmp_path / "suite.json"
    suite_path.write_text(one_case.model_dump_json(indent=2), encoding="utf-8")

    report = run_benchmark(suite_path, tmp_path / "results", release="test")

    assert report["summary"]["runs"] == 2
    assert {result["mode"] for result in report["results"]} == {
        "local",
        "optional-provider",
    }
    optional = next(result for result in report["results"] if result["mode"] == "optional-provider")
    assert optional["provider"]["network_status"] == "not-sent"
    assert optional["provider"]["used"] == "local"
    assert optional["score"] <= 100
    assert (tmp_path / "results/cases/onboarding-pilot/local/deck.pptx").read_bytes()[:2] == b"PK"
    manifest = json.loads((tmp_path / "results/manifest.json").read_text(encoding="utf-8"))
    assert "cases/onboarding-pilot/local/deck.pptx" in manifest["sha256"]


def test_regression_comparison_skips_changed_provider_and_flags_lower_scores():
    baseline = {
        "release": "v0.2.0",
        "results": [
            {
                "case_id": "first",
                "mode": "local",
                "score": 90,
                "provider": {"used": "local", "used_model": "deterministic-v1"},
            },
            {
                "case_id": "second",
                "mode": "optional-provider",
                "score": 60,
                "provider": {"used": "local", "used_model": "deterministic-v1"},
            },
        ],
    }
    current = {
        "results": [
            {
                "case_id": "first",
                "mode": "local",
                "score": 89,
                "provider": {"used": "local", "used_model": "deterministic-v1"},
            },
            {
                "case_id": "second",
                "mode": "optional-provider",
                "score": 95,
                "provider": {"used": "openai-compatible", "used_model": "fixture-model"},
            },
        ]
    }

    comparison = compare_reports(current, baseline)

    assert comparison["status"] == "regressed"
    assert comparison["regressions"] == [
        {"case_id": "first", "mode": "local", "status": "compared", "delta": -1.0}
    ]
    assert comparison["comparisons"][1]["status"] == "provider-not-comparable"


def test_overwrite_refuses_unrelated_files(tmp_path):
    output = tmp_path / "not-a-benchmark-directory"
    output.mkdir()
    protected = output / "keep-me.txt"
    protected.write_text("user data", encoding="utf-8")

    with pytest.raises(ValueError, match="Refusing to overwrite unrelated files"):
        run_benchmark(
            "benchmarks/decision-v1/suite.json",
            output,
            release="test",
            overwrite=True,
        )

    assert protected.read_text(encoding="utf-8") == "user data"
