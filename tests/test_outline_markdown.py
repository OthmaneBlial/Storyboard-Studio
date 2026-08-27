import json
from pathlib import Path

from outline_markdown import (
    markdown_to_presentation,
    markdown_to_story,
    presentation_to_markdown,
    story_to_markdown,
)
from schemas import StoryDocumentV2


def test_markdown_round_trip_is_deterministic():
    source = json.loads(Path("examples/templates/decision-brief.json").read_text(encoding="utf-8"))
    markdown = presentation_to_markdown(source)
    result = markdown_to_presentation(markdown)

    assert result["title"] == source["title"]
    assert len(result["slides"]) == 3
    assert result["slides"][1]["block"] == "comparison"


def test_complete_story_markdown_round_trip_preserves_review_metadata():
    source = json.loads(Path("storyboard_studio/data/decision-brief.story.json").read_text(encoding="utf-8"))
    markdown = story_to_markdown(source)
    result, migrated = markdown_to_story(markdown)

    assert migrated is False
    expected = StoryDocumentV2.model_validate(source).model_dump(mode="json")
    assert StoryDocumentV2.model_validate(result).model_dump(mode="json") == expected


def test_unsupported_markdown_construct_reports_the_exact_line():
    markdown = "# Review\n\n## Unsupported heading\n"

    try:
        markdown_to_presentation(markdown)
    except ValueError as exc:
        assert "line 3" in str(exc)
        assert "expected a slide heading" in str(exc)
    else:  # pragma: no cover - keeps the failure useful if parser behavior regresses
        raise AssertionError("Unsupported Markdown unexpectedly parsed")
