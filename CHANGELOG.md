# Changelog

All notable changes to this project are documented here.

## [Unreleased]

- The release workflow now builds, clean-installs, and attests source and wheel
  artifacts from version tags.
- CI covers the supported Python 3.10–3.14 range.

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
