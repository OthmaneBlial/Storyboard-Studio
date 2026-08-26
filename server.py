"""Local-first FastAPI service for Storyboard Studio."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
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
from schemas import ExportPresentationRequest, GenerateContentRequest

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "output"
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
    for candidate in OUTPUT_DIR.glob("*.pptx"):
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
    version="1.0.0",
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

    if request.method == "POST" and request.url.path.startswith("/api/"):
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
    return FileResponse(ROOT / "index.html", media_type="text/html")


@app.get("/api/health", tags=["system"])
async def health() -> dict[str, object]:
    return {"status": "ok", "ai_configured": bool(os.getenv("GEMINI_API_KEY")), "export_ttl_hours": 24}


@app.post("/api/content", tags=["generation"])
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
async def export_presentation(request: ExportPresentationRequest) -> dict[str, str]:
    """Render an isolated export. User content is retained only in that PPTX."""
    _cleanup_exports()
    export_id = uuid4().hex
    destination = OUTPUT_DIR / f"{export_id}.pptx"
    try:
        await run_in_threadpool(create_presentation, request.presentation.model_dump(), destination)
    except Exception as exc:  # pragma: no cover - OS / renderer failures are environment-specific
        logger.exception("PPTX export failed")
        raise HTTPException(
            status_code=500,
            detail="The PowerPoint file could not be created. Check the server log and try again.",
        ) from exc
    return {"id": export_id, "download_url": f"/api/presentations/{export_id}.pptx"}


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
