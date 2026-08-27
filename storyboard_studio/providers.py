"""Isolated, capability-described content-provider adapters."""

from __future__ import annotations

import ipaddress
import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

ProviderId = Literal["local", "gemini", "openai-compatible"]
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT_SECONDS = 30
TRANSFERRED_FIELDS = ("topic", "brief", "slide_count", "slide_focuses")
EXCLUDED_FIELDS = ("assets", "evidence", "files", "sources", "speaker_notes")


@dataclass(frozen=True)
class ProviderCapabilities:
    id: ProviderId
    label: str
    status: Literal["supported", "experimental"]
    maintainer: str
    network_boundary: Literal["offline", "external-provider", "loopback-only"]
    structured_output: bool
    accepts_files: bool
    accepts_evidence: bool
    cost_disclosure: str
    retention_disclosure: str
    conformance_suite: str


@dataclass(frozen=True)
class ProviderInput:
    topic: str
    slide_count: int
    brief: str
    slide_focuses: tuple[str, ...]

    def prompt(self) -> str:
        return f"""Create an editable {self.slide_count}-slide presentation outline.
Topic: {self.topic}
Audience / purpose: {self.brief or "General audience; make the core idea clear."}
Requested slide focuses: {json.dumps(self.slide_focuses, ensure_ascii=False)}

Return JSON only with title, subtitle, and slides. Each slide needs title (max 8 words),
content (max 30 words), and exactly 3 bullet_points. A bullet point may be an object with
title and description, or a three-item array [label, title, description]. Do not invent
statistics, citations, or claims that cannot be supported. Keep wording concise and useful."""


class ContentProvider(Protocol):
    capabilities: ProviderCapabilities
    model: str

    def generate(self, request: ProviderInput, timeout_seconds: int) -> dict[str, object]: ...


LOCAL_CAPABILITIES = ProviderCapabilities(
    id="local",
    label="Deterministic local planner",
    status="supported",
    maintainer="Storyboard Studio maintainers",
    network_boundary="offline",
    structured_output=True,
    accepts_files=False,
    accepts_evidence=False,
    cost_disclosure="No provider charge; runs in the Storyboard Studio process.",
    retention_disclosure="No provider request and no provider-side retention.",
    conformance_suite="tests/test_providers.py",
)
GEMINI_CAPABILITIES = ProviderCapabilities(
    id="gemini",
    label="Google Gemini",
    status="supported",
    maintainer="Storyboard Studio maintainers",
    network_boundary="external-provider",
    structured_output=True,
    accepts_files=False,
    accepts_evidence=False,
    cost_disclosure=(
        "Your Google provider account and model pricing apply; Storyboard does not estimate cost."
    ),
    retention_disclosure=(
        "Google account and API data policies apply; Storyboard stores no provider response."
    ),
    conformance_suite="tests/test_providers.py",
)
OPENAI_COMPATIBLE_CAPABILITIES = ProviderCapabilities(
    id="openai-compatible",
    label="Local OpenAI-compatible endpoint",
    status="experimental",
    maintainer="Storyboard Studio maintainers",
    network_boundary="loopback-only",
    structured_output=True,
    accepts_files=False,
    accepts_evidence=False,
    cost_disclosure="No Storyboard charge; the local endpoint operator owns compute and model costs.",
    retention_disclosure="The local endpoint policy applies; Storyboard stores no provider response.",
    conformance_suite="tests/test_providers.py::test_openai_compatible_conformance",
)


def provider_timeout(environment: dict[str, str] | os._Environ[str] | None = None) -> int:
    env = environment if environment is not None else os.environ
    try:
        value = int(env.get("PROVIDER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return min(max(value, 1), 120)


def _loopback_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("The OpenAI-compatible base URL must use explicit http or https.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("The OpenAI-compatible base URL cannot contain credentials, query, or fragment.")
    hostname = parsed.hostname.rstrip(".").lower()
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if hostname != "localhost" and not (address and address.is_loopback):
        raise ValueError("The OpenAI-compatible adapter accepts loopback endpoints only.")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def _json_object(value: str) -> dict[str, object]:
    cleaned = value.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1)
    result = json.loads(cleaned)
    if not isinstance(result, dict):
        raise ValueError("Provider structured output must be one JSON object.")
    return result


class GeminiProvider:
    capabilities = GEMINI_CAPABILITIES

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def generate(self, request: ProviderInput, timeout_seconds: int) -> dict[str, object]:
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover - covered by clean-install validation
            raise RuntimeError("The Gemini adapter dependency is unavailable.") from exc
        client = genai.Client(
            api_key=self.api_key,
            http_options={"timeout": timeout_seconds * 1000},
        )
        response = client.models.generate_content(
            model=self.model,
            contents=request.prompt(),
            config={"response_mime_type": "application/json"},
        )
        return _json_object(response.text)


class OpenAICompatibleProvider:
    capabilities = OPENAI_COMPATIBLE_CAPABILITIES

    def __init__(self, base_url: str, model: str, api_key: str = ""):
        self.base_url = _loopback_base_url(base_url)
        self.model = model
        self.api_key = api_key

    def generate(self, request: ProviderInput, timeout_seconds: int) -> dict[str, object]:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": request.prompt()}],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        target = f"{self.base_url}/chat/completions"
        try:
            with urlopen(
                Request(target, data=body, headers=headers, method="POST"), timeout=timeout_seconds
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                "The local OpenAI-compatible endpoint did not return a valid response."
            ) from exc
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("The OpenAI-compatible response is missing choices[0].message.content.") from exc
        if isinstance(content, dict):
            return content
        if not isinstance(content, str):
            raise ValueError("The OpenAI-compatible response content must be JSON text or an object.")
        return _json_object(content)


def selected_provider(provider: ProviderId | None, use_ai: bool) -> ProviderId:
    if provider is not None:
        return provider
    return "gemini" if use_ai else "local"


def configured_provider(
    provider_id: ProviderId,
    environment: dict[str, str] | os._Environ[str] | None = None,
) -> ContentProvider | None:
    env = environment if environment is not None else os.environ
    if provider_id == "local":
        return None
    if provider_id == "gemini":
        api_key = env.get("GEMINI_API_KEY", "").strip()
        return GeminiProvider(api_key, env.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)) if api_key else None
    base_url = env.get("OPENAI_COMPATIBLE_BASE_URL", "").strip()
    model = env.get("OPENAI_COMPATIBLE_MODEL", "").strip()
    if not base_url or not model:
        return None
    return OpenAICompatibleProvider(base_url, model, env.get("OPENAI_COMPATIBLE_API_KEY", ""))


def provider_catalog(
    environment: dict[str, str] | os._Environ[str] | None = None,
) -> list[dict[str, object]]:
    env = environment if environment is not None else os.environ
    timeout = provider_timeout(env)
    rows = []
    for capabilities in (LOCAL_CAPABILITIES, GEMINI_CAPABILITIES, OPENAI_COMPATIBLE_CAPABILITIES):
        configuration_error = ""
        try:
            adapter = configured_provider(capabilities.id, env)
        except ValueError as exc:
            adapter = None
            configuration_error = str(exc)
        model = (
            "deterministic-v1"
            if capabilities.id == "local"
            else env.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
            if capabilities.id == "gemini"
            else env.get("OPENAI_COMPATIBLE_MODEL", "not-configured")
        )
        rows.append(
            {
                **asdict(capabilities),
                "configured": capabilities.id == "local" or adapter is not None,
                "configuration_error": configuration_error,
                "model": model,
                "timeout_seconds": timeout,
                "transferred_fields": list(TRANSFERRED_FIELDS),
                "excluded_fields": list(EXCLUDED_FIELDS),
            }
        )
    return rows


def catalog_entry(
    provider_id: ProviderId,
    environment: dict[str, str] | os._Environ[str] | None = None,
) -> dict[str, object]:
    return next(item for item in provider_catalog(environment) if item["id"] == provider_id)
