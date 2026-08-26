from pathlib import Path

from pptx import Presentation

from ai_helper import build_local_presentation
from generate_pptx import THEMES, create_presentation


def test_renderer_creates_an_editable_title_and_content_slides(tmp_path: Path):
    data = build_local_presentation("A reliable onboarding experience", 3)
    data["theme"] = "forest"
    destination = create_presentation(data, tmp_path / "deck.pptx")

    assert destination.is_file()
    exported = Presentation(destination)
    assert len(exported.slides) == 4
    assert exported.slide_width > exported.slide_height
    assert any(
        "Reliable Onboarding" in shape.text for shape in exported.slides[0].shapes if shape.has_text_frame
    )


def test_all_public_themes_can_render(tmp_path: Path):
    for theme in THEMES:
        data = build_local_presentation("Theme test", 3)
        data["theme"] = theme
        assert create_presentation(data, tmp_path / f"{theme}.pptx").is_file()
