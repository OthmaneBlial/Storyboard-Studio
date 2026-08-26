# Contributing to Storyboard Studio

Thanks for helping make concise, editable presentations easier to create.

## Prerequisites

- Python 3.10+
- PowerPoint, LibreOffice, or another compatible viewer if you want to inspect exports manually

## Setup

```bash
git clone https://github.com/OthmaneBlial/Storyboard-Studio.git
cd Storyboard-Studio
make setup
```

Run the application with `make run`, then open `http://127.0.0.1:8000`.

## Architecture

- `index.html` and `static/` contain the dependency-free browser studio.
- `server.py` owns HTTP boundaries, static serving, size/rate limits, and short-lived exports.
- `schemas.py` is the public request/presentation contract.
- `ai_helper.py` provides the optional Gemini provider and the local fallback planner.
- `generate_pptx.py` renders validated data into editable native PowerPoint shapes.
- `examples/` holds runnable, non-sensitive input fixtures.

Keep the server local-first: do not add persistence, telemetry, or third-party requests without an explicit product decision and clear documentation.

## Before opening a pull request

```bash
make lint
make format-check
make test
make export-sample
```

For renderer changes, open the produced file in a PowerPoint-compatible viewer and check for clipping, overflow, and unexpected wrapping. For UI changes, test keyboard navigation and a narrow mobile viewport.

## Pull request expectations

- Keep a pull request focused and explain the user-facing change.
- Add or update tests for behavior changes, especially validation and export behavior.
- Do not commit API keys, `.env` files, generated local exports, or personal presentation content.
- Preserve the promise that exported decks are editable and that the app works without Gemini.

There is no required commit-message format. Clear, imperative summaries are appreciated.
