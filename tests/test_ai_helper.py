from ai_helper import build_local_presentation, generate_ppt_content, normalize_presentation


def test_local_planner_creates_a_complete_editable_story():
    data = build_local_presentation("Remote onboarding", 4, "Help new teammates contribute sooner")

    assert data["title"] == "Remote Onboarding"
    assert len(data["slides"]) == 4
    assert [slide["slide_number"] for slide in data["slides"]] == [1, 2, 3, 4]
    assert all(len(slide["bullet_points"]) == 3 for slide in data["slides"])
    assert {slide["block"] for slide in data["slides"]} >= {"comparison", "timeline", "decision"}


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
    assert warning is None
    assert len(data["slides"]) == 3
