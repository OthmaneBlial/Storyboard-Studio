from ai_helper import build_local_presentation
from storyboard_studio.doctor import diagnose_presentation, diagnosis_to_markdown


def test_doctor_finds_missing_decision_and_action():
    outline = build_local_presentation("Quarterly context", 3, "A general update")
    outline["slides"][-1]["title"] = "Background"
    outline["slides"][-1]["content"] = "Additional context for the audience."
    for point in outline["slides"][-1]["bullet_points"]:
        point["title"] = "Context"
        point["description"] = "More background information."

    report = diagnose_presentation(outline)
    codes = {finding["code"] for finding in report["findings"]}

    assert report["status"] == "needs-review"
    assert "decision.missing" in codes
    assert "action.missing" in codes
    assert all(finding["rationale"] for finding in report["findings"])


def test_doctor_flags_numeric_claim_without_source():
    outline = build_local_presentation("Improve conversion", 3, "Product leaders deciding an experiment")
    outline["slides"][0]["content"] = "Activation increased by 32% in the latest cohort."

    report = diagnose_presentation(outline)

    assert any(finding["code"] == "evidence.numeric-claim" for finding in report["findings"])
    assert "does not verify factual truth" in diagnosis_to_markdown(report)


def test_doctor_is_deterministic():
    outline = build_local_presentation("Choose an onboarding direction", 3, "Leaders choose one option")

    assert diagnose_presentation(outline) == diagnose_presentation(outline)


def test_doctor_explains_repetitive_story_roles():
    outline = build_local_presentation("Choose an onboarding direction", 3, "Leaders choose one option")
    for slide in outline["slides"]:
        slide["block"] = "standard"

    report = diagnose_presentation(outline)

    assert any(finding["code"] == "story.progression-weak" for finding in report["findings"])
