from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ai_helper import generate_ppt_content_run
from storyboard_studio.providers import (
    EXCLUDED_FIELDS,
    OpenAICompatibleProvider,
    ProviderInput,
    provider_catalog,
    provider_timeout,
)


def test_provider_catalog_discloses_capabilities_policy_and_supported_state():
    catalog = provider_catalog({})

    assert [item["id"] for item in catalog] == ["local", "gemini", "openai-compatible"]
    assert catalog[0]["configured"] is True
    assert catalog[1]["network_boundary"] == "external-provider"
    assert catalog[2]["network_boundary"] == "loopback-only"
    assert catalog[2]["status"] == "experimental"
    assert all(item["maintainer"] and item["conformance_suite"] for item in catalog)
    assert all(item["cost_disclosure"] and item["retention_disclosure"] for item in catalog)
    assert all(item["accepts_files"] is False and item["accepts_evidence"] is False for item in catalog)
    assert set(catalog[0]["excluded_fields"]) == set(EXCLUDED_FIELDS)


def test_provider_timeout_is_bounded_and_has_a_deterministic_default():
    assert provider_timeout({}) == 30
    assert provider_timeout({"PROVIDER_TIMEOUT_SECONDS": "invalid"}) == 30
    assert provider_timeout({"PROVIDER_TIMEOUT_SECONDS": "0"}) == 1
    assert provider_timeout({"PROVIDER_TIMEOUT_SECONDS": "999"}) == 120


def test_openai_compatible_rejects_non_loopback_or_credentialed_endpoints():
    with pytest.raises(ValueError, match="loopback"):
        OpenAICompatibleProvider("https://api.example.com/v1", "model")
    with pytest.raises(ValueError, match="credentials"):
        OpenAICompatibleProvider("http://user:secret@localhost:11434/v1", "model")


def test_openai_compatible_conformance():
    received: dict[str, object] = {}
    fixture = json.loads(
        Path("examples/providers/openai-compatible-response.json").read_text(encoding="utf-8")
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - stdlib callback name
            received["path"] = self.path
            length = int(self.headers["content-length"])
            received["body"] = json.loads(self.rfile.read(length))
            response = json.dumps(fixture).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        provider = OpenAICompatibleProvider(
            f"http://127.0.0.1:{server.server_port}/v1", "local-conformance-model"
        )
        result = provider.generate(
            ProviderInput(
                topic="Conformance",
                slide_count=3,
                brief="No private source material",
                slide_focuses=("Decision",),
            ),
            timeout_seconds=2,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result["title"] == "Loopback Conformance Fixture"
    assert len(result["slides"]) == 3
    assert received["path"] == "/v1/chat/completions"
    body = received["body"]
    assert body["model"] == "local-conformance-model"
    assert body["temperature"] == 0
    assert body["response_format"] == {"type": "json_object"}
    serialized = json.dumps(body)
    assert not any(field in serialized for field in EXCLUDED_FIELDS)


def test_unconfigured_provider_falls_back_without_a_network_attempt():
    run = generate_ppt_content_run(
        "Fallback contract",
        3,
        provider="openai-compatible",
        environment={},
    )

    assert run.source == "local"
    assert run.provider["selected"] == "openai-compatible"
    assert run.provider["used"] == "local"
    assert run.provider["network_status"] == "not-sent"
    assert run.provider["fallback_reason"]["code"] == "openai-compatible-not-configured"
    assert run.provider["used_model"] == "deterministic-v1"
