import json
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Inches

from ai_helper import build_local_presentation
from generate_pptx import THEMES, create_presentation
from storyboard_studio.layout import load_layout_contract


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


def test_renderer_uses_shared_geometry_and_local_brand_fonts(tmp_path: Path):
    data = build_local_presentation("Shared layout geometry", 3)
    data["brand_kit"] = json.loads(Path("themes/brand-kit.example.json").read_text(encoding="utf-8"))
    data["brand_kit"]["display_font_fallbacks"] = ["Arial", "sans-serif"]
    exported = Presentation(create_presentation(data, tmp_path / "branded.pptx"))
    contract = load_layout_contract()
    content_slide = exported.slides[1]
    title_shape = next(
        shape
        for shape in content_slide.shapes
        if shape.has_text_frame and shape.text == data["slides"][0]["title"]
    )

    assert title_shape.left == Inches(contract.layouts["right"].heading.x)
    assert title_shape.top == Inches(contract.layouts["right"].heading.y)
    assert title_shape.text_frame.paragraphs[0].runs[0].font.name == "Arial"
    assert str(content_slide.background.fill.fore_color.rgb) == "F7F9FC"


def test_edge_fixture_preserves_unicode_and_all_layouts(tmp_path: Path):
    fixture = json.loads(Path("examples/fixtures/edge-cases.json").read_text(encoding="utf-8"))
    destination = create_presentation(fixture, tmp_path / "edge-cases.pptx")
    exported = Presentation(destination)
    texts = "\n".join(
        shape.text for slide in exported.slides for shape in slide.shapes if shape.has_text_frame
    )

    assert len(exported.slides) == 4
    assert "Café déjà vu" in texts
    assert "Unicode text" in texts
    assert "Long copy is a rendering risk" in texts


def test_export_has_stable_editable_core_properties(tmp_path: Path):
    data = build_local_presentation("Core property test", 3)
    exported = Presentation(create_presentation(data, tmp_path / "properties.pptx"))

    assert exported.core_properties.author == "Storyboard Studio"
    assert exported.core_properties.title == "Core Property Test"
    assert all(
        shape.has_text_frame for slide in exported.slides for shape in slide.shapes if shape.has_text_frame
    )


def test_sources_and_speaker_notes_are_native_notes(tmp_path: Path):
    data = build_local_presentation("Evidence-aware brief", 3)
    data["slides"][0]["sources"] = [{"label": "Internal brief", "evidence": "Author notes", "owner": "Team"}]
    data["slides"][0]["speaker_notes"] = "Check this draft before sharing."
    exported = Presentation(create_presentation(data, tmp_path / "notes.pptx"))
    notes = exported.slides[1].notes_slide.notes_text_frame.text

    assert "Check this draft" in notes
    assert "Internal brief" in notes
    assert "author-supplied; not verified" in notes


def test_all_semantic_blocks_render_as_distinct_native_structures_in_dark_and_light(
    tmp_path: Path,
):
    fixture = json.loads(Path("examples/fixtures/semantic-blocks.json").read_text(encoding="utf-8"))
    expected_names = [
        "semantic.standard.point.1",
        "semantic.comparison.side.1",
        "semantic.decision.statement",
        "semantic.timeline.step.1",
        "semantic.metric.value",
        "semantic.process.step.1",
        "semantic.quote.evidence",
        "semantic.table",
    ]

    for theme in ("midnight", "glacier"):
        fixture["theme"] = theme
        exported = Presentation(create_presentation(fixture, tmp_path / f"semantic-blocks-{theme}.pptx"))
        assert len(exported.slides) == 9
        for slide, expected_name in zip(list(exported.slides)[1:], expected_names, strict=True):
            names = {shape.name for shape in slide.shapes}
            assert expected_name in names
            assert all(shape.left >= 0 and shape.top >= 0 for shape in slide.shapes)
            assert all(shape.left + shape.width <= exported.slide_width for shape in slide.shapes)
            assert all(shape.top + shape.height <= exported.slide_height for shape in slide.shapes)
        assert any(shape.has_table for shape in exported.slides[-1].shapes)


def test_renderer_keeps_complete_titles_notes_and_internal_whitespace(tmp_path: Path):
    data = build_local_presentation("Preserve authored copy", 3)
    # These fit the public title budgets but exceeded the old footer/caption slices.
    data["title"] = "Une décision complète " + "é" * 50
    data["slides"][0]["title"] = "Une décision détaillée " + "é" * 30
    data["slides"][0]["layout"] = "left"
    data["slides"][0]["content"] = "Première ligne\nDeuxième  ligne avec espacement"
    data["slides"][0]["speaker_notes"] = "Notes privées\n\nDeuxième paragraphe  conservé"
    exported = Presentation(create_presentation(data, tmp_path / "complete-copy.pptx"))
    content = exported.slides[1]
    texts = [shape.text for shape in content.shapes if shape.has_text_frame]
    assert data["title"] in texts
    assert texts.count(data["slides"][0]["title"]) == 1
    # PowerPoint encodes a line break within a run as a vertical tab on extraction.
    assert data["slides"][0]["content"] in [text.replace("\v", "\n") for text in texts]
    assert data["slides"][0]["speaker_notes"] in content.notes_slide.notes_text_frame.text


def test_legacy_semantic_blocks_keep_every_bullet_visible_in_native_output(tmp_path: Path):
    data = build_local_presentation("Legacy block preservation", 3)
    blocks = ["comparison", "metric", "quote"]
    expected = []
    for slide, block in zip(data["slides"], blocks, strict=True):
        slide["block"] = block
        for point in slide["bullet_points"]:
            point["description"] = f"{point['description']} — legacy detail"
            expected.append(point["description"])
    exported = Presentation(create_presentation(data, tmp_path / "legacy-blocks.pptx"))
    texts = "\n".join(
        shape.text for slide in exported.slides for shape in slide.shapes if shape.has_text_frame
    )

    assert all(detail in texts for detail in expected)


def test_legacy_timeline_projection_is_blocked_before_it_can_clip_combined_text(tmp_path: Path):
    data = build_local_presentation("Legacy timeline", 3)
    data["slides"][0]["block"] = "timeline"
    data["slides"][0]["bullet_points"][0]["description"] = "A" * 120
    from storyboard_studio.preflight import ExportPreflightError

    with pytest.raises(ExportPreflightError, match="legacy detail"):
        create_presentation(data, tmp_path / "legacy-timeline.pptx")
    assert not (tmp_path / "legacy-timeline.pptx").exists()
