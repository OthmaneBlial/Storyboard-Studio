from ai_helper import (
    build_local_presentation,
    generate_ppt_content,
    generate_ppt_content_run,
    normalize_presentation,
)


def test_local_planner_creates_a_complete_editable_story():
    data = build_local_presentation("Remote onboarding", 4, "Help new teammates contribute sooner")

    assert data["title"] == "Remote Onboarding"
    assert len(data["slides"]) == 4
    assert [slide["slide_number"] for slide in data["slides"]] == [1, 2, 3, 4]
    assert all(len(slide["bullet_points"]) == 3 for slide in data["slides"])
    assert {slide["block"] for slide in data["slides"]} >= {"comparison", "timeline", "decision"}


def test_local_planner_varies_story_copy_by_topic_and_brief():
    recovery = build_local_presentation(
        "Database recovery sequence",
        3,
        "Incident commanders choosing a safe restoration order",
    )
    onboarding = build_local_presentation(
        "Remote onboarding experience",
        3,
        "People operations leads improving a new-hire welcome",
    )

    assert [slide["title"] for slide in recovery["slides"]] != [
        slide["title"] for slide in onboarding["slides"]
    ]
    assert "database recovery" in recovery["slides"][0]["content"].lower()
    assert "incident commanders" in recovery["slides"][0]["content"].lower()
    assert "remote onboarding" in onboarding["slides"][0]["content"].lower()


def test_model_normalization_repairs_malformed_output():
    raw = {"title": "A" * 200, "slides": [{"title": "Only one", "bullet_points": [["x", "One", "Two"]]}]}

    data = normalize_presentation(raw, "A topic", 3)

    assert len(data["title"]) == 90
    assert len(data["slides"]) == 3
    assert all(len(slide["bullet_points"]) == 3 for slide in data["slides"])


def test_no_key_uses_local_planner(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    data, source, warning = generate_ppt_content("Responsible automation", 3, use_ai=True)

    assert source == "local"
    assert warning is not None
    assert "not configured" in warning
    assert len(data["slides"]) == 3


def test_explicit_local_provider_is_offline_even_when_ai_flag_is_true():
    run = generate_ppt_content_run("Responsible automation", 3, use_ai=True, provider="local")

    assert run.source == "local"
    assert run.warning is None
    assert run.provider["selected"] == "local"
    assert run.provider["network_status"] == "offline"
    assert run.provider["fallback_reason"] is None


def test_local_planner_preserves_new_semantic_block_requests():
    data = build_local_presentation(
        "Semantic authoring",
        3,
        slide_configs=[
            {"block": "process"},
            {"block": "quote"},
            {"block": "table"},
        ],
    )

    assert [slide["block"] for slide in data["slides"]] == ["process", "quote", "table"]
