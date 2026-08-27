import io
import zipfile

from fastapi.testclient import TestClient

from server import app


def test_health_and_static_assets_are_available():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["version"]
        assert health.json()["providers"][0]["id"] == "local"
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/server.py").status_code == 404
        contract = client.get("/api/v1/layout-contract")
        assert contract.status_code == 200
        assert contract.json()["schema_version"] == "2"


def test_provider_catalog_is_visible_before_generation():
    with TestClient(app) as client:
        response = client.get("/api/v1/providers")

    assert response.status_code == 200
    body = response.json()
    assert body["default"] == "local"
    assert body["files_or_evidence_transfer_supported"] is False
    assert [item["id"] for item in body["providers"]] == [
        "local",
        "gemini",
        "openai-compatible",
    ]


def test_content_validation_rejects_invalid_topic():
    with TestClient(app) as client:
        response = client.post("/api/content", json={"topic": "x", "slide_count": 3, "use_ai": False})

    assert response.status_code == 422


def test_local_content_can_be_exported_and_downloaded():
    with TestClient(app) as client:
        outline_response = client.post(
            "/api/content",
            json={"topic": "Better remote onboarding", "slide_count": 3, "use_ai": False},
        )
        assert outline_response.status_code == 200
        outline = outline_response.json()
        assert outline["source"] == "local"

        export_response = client.post("/api/presentations", json={"presentation": outline["presentation"]})
        assert export_response.status_code == 201
        download = client.get(export_response.json()["download_url"])

    assert download.status_code == 200
    assert download.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert download.content[:2] == b"PK"


def test_versioned_api_aliases_follow_the_same_contract():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/content",
            json={"topic": "Versioned brief", "slide_count": 3, "provider": "local"},
        )
    assert response.status_code == 200
    assert response.json()["source"] == "local"
    assert response.json()["provider"]["selected"] == "local"
    assert response.json()["provider"]["network_status"] == "offline"


def test_generation_rejects_implicit_file_evidence_or_asset_transfer():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/content",
            json={
                "topic": "Private material",
                "slide_count": 3,
                "provider": "gemini",
                "files": ["private.txt"],
                "evidence": [{"label": "secret"}],
                "assets": [{"path": "private.png"}],
            },
        )

    assert response.status_code == 422


def test_unconfigured_selected_provider_returns_visible_fallback_provenance(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/content",
            json={"topic": "Visible fallback", "slide_count": 3, "provider": "gemini"},
        )

    assert response.status_code == 200
    run = response.json()["provider"]
    assert run["selected"] == "gemini"
    assert run["used"] == "local"
    assert run["network_status"] == "not-sent"
    assert run["fallback_reason"]["code"] == "gemini-not-configured"


def test_doctor_api_returns_explainable_findings():
    with TestClient(app) as client:
        outline = client.post(
            "/api/v1/content",
            json={"topic": "Generic planning", "slide_count": 3, "use_ai": False},
        ).json()["presentation"]
        response = client.post("/api/v1/doctor", json=outline)

    assert response.status_code == 200
    report = response.json()
    assert report["schema_version"] == "1"
    assert report["status"] in {"ready", "needs-review"}
    assert all(
        {"code", "severity", "path", "message", "rationale", "action"} <= finding.keys()
        for finding in report["findings"]
    )


def test_layout_preflight_reports_recoverable_overflow():
    with TestClient(app) as client:
        outline = client.post(
            "/api/v1/content",
            json={"topic": "Layout preflight", "slide_count": 3, "use_ai": False},
        ).json()["presentation"]
        outline["slides"][0]["title"] = "This valid title is intentionally too long for the right layout now"
        response = client.post("/api/v1/layout/preflight", json=outline)

    assert response.status_code == 200
    assert response.json()["status"] == "needs-fix"
    assert response.json()["findings"][0]["actions"]


def test_guided_decision_story_is_local_versioned_and_diagnosable():
    request = {
        "brief": {
            "decision": "Choose the onboarding pilot",
            "audience": "Product and customer-success leaders",
            "desired_outcome": "Approve one measurable first-30-day experience",
            "current_context": "New customers receive inconsistent guidance after handoff.",
            "constraints": ["No new platform", "One product team", "Six-week pilot"],
            "options": [
                {"title": "Concierge", "description": "A human-led cohort."},
                {"title": "In-product", "description": "Guidance in the current product."},
            ],
            "trade_offs": ["Reach versus learning depth"],
            "evidence": [{"label": "Handoff review", "evidence": "Author synthesis", "owner": "CS lead"}],
            "owner": "Onboarding lead",
            "next_step": "Run a five-customer pilot",
            "review_date": "2026-09-30",
        },
        "theme": "forest",
    }
    with TestClient(app) as client:
        response = client.post("/api/v1/stories/decision-brief", json=request)
        assert response.status_code == 200
        result = response.json()
        diagnosis = client.post("/api/v1/stories/doctor", json=result["story"])

    assert result["source"] == "local"
    assert result["story"]["schema_version"] == "2"
    assert result["presentation"]["theme"] == "forest"
    assert diagnosis.status_code == 200
    assert diagnosis.json()["story_kind"] == "decision-brief"


def test_review_bundle_contains_pptx_story_and_receipt():
    request = {
        "brief": {
            "decision": "Choose the onboarding pilot",
            "audience": "Product and customer-success leaders",
            "desired_outcome": "Approve one measurable first-30-day experience",
            "current_context": "New customers receive inconsistent guidance after handoff.",
            "constraints": ["No new platform", "Six-week pilot"],
            "options": [
                {"title": "Concierge", "description": "A human-led cohort."},
                {"title": "In-product", "description": "Guidance in the current product."},
            ],
            "trade_offs": ["Reach versus learning depth"],
            "evidence": [],
            "owner": "Onboarding lead",
            "next_step": "Run a five-customer pilot",
            "review_date": "2026-09-30",
        }
    }
    with TestClient(app) as client:
        story = client.post("/api/v1/stories/decision-brief", json=request).json()["story"]
        response = client.post("/api/v1/bundles", json=story)
        assert response.status_code == 201
        download = client.get(response.json()["download_url"])

    assert download.status_code == 200
    with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
        assert set(archive.namelist()) == {
            "deck.pptx",
            "deck.receipt.json",
            "deck.story.json",
        }
        assert archive.read("deck.pptx")[:2] == b"PK"


def test_export_rejects_unexpected_fields_and_bad_ids():
    with TestClient(app) as client:
        response = client.post("/api/presentations", json={"unexpected": True})
        assert response.status_code == 422
        assert client.get("/api/presentations/not-a-real-id.pptx").status_code == 404
