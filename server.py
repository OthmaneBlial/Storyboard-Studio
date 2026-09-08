"""Local-first FastAPI service for Storyboard Studio."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import time
import zipfile
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ai_helper import generate_ppt_content_run
from generate_pptx import create_presentation
from schemas import (
    ExportPresentationRequest,
    GenerateContentRequest,
    GuidedDecisionRequest,
    PresentationPayload,
    StoryDocumentV2,
)
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_presentation, diagnose_story
from storyboard_studio.evidence import evidence_coverage
from storyboard_studio.export_store import ExportStore, default_export_root
from storyboard_studio.http_limits import LocalRequestLimits
from storyboard_studio.layout import analyze_overflow, load_layout_contract
from storyboard_studio.projects import ProjectPayload, materialize_project, read_project, write_project
from storyboard_studio.providers import provider_catalog
from storyboard_studio.receipt import create_receipt, digest_value
from storyboard_studio.resources import web_root
from storyboard_studio.story import build_decision_story

ROOT = Path(__file__).resolve().parent
WEB_DIR = web_root()
STATIC_DIR = WEB_DIR / "static"
OUTPUT_DIR = Path(os.getenv("STORYBOARD_OUTPUT_DIR", str(default_export_root()))).expanduser()
MAX_REQUEST_BYTES = 200_000
EXPORT_TTL_SECONDS = 24 * 60 * 60
RATE_LIMIT = 20
RATE_WINDOW_SECONDS = 60
logger = logging.getLogger("storyboard")
_requests: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = asyncio.Lock()


def _export_store() -> ExportStore:
    return ExportStore(OUTPUT_DIR, EXPORT_TTL_SECONDS)


def _cleanup_exports() -> None:
    """Sweep only marked server-owned exports, never the CLI output directory."""
    _export_store().cleanup()


async def _periodic_cleanup() -> None:
    while True:
        await asyncio.sleep(300)
        await run_in_threadpool(_cleanup_exports)


async def _is_rate_limited(client_id: str) -> bool:
    now = time.monotonic()
    async with _rate_lock:
        for key in list(_requests):
            if not _requests[key] or _requests[key][-1] <= now - RATE_WINDOW_SECONDS:
                del _requests[key]
        if client_id not in _requests and len(_requests) >= 1024:
            return True
        bucket = _requests[client_id]
        while bucket and bucket[0] <= now - RATE_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return True
        bucket.append(now)
        return False


@asynccontextmanager
async def lifespan(_: FastAPI):
    _cleanup_exports()
    cleanup_task = asyncio.create_task(_periodic_cleanup())
    logger.info("Storyboard Studio is ready. Gemini configured: %s", bool(os.getenv("GEMINI_API_KEY")))
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(
    title="Storyboard Studio API",
    version="1.1.0",
    description="A local-first, editable PowerPoint presentation generator.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.add_middleware(
    LocalRequestLimits,
    path_limits={
        f"/api/v1/projects/{action}": 8_000_000 for action in ("validate", "save", "export", "bundle", "open")
    },
    max_bytes=MAX_REQUEST_BYTES,
    allowed_hosts=tuple(
        host.strip() for host in os.getenv("STORYBOARD_ALLOWED_HOSTS", "").split(",") if host.strip()
    ),
)


@app.middleware("http")
async def security_and_limits(request: Request, call_next):
    if (
        request.method == "POST"
        and request.url.path.startswith("/api/")
        and request.url.path not in {"/api/v1/layout/preflight", "/api/v1/evidence/coverage"}
    ):
        client_id = request.client.host if request.client else "local"
        if await _is_rate_limited(client_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Wait a minute, then try again."},
                headers={"Retry-After": str(RATE_WINDOW_SECONDS)},
            )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; "
        "script-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'"
    )
    return response


@app.get("/", include_in_schema=False)
async def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html", media_type="text/html")


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, object]:
    layout = load_layout_contract()
    return {
        "status": "ok",
        "version": __version__,
        "ai_configured": bool(os.getenv("GEMINI_API_KEY")),
        "providers": provider_catalog(),
        "export_ttl_hours": 24,
        "layout_schema": layout.schema_version,
    }


@app.get("/api/v1/providers", tags=["generation"])
async def providers() -> dict[str, object]:
    """Describe provider capabilities and configuration before any request is sent."""
    return {
        "default": "local",
        "providers": provider_catalog(),
        "files_or_evidence_transfer_supported": False,
    }


@app.get("/api/v1/layout-contract", tags=["system"])
async def layout_contract() -> dict[str, object]:
    """Expose the validated local tokens used by both preview and export."""
    return load_layout_contract().model_dump(mode="json")


@app.post("/api/v1/layout/preflight", tags=["review"])
async def layout_preflight(presentation: PresentationPayload) -> dict[str, object]:
    """Find deterministic text overflow risks before creating a PowerPoint."""
    return analyze_overflow(presentation.model_dump(mode="json"), load_layout_contract())


@app.post("/api/v1/evidence/coverage", tags=["review"])
async def evidence_coverage_report(presentation: PresentationPayload) -> dict[str, object]:
    """Map claims to explicit author-linked and author-checked sources."""
    return evidence_coverage(presentation)


@app.post("/api/v1/doctor", tags=["review"])
async def doctor(presentation: PresentationPayload) -> dict[str, object]:
    """Diagnose narrative structure and evidence gaps without a network provider."""
    return diagnose_presentation(presentation)


@app.post("/api/v1/stories/doctor", tags=["review"])
async def story_doctor(story: StoryDocumentV2) -> dict[str, object]:
    """Diagnose a versioned story and preserve explicit finding dispositions."""
    return diagnose_story(story)


@app.post("/api/v1/stories/decision-brief", tags=["generation"])
async def create_decision_story(request: GuidedDecisionRequest) -> dict[str, object]:
    """Compile an author-supplied decision brief locally without invented claims."""
    story = build_decision_story(request.brief, request.theme)
    return {
        "story": story.model_dump(mode="json"),
        "presentation": story.presentation.model_dump(mode="json"),
        "source": "local",
    }


@app.post("/api/content", tags=["generation"])
@app.post("/api/v1/content", tags=["generation"])
async def create_content(request: GenerateContentRequest) -> dict[str, object]:
    """Create an editable outline; no request data is retained by the server."""
    run = await run_in_threadpool(
        generate_ppt_content_run,
        request.topic,
        request.slide_count,
        request.brief,
        [config.model_dump() for config in request.slide_configs],
        request.use_ai,
        request.provider,
    )
    response: dict[str, object] = {
        "presentation": run.presentation,
        "source": run.source,
        "provider": run.provider,
    }
    if run.warning:
        response["warning"] = run.warning
    return response


@app.post("/api/presentations", status_code=201, tags=["export"])
@app.post("/api/v1/presentations", status_code=201, tags=["export"])
async def export_presentation(request: ExportPresentationRequest) -> dict[str, str]:
    """Render an isolated export. User content is retained only in that PPTX."""
    _cleanup_exports()
    try:
        export_id, _ = await run_in_threadpool(
            _export_store().create,
            ".pptx",
            lambda destination: create_presentation(
                request.presentation.model_dump(), destination, asset_root=Path.cwd()
            ),
        )
    except Exception as exc:  # pragma: no cover - OS / renderer failures are environment-specific
        logger.exception("PPTX export failed")
        raise HTTPException(
            status_code=500,
            detail="The PowerPoint file could not be created. Check the server log and try again.",
        ) from exc
    return {"id": export_id, "download_url": f"/api/presentations/{export_id}.pptx"}


def _create_review_bundle(story: StoryDocumentV2, destination: Path) -> None:
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        root = Path(temporary)
        story_path = root / "deck.story.json"
        presentation_path = root / "deck.pptx"
        receipt_path = root / "deck.receipt.json"
        story_path.write_text(
            json.dumps(story.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        outline_digest = digest_value(story.presentation.model_dump(mode="json"))
        provenance = (
            f"Storyboard Studio {__version__}; story schema {story.schema_version}; "
            f"outline sha256 {outline_digest}; integrity does not prove factual truth."
        )
        create_presentation(
            story.presentation.model_dump(),
            presentation_path,
            provenance=provenance,
            asset_root=Path.cwd(),
        )
        receipt = create_receipt(story, story_path, presentation_path)
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for artifact in (presentation_path, story_path, receipt_path):
                archive.write(artifact, artifact.name)


@app.post("/api/v1/bundles", status_code=201, tags=["export"])
async def export_review_bundle(story: StoryDocumentV2) -> dict[str, str]:
    """Export a local PPTX, versioned story, and verifiable receipt as one ZIP."""
    _cleanup_exports()
    try:
        export_id, _ = await run_in_threadpool(
            _export_store().create, ".zip", lambda destination: _create_review_bundle(story, destination)
        )
    except Exception as exc:  # pragma: no cover - OS failures are environment-specific
        logger.exception("Review bundle export failed")
        raise HTTPException(
            status_code=500,
            detail="The review bundle could not be created. Check the server log and try again.",
        ) from exc
    return {"id": export_id, "download_url": f"/api/bundles/{export_id}.zip"}


def _validate_project(project: ProjectPayload) -> dict[str, object]:
    import csv

    with tempfile.TemporaryDirectory(prefix="storyboard-project-validate-") as temporary:
        root = Path(temporary)
        story = materialize_project(project, root)
        columns = {}
        for asset in story.presentation.assets:
            if asset.kind != "data":
                continue
            source = root / asset.path
            if asset.media_type == "text/csv":
                with source.open(encoding="utf-8-sig", newline="") as stream:
                    columns[asset.id] = csv.DictReader(stream).fieldnames or []
            else:
                payload = json.loads(source.read_text(encoding="utf-8"))
                rows = payload.get("rows") if isinstance(payload, dict) else payload
                columns[asset.id] = sorted({key for row in rows for key in row})
        return {"story": story.model_dump(mode="json"), "columns": columns}


@app.post("/api/v1/projects/validate", tags=["projects"])
async def validate_project(project: ProjectPayload) -> dict[str, object]:
    try:
        return await run_in_threadpool(_validate_project, project)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _render_project(project: ProjectPayload, destination: Path) -> None:
    with tempfile.TemporaryDirectory(
        prefix="storyboard-project-render-", dir=destination.parent
    ) as temporary:
        root = Path(temporary)
        story = materialize_project(project, root)
        create_presentation(story.presentation.model_dump(), destination, asset_root=root)


async def _project_export(project: ProjectPayload, *, mode: str) -> dict[str, str]:
    suffix = ".pptx" if mode == "export" else ".zip"
    try:
        export_id, _ = await run_in_threadpool(
            _export_store().create,
            suffix,
            lambda destination: (
                _render_project(project, destination)
                if mode == "export"
                else write_project(project, destination, render=mode == "bundle")
            ),
        )
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    url = f"/api/presentations/{export_id}.pptx" if suffix == ".pptx" else f"/api/bundles/{export_id}.zip"
    return {"id": export_id, "download_url": url}


@app.post("/api/v1/projects/save", status_code=201, tags=["projects"])
async def save_project(project: ProjectPayload) -> dict[str, str]:
    """Save editable inputs and assets without requiring a renderable deck."""
    return await _project_export(project, mode="save")


@app.post("/api/v1/projects/bundle", status_code=201, tags=["projects"])
async def bundle_project(project: ProjectPayload) -> dict[str, str]:
    return await _project_export(project, mode="bundle")


@app.post("/api/v1/projects/export", status_code=201, tags=["projects"])
async def export_project(project: ProjectPayload) -> dict[str, str]:
    return await _project_export(project, mode="export")


@app.post(
    "/api/v1/projects/open",
    tags=["projects"],
    response_model=ProjectPayload,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def open_project(request: Request) -> dict[str, object]:
    content = await request.body()

    def read() -> dict[str, object]:
        with tempfile.TemporaryDirectory(prefix="storyboard-project-open-") as temporary:
            archive = Path(temporary) / "input.zip"
            archive.write_bytes(content)
            return read_project(archive).model_dump(mode="json")

    try:
        return await run_in_threadpool(read)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/presentations/{export_id}.pptx", tags=["export"])
async def download_presentation(export_id: str) -> FileResponse:
    destination = _export_store().get(export_id, ".pptx")
    if destination is None:
        raise HTTPException(
            status_code=404, detail="Presentation not found or it has expired after 24 hours."
        )
    return FileResponse(
        destination,
        filename="storyboard-presentation.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.get("/api/bundles/{export_id}.zip", tags=["export"])
async def download_review_bundle(export_id: str) -> FileResponse:
    destination = _export_store().get(export_id, ".zip")
    if destination is None:
        raise HTTPException(status_code=404, detail="Review bundle not found or expired.")
    return FileResponse(destination, filename="storyboard-review-bundle.zip", media_type="application/zip")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
