from fastapi.testclient import TestClient

from server import app


def test_health_and_static_assets_are_available():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert health.json()["version"]
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/server.py").status_code == 404


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
            json={"topic": "Versioned brief", "slide_count": 3, "use_ai": False},
        )
    assert response.status_code == 200
    assert response.json()["source"] == "local"


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
        {"code", "severity", "path", "message", "action"} <= finding.keys() for finding in report["findings"]
    )


def test_export_rejects_unexpected_fields_and_bad_ids():
    with TestClient(app) as client:
        response = client.post("/api/presentations", json={"unexpected": True})
        assert response.status_code == 422
        assert client.get("/api/presentations/not-a-real-id.pptx").status_code == 404
