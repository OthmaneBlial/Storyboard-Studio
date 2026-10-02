# Contributing

Keep changes small, concrete and easy to review. Describe the behavior before and
after, run the relevant local checks, and record the result. Owner maintenance uses
small validated direct-main commits; external contributors can still propose PRs.

Requirements: Rust 1.95+, Node 20+ for desktop authoring/tools, and the platform's
[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/). Install desktop
CLI dependencies with `npm --prefix apps/desktop ci`, then run `make check`.
`make demo` builds and verifies an editable deck. `make desktop` builds the local
installer. GitHub CI remains disabled; do not re-enable it without owner direction.

Use shared core/rendering functions when changing behavior in CLI or desktop.
Keep input validation, rollback and scoped filesystem access intact. Add a focused
runnable regression check for nontrivial logic; avoid tests that merely mirror code.
Inspect affected screens and exported objects when changing layout/UI.

Use synthetic examples with clearly labeled assumptions. Never include private
projects, credentials, real customer claims or invented compatibility evidence.
Gallery regeneration: `make gallery`; independent LibreOffice/Poppler checks:
`make office`. Report the actual viewer and version separately from XML validation.

See [architecture](docs/ARCHITECTURE.md), [format](docs/native/FORMAT.md) and
[security](SECURITY.md). Report only necessary details and redact local paths/secrets.
