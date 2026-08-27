"""Local-first FastAPI service for Storyboard Studio."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import tempfile
import time
import zipfile
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ai_helper import generate_ppt_content
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
from storyboard_studio.layout import analyze_overflow, load_layout_contract
from storyboard_studio.receipt import create_receipt, digest_value
from storyboard_studio.resources import web_root
from storyboard_studio.story import build_decision_story

ROOT = Path(__file__).resolve().parent
WEB_DIR = web_root()
STATIC_DIR = WEB_DIR / "static"
OUTPUT_DIR = Path(os.getenv("STORYBOARD_OUTPUT_DIR", str(Path.cwd() / "output"))).expanduser().resolve()
MAX_REQUEST_BYTES = 200_000
EXPORT_TTL_SECONDS = 24 * 60 * 60
RATE_LIMIT = 20
RATE_WINDOW_SECONDS = 60
EXPORT_ID_RE = re.compile(r"^[a-f0-9]{32}$")
logger = logging.getLogger("storyboard")
_requests: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = asyncio.Lock()


def _cleanup_exports() -> None:
    """Remove only expired generated decks; source files are never touched."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    cutoff = time.time() - EXPORT_TTL_SECONDS
    for candidate in (*OUTPUT_DIR.glob("*.pptx"), *OUTPUT_DIR.glob("*.zip")):
        try:
            if candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            logger.warning("Could not remove expired export %s", candidate.name)


async def _is_rate_limited(client_id: str) -> bool:
    now = time.monotonic()
    async with _rate_lock:
        bucket = _requests[client_id]
        while bucket and bucket[0] <= now - RATE_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return True
        bucket.append(now)
        return False


@asynccontextmanager
async def lifespan(_: FastAPI):
    OUTPUT_DIR.mkdir(exist_ok=True)
    _cleanup_exports()
    logger.info("Storyboard Studio is ready. Gemini configured: %s", bool(os.getenv("GEMINI_API_KEY")))
    yield


app = FastAPI(
    title="Storyboard Studio API",
    version="1.1.0",
    description="A local-first, editable PowerPoint presentation generator.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_and_limits(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request is too large. Keep presentation input below 200 KB."},
        )

    if (
        request.method == "POST"
        and request.url.path.startswith("/api/")
        and request.url.path != "/api/v1/layout/preflight"
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
        "export_ttl_hours": 24,
        "layout_schema": layout.schema_version,
    }


@app.get("/api/v1/layout-contract", tags=["system"])
async def layout_contract() -> dict[str, object]:
    """Expose the validated local tokens used by both preview and export."""
    return load_layout_contract().model_dump(mode="json")


@app.post("/api/v1/layout/preflight", tags=["review"])
async def layout_preflight(presentation: PresentationPayload) -> dict[str, object]:
    """Find deterministic text overflow risks before creating a PowerPoint."""
    return analyze_overflow(presentation.model_dump(mode="json"), load_layout_contract())


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
    presentation, source, warning = await run_in_threadpool(
        generate_ppt_content,
        request.topic,
        request.slide_count,
        request.brief,
        [config.model_dump() for config in request.slide_configs],
        request.use_ai,
    )
    response: dict[str, object] = {"presentation": presentation, "source": source}
    if warning:
        response["warning"] = warning
    return response


@app.post("/api/presentations", status_code=201, tags=["export"])
@app.post("/api/v1/presentations", status_code=201, tags=["export"])
async def export_presentation(request: ExportPresentationRequest) -> dict[str, str]:
    """Render an isolated export. User content is retained only in that PPTX."""
    _cleanup_exports()
    export_id = uuid4().hex
    destination = OUTPUT_DIR / f"{export_id}.pptx"
    try:
        await run_in_threadpool(
            create_presentation,
            request.presentation.model_dump(),
            destination,
            asset_root=Path.cwd(),
        )
    except Exception as exc:  # pragma: no cover - OS / renderer failures are environment-specific
        logger.exception("PPTX export failed")
        raise HTTPException(
            status_code=500,
            detail="The PowerPoint file could not be created. Check the server log and try again.",
        ) from exc
    return {"id": export_id, "download_url": f"/api/presentations/{export_id}.pptx"}


def _create_review_bundle(story: StoryDocumentV2, destination: Path) -> None:
    with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temporary:
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
    export_id = uuid4().hex
    destination = OUTPUT_DIR / f"{export_id}.zip"
    try:
        await run_in_threadpool(_create_review_bundle, story, destination)
    except Exception as exc:  # pragma: no cover - OS failures are environment-specific
        logger.exception("Review bundle export failed")
        raise HTTPException(
            status_code=500,
            detail="The review bundle could not be created. Check the server log and try again.",
        ) from exc
    return {"id": export_id, "download_url": f"/api/bundles/{export_id}.zip"}


@app.get("/api/presentations/{export_id}.pptx", tags=["export"])
async def download_presentation(export_id: str) -> FileResponse:
    if not EXPORT_ID_RE.fullmatch(export_id):
        raise HTTPException(status_code=404, detail="Presentation not found.")
    destination = OUTPUT_DIR / f"{export_id}.pptx"
    if not destination.is_file():
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
    if not EXPORT_ID_RE.fullmatch(export_id):
        raise HTTPException(status_code=404, detail="Review bundle not found.")
    destination = OUTPUT_DIR / f"{export_id}.zip"
    if not destination.is_file():
        raise HTTPException(status_code=404, detail="Review bundle not found or expired.")
    return FileResponse(destination, filename="storyboard-review-bundle.zip", media_type="application/zip")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
