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
