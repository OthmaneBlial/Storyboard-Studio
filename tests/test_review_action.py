import json
from pathlib import Path

import pytest

from scripts.review_story import review_story


def test_offline_review_action_builds_complete_artifact(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()
    source = repository / "review.story.json"
    source.write_text(
        Path("storyboard_studio/data/decision-brief.story.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    manifest = review_story(Path("review.story.json"), Path("artifact"), repository)

    assert manifest["network_provider_used"] is False
    assert manifest["factual_truth_verified"] is False
    expected = {
        "doctor.json",
        "doctor.md",
        "evidence.json",
        "review.pptx",
        "review.receipt.json",
        "review.story.json",
        "review-manifest.json",
    }
    assert {path.name for path in (repository / "artifact").iterdir()} == expected
    receipt = json.loads((repository / "artifact" / "review.receipt.json").read_text())
    assert receipt["viewer_status"] == "ci-structural-review-only"


def test_offline_review_action_rejects_paths_outside_checkout(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()

    with pytest.raises(ValueError, match="inside the checked-out repository"):
        review_story(Path("../private.story.json"), Path("artifact"), repository)


def test_reusable_workflow_declares_read_only_permissions_and_no_provider_secret():
    workflow = Path(".github/workflows/review-story.yml").read_text(encoding="utf-8")
    action = Path(".github/actions/review-story/action.yml").read_text(encoding="utf-8")

    assert "contents: read" in workflow
    assert "actions/upload-artifact" in workflow
    assert 'GEMINI_API_KEY: ""' in action
    assert "scripts/review_story.py" in action
