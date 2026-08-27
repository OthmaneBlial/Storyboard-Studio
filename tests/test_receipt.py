import json
from pathlib import Path

from pptx import Presentation

from storyboard_studio.cli import main
from storyboard_studio.receipt import diff_stories, verify_receipt
from storyboard_studio.story import read_story_or_presentation


def test_bundle_receipt_verifies_and_detects_tampering(tmp_path: Path):
    output = tmp_path / "deck.pptx"
    assert (
        main(
            [
                "export",
                "--input",
                "examples/product-brief.json",
                "--output",
                str(output),
                "--bundle",
            ]
        )
        == 0
    )
    story_path = tmp_path / "deck.story.json"
    receipt_path = tmp_path / "deck.receipt.json"
    assert output.is_file()
    assert story_path.is_file()
    assert receipt_path.is_file()
    assert verify_receipt(receipt_path)["status"] == "verified"
    assert "outline sha256" in Presentation(output).core_properties.comments

    story_path.write_text("{}\n", encoding="utf-8")
    result = verify_receipt(receipt_path)
    assert result["status"] == "invalid"
    assert any("digest mismatch" in error for error in result["errors"])


def test_diff_requires_and_reports_versioned_story_changes(tmp_path: Path):
    first = tmp_path / "first.story.json"
    second = tmp_path / "second.story.json"
    assert main(["migrate", "examples/product-brief.json", "--output", str(first)]) == 0
    story = json.loads(first.read_text(encoding="utf-8"))
    story["presentation"]["title"] = "A changed review title"
    second.write_text(json.dumps(story), encoding="utf-8")

    old, _ = read_story_or_presentation(first)
    new, _ = read_story_or_presentation(second)
    report = diff_stories(old, new)

    assert report["changed"] is True
    assert any(change["path"] == "presentation.title" for change in report["changes"])
