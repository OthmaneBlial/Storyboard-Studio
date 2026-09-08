from datetime import date

from ai_helper import build_local_presentation
from schemas import DecisionBriefV2, PresentationPayload
from storyboard_studio.semantic import block_plain_text, normalize_content_block
from storyboard_studio.story import build_decision_story, migrate_presentation_v1


def decision_brief(**overrides):
    values = {
        "decision": "Choose the onboarding pilot for the next release",
        "audience": "Product and customer-success leaders",
        "desired_outcome": "Approve one measurable first-30-day experience",
        "current_context": "New customers receive inconsistent guidance after handoff.",
        "constraints": ["No new platform", "One product team", "Six-week pilot"],
        "options": [
            {"title": "Concierge pilot", "description": "A human-led cohort with a shared checklist."},
            {"title": "In-product pilot", "description": "A guided workflow inside the current product."},
        ],
        "trade_offs": ["Reach versus learning depth", "Speed versus automation"],
        "evidence": [
            {
                "label": "Support handoff review",
                "evidence": "Author-owned synthesis from recent handoffs.",
                "owner": "Customer success",
            }
        ],
        "owner": "Onboarding lead",
        "next_step": "Run a five-customer concierge pilot",
        "review_date": date(2026, 9, 30),
    }
    values.update(overrides)
    return DecisionBriefV2.model_validate(values)


def presentation_text(story) -> str:
    parts = [story.presentation.title, story.presentation.subtitle]
    for slide in story.presentation.slides:
        parts.extend([slide.title, slide.content])
        parts.append(block_plain_text(normalize_content_block(slide.model_dump(mode="json"))))
    return " ".join(parts)


def test_decision_brief_uses_author_fields_without_topic_agnostic_filler():
    onboarding = build_decision_story(decision_brief())
    incident = build_decision_story(
        decision_brief(
            decision="Choose the database recovery sequence",
            audience="Incident commander and storage owners",
            desired_outcome="Approve the safest restoration order",
            current_context="Replica lag increased after a failed regional switchover.",
            constraints=["Preserve audit logs", "Keep writes paused", "Verify every restore point"],
            options=[
                {"title": "Restore primary", "description": "Recover the last verified primary snapshot."},
                {"title": "Promote replica", "description": "Promote the least-lagging verified replica."},
            ],
            trade_offs=["Recovery time versus data confidence"],
            owner="Incident commander",
            next_step="Approve one restore point and record the decision",
        )
    )

    onboarding_text = presentation_text(onboarding)
    incident_text = presentation_text(incident)
    assert "onboarding pilot" in onboarding_text.lower()
    assert "database recovery" in incident_text.lower()
    assert "replica lag" in incident_text.lower()
    assert onboarding_text != incident_text
    assert [slide.block for slide in onboarding.presentation.slides] == [
        "standard",
        "standard",
        "comparison",
        "decision",
        "timeline",
    ]


def test_v1_migration_keeps_freeform_boundary_explicit():
    presentation = PresentationPayload.model_validate(
        build_local_presentation("Legacy outline", 3, "Leaders reviewing an old outline")
    )
    story = migrate_presentation_v1(presentation)

    assert story.kind == "freeform-outline"
    assert story.decision_brief is None
    assert "were not inferred" in story.provider_warning


def test_third_choice_is_preserved_and_comparison_scope_is_explicit():
    brief = decision_brief()
    values = brief.model_dump()
    values["options"].append({"title": "Keep current flow", "description": "Observe the existing process."})
    story = build_decision_story(DecisionBriefV2.model_validate(values))
    assert "all three options" in story.presentation.slides[2].content
    assert "Keep current flow" in presentation_text(story)
    assert len(story.decision_brief.options) == 3
    assert story.presentation.slides[1].content == brief.desired_outcome


def test_long_author_text_survives_compilation_and_portable_save(tmp_path):
    import pytest

    from generate_pptx import create_presentation
    from storyboard_studio.layout import analyze_overflow, load_layout_contract
    from storyboard_studio.preflight import ExportPreflightError
    from storyboard_studio.projects import ProjectPayload, read_project, write_project

    brief = decision_brief(
        decision="Décision complète " + "é" * 180,
        current_context="Contexte\n" + "c" * 500,
        next_step="Étape " + "n" * 200,
        constraints=["Contrainte " + "x" * 500],
        trade_offs=["Compromis " + "t" * 500],
    )
    story = build_decision_story(brief)
    assert story.presentation.title == brief.decision
    assert story.presentation.slides[0].content == brief.current_context
    assert story.presentation.slides[1].content_block.points[0].description == brief.constraints[0]
    assert story.presentation.slides[3].content_block.rationale == brief.trade_offs[0]
    assert story.presentation.slides[4].content_block.steps[0].title == brief.next_step
    report = analyze_overflow(story.presentation.model_dump(), load_layout_contract())
    paths = {finding["path"] for finding in report["findings"]}
    assert "title" in paths
    assert "slides.4.content_block.steps.0.title" in paths
    destination = tmp_path / "complete.zip"
    write_project(ProjectPayload(story=story), destination)
    reopened = read_project(destination)
    assert reopened.story == story
    output = tmp_path / "oversized.pptx"
    with pytest.raises(ExportPreflightError):
        create_presentation(reopened.story.presentation.model_dump(), output)
    assert not output.exists()


def test_storage_limit_rejects_text_instead_of_shortening_it():
    import pytest
    from pydantic import ValidationError

    story = build_decision_story(decision_brief()).presentation.model_dump()
    story["title"] = "é" * 2000
    assert PresentationPayload.model_validate(story).title == story["title"]
    story["title"] += "é"
    with pytest.raises(ValidationError):
        PresentationPayload.model_validate(story)
