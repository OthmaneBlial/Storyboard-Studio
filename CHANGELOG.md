# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- Complete installed CLI with `serve`, `demo`, `export`, and deterministic
  `doctor` commands.
- Packaged browser application and synthetic demo data so a wheel works outside
  the source checkout.
- Versioned `/api/v1/doctor` endpoint with explainable narrative and evidence
  findings.
- Playwright browser contract covering keyboard authoring, editing, reordering,
  undo/redo, responsive widths, accessibility states, preview/PPTX parity, and
  export.
- Versioned decision-story schema and guided local compiler using explicit
  audience, outcome, context, constraints, options, trade-offs, evidence,
  owner, next-step, and review-date fields.
- In-browser story map and Narrative Doctor with accepted,
  ignored-with-reason, and resolved dispositions.
- Portable review bundles, PPTX provenance metadata, receipt verification,
  explicit v1 migration, and readable schema v2 story diffs.
- An uncut browser-to-editable-viewer demo, custom social preview, and three
  downloadable golden examples with receipt and LibreOffice proof.
- Optional viewer-result recording in CLI-generated Narrative Receipts.
- A packaged, validated template catalog with one launched decision brief and
  evidence-gated dormant contracts for project alignment, proposals, and
  incident retrospectives.
- A reproducible 10-brief benchmark with raw local/provider-fallback artifacts,
  a published 100-point rubric, and release-to-release regression checks.
- An offline template/fixture contribution gate for privacy, license, schema,
  rendering, and attribution validation.
- Privacy-safe `storyboard research validate/aggregate` commands for consented
  session records, with strict schemas, high-confidence secret scanning,
  small-segment suppression, and deferred evidence decisions.
- A proof-first `storyboard launch-check` command that reports release,
  publication, research, maintainer-capacity, and launch-policy gates without
  contacting providers by default.
- A `storyboard-studio` executable alias for the future short `uvx` demo path
  while preserving the `storyboard` CLI.

### Changed

- Keep the launch checker compatible with Python 3.10 through the conditional
  `tomli` fallback.
- Make the macOS proof recorder resolve a foreground window ID and fail closed
  instead of relying on a fixed screen rectangle.
- CI and release workflows now verify the installed wheel from an empty
  directory, including the packaged server, demo export, and Doctor report.
- Visual CI regenerates its PPTX from the current renderer before comparing it
  with the approved reference.
- TestClient uses Starlette's supported `httpx2` path instead of the deprecated
  compatibility path.
- Long editable titles now fit the preview at mobile and desktop widths.

## [0.2.0] - 2026-08-26

### Added

- Editable storyboard preview with inline copy/layout/block editing, slide
  ordering, duplication, deletion, undo/redo, and local JSON import/export.
- Author-supplied source/evidence/owner fields copied to native PowerPoint
  speaker notes with an explicit unverified boundary.
- Decision, comparison, timeline, and metric editorial blocks plus six-theme
  token guidance and a versioned JSON Schema.
- `storyboard` CLI, `/api/v1` aliases, deterministic Markdown interchange,
  local asset manifest validation, synthetic gallery, and release-candidate
  viewer QA tooling.

### Changed

- The no-key path is described accurately as local-first/no-network by default;
  Gemini remains an optional disclosed provider.
- The initial workflow is a private decision brief for a small alignment group.

## [0.1.1] - 2026-08-26

### Fixed

- Make every documented `make` target use the virtual environment created by `make setup`, so a fresh clone can run, test, lint, format-check, and export without an implicit global Python install.

## [0.1.0] - 2026-08-26

### Added

- Local-first browser studio for briefing, reviewing, and exporting presentations.
- Optional Gemini-assisted outline generation with a deterministic local fallback.
- Validated FastAPI API with request-size limits, local rate limiting, security headers, health check, and isolated expiring exports.
- Native editable 16:9 PowerPoint renderer with six editorial themes.
- CLI sample export, Docker image, automated tests, CI, contributor guidance, security policy, and release documentation.

### Changed

- Removed hard-coded Gemini credentials and deprecated experimental model usage.
- Replaced shared global presentation state and arbitrary client-controlled filenames.
