import json
from pathlib import Path

import pytest

from storyboard_studio.cli import main
from storyboard_studio.research import aggregate_research_sessions, load_research_session


def _session(
    session_id: str = "S01",
    *,
    audience_band: str = "product-ops",
    workflow: str = "golden-synthetic",
    first_story: int = 60,
    export_seconds: int = 180,
    friction_codes: list[str] | None = None,
    quote: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1",
        "session_id": session_id,
        "consent": "yes",
        "consent_date": "2026-08-27",
        "audience_band": audience_band,
        "workflow": workflow,
        "setup": {"outcome": "completed", "seconds": first_story},
        "first_editable_story_seconds": first_story,
        "export": {"outcome": "completed", "total_seconds": export_seconds, "viewer": "not-run"},
        "friction_codes": friction_codes or [],
        "doctor": {"useful_codes": [], "false_positive_codes": []},
        "evidence_friction": "none",
        "interventions": 0,
        "outcome": "Completed a useful local export.",
        "quote": quote or {"permission": "no", "text": ""},
    }


def test_research_validate_command_writes_a_privacy_safe_report(tmp_path: Path):
    source = tmp_path / "S01.json"
    source.write_text(json.dumps(_session()), encoding="utf-8")
    report = tmp_path / "validation.json"

    assert main(["research", "validate", str(source), "--output", str(report)]) == 0

    value = json.loads(report.read_text(encoding="utf-8"))
    assert value["status"] == "valid"
    assert value["network"] == "none"
    assert value["session"]["session_id"] == "S01"


def test_research_aggregate_suppresses_small_segments_and_defers_decisions(tmp_path: Path):
    input_dir = tmp_path / "sessions"
    input_dir.mkdir()
    for index, seconds in enumerate((30, 60, 90), start=1):
        record = _session(
            f"S{index:02d}",
            first_story=seconds,
            export_seconds=seconds * 3,
            friction_codes=["preview-confusion"] if index == 1 else [],
        )
        (input_dir / f"S{index:02d}.json").write_text(json.dumps(record), encoding="utf-8")
    (input_dir / "S01.validation.json").write_text('{"status":"valid"}', encoding="utf-8")

    output_dir = tmp_path / "aggregate"
    report = aggregate_research_sessions(input_dir, output_dir)

    assert report["summary"] == {
        "sessions": 3,
        "real_private_workflows": 0,
        "median_first_editable_story_seconds": 60,
        "median_export_seconds": 180,
        "completion": {"setup_completed": 3, "export_completed": 3},
    }
    assert report["audience_mix"] == {"product-ops": 3}
    assert set(report["suppressed_audience_bands"]) == {
        "consulting-enablement",
        "developer-automation",
    }
    assert report["second_template_decision"].startswith("deferred")
    assert "preview-confusion" in report["friction_codes"]
    assert (output_dir / "aggregate.json").is_file()
    assert (output_dir / "aggregate.md").is_file()


def test_research_aggregate_keeps_permissioned_quotes_only(tmp_path: Path):
    input_dir = tmp_path / "sessions"
    input_dir.mkdir()
    first = _session("S01", quote={"permission": "yes", "text": "The story made the trade-off clear."})
    second = _session("S02")
    (input_dir / "S01.json").write_text(json.dumps(first), encoding="utf-8")
    (input_dir / "S02.json").write_text(json.dumps(second), encoding="utf-8")

    report = aggregate_research_sessions(input_dir, tmp_path / "aggregate")

    assert report["permissioned_quotes"] == ["The story made the trade-off clear."]


def test_research_rejects_duplicate_ids_and_private_tokens(tmp_path: Path):
    duplicate_dir = tmp_path / "duplicates"
    duplicate_dir.mkdir()
    for name in ("a.json", "b.json"):
        (duplicate_dir / name).write_text(json.dumps(_session("S01")), encoding="utf-8")
    with pytest.raises(ValueError, match="session_id values must be unique"):
        aggregate_research_sessions(duplicate_dir, tmp_path / "out")

    unsafe = tmp_path / "unsafe.json"
    unsafe_record = _session()
    unsafe_record["outcome"] = "ghp_123456789012345678901234567890"
    unsafe.write_text(json.dumps(unsafe_record), encoding="utf-8")
    with pytest.raises(ValueError, match="privacy validation"):
        load_research_session(unsafe)


def test_research_rejects_unpermissioned_quote_and_duplicate_json_keys(tmp_path: Path):
    invalid = tmp_path / "invalid.json"
    record = _session(quote={"permission": "no", "text": "Do not publish"})
    invalid.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="quote must be empty"):
        load_research_session(invalid)

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"session_id":"S01","session_id":"S02"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate JSON key"):
        load_research_session(duplicate)
