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

- `storyboard_studio/web/` contains the packaged, dependency-free browser studio.
- `storyboard_studio/cli.py` owns the installed compile, diagnose, migrate,
  render, diff, verify, demo, and serve commands.
- `storyboard_studio/story.py` compiles versioned author-owned decision fields;
  `doctor.py` and `receipt.py` own deterministic review and provenance.
- `server.py` owns HTTP boundaries, static serving, size/rate limits, and short-lived exports.
- `schemas.py` is the public request, story, presentation, and disposition contract.
- `ai_helper.py` provides the optional Gemini provider and the local fallback planner.
- `generate_pptx.py` renders validated data into editable native PowerPoint shapes.
- `examples/` holds runnable, non-sensitive input fixtures.

The complete ownership and trust-boundary map is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

Keep the server local-first: do not add persistence, telemetry, or third-party requests without an explicit product decision and clear documentation.

## Before opening a pull request

```bash
make lint
make format-check
make test
make export-sample
make validate-contribution
```

For renderer changes, open the produced file in a PowerPoint-compatible viewer and check for clipping, overflow, and unexpected wrapping. For UI changes, test keyboard navigation and a narrow mobile viewport.

Useful bounded contributions include a synthetic template, a viewer
compatibility report, an accessibility fix, a documentation improvement, or a
focused renderer test. Issue labels explain the expected surface; ask before
starting a larger product change.

Template and fixture pull requests must include a contribution manifest and a
passing `storyboard validate-contribution` report. See
[`docs/TEMPLATE_CONTRACT.md`](docs/TEMPLATE_CONTRACT.md). The gate is local and
does not upload the fixture; it complements, but does not replace, human privacy
and licensing review.

## Pull request expectations

- Keep a pull request focused and explain the user-facing change.
- Add or update tests for behavior changes, especially validation and export behavior.
- Do not commit API keys, `.env` files, generated local exports, or personal presentation content.
- Preserve the promise that exported decks are editable and that the app works without Gemini.

There is no required commit-message format. Clear, imperative summaries are appreciated.

See [`docs/MAINTAINER_PLAYBOOK.md`](docs/MAINTAINER_PLAYBOOK.md) for triage and
release cadence. Shipped external contributors are credited according to
[`docs/CONTRIBUTOR_RECOGNITION.md`](docs/CONTRIBUTOR_RECOGNITION.md).
