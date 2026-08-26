import json
from pathlib import Path

from outline_markdown import markdown_to_presentation, presentation_to_markdown


def test_markdown_round_trip_is_deterministic():
    source = json.loads(Path("examples/templates/decision-brief.json").read_text(encoding="utf-8"))
    markdown = presentation_to_markdown(source)
    result = markdown_to_presentation(markdown)

    assert result["title"] == source["title"]
    assert len(result["slides"]) == 3
    assert result["slides"][1]["block"] == "comparison"
