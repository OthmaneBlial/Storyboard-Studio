# Security policy

## Supported versions

Security fixes are developed on `main`. The latest verified published release is
0.2.0; subsequent fixes on `main` are unreleased until a new tagged distribution
is published. Older releases are not maintained independently.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability. Email the maintainer at **blial.othmane@gmail.com** (the public contact on the
repository owner’s GitHub profile), with:

- a clear description of the issue;
- steps to reproduce it safely;
- affected files or endpoint(s); and
- any suggested mitigation.

Do not include real API keys, personal presentation data, or exploit payloads that could harm other users. We will acknowledge credible reports, investigate, and coordinate a fix before public disclosure where possible.

## Security boundaries

- `GEMINI_API_KEY` is read only from the process environment and must never be committed.
- The API accepts validated presentation JSON only; clients cannot choose server filesystem paths.
- PPTX/ZIP server exports live in marked private cache directories with random IDs.
  Downloads are refused at 24 hours; expired server files are swept every five
  minutes and at startup/export. CLI outputs and downloaded files are not purged.
- This project is meant to run locally or behind an operator-controlled reverse proxy. The built-in in-memory rate limit is a safety measure, not a distributed abuse-prevention service.

## Export cache ownership

By default the server uses `~/Library/Caches/storyboard-studio/exports` on
macOS, `%LOCALAPPDATA%/storyboard-studio/exports` on Windows and
`$XDG_CACHE_HOME/storyboard-studio/exports` (or `~/.cache/...`) on Linux.
`STORYBOARD_OUTPUT_DIR` overrides that cache root. It may be a new nested path;
it must not be a symlink. Per-export directories are created exclusively and
carry an ownership marker. Unmarked files, foreign files and symlink targets
are never swept. Failed writes are discarded inside their newly owned directory
before a download URL is returned.

Existing files from the old `output/` implementation are deliberately left
untouched. Inspect and remove unwanted legacy exports manually; the application
cannot safely infer which of those files belong to the user. This means old
copies are not retroactively covered by the new TTL promise.

## Local HTTP limits

The server counts actual body bytes before JSON parsing, including chunked
requests; bodies above 200,000 bytes return 413. Inconsistent lengths return
400, incomplete bodies time out after 10 seconds, and at most four modifying
requests execute concurrently per server process (429 when busy). The per-client
rate limiter has a bounded client map. Run a single local server process for
these limits; a shared deployment requires its own authentication and quotas.

Only loopback Host names/addresses are allowed by default. Browser Origin must
match the request's scheme and Host. Operators using a reverse proxy can set
`STORYBOARD_ALLOWED_HOSTS` to comma-separated exact hostnames and must separately
provide authentication and TLS; this setting is not an authentication mechanism.
Do not use a wildcard. CLI/API clients with no Origin retain the local workflow.

Local SVG assets are checked before rasterization: at most 20 megapixels,
16384 source-side units, 10000 elements and 64 levels, with a bounded raster
surface. Recursive `<use>` elements are unsupported; expand symbols before
import. Active/external SVG content remains rejected.

## Distribution checks

See [the dated validation record](docs/SECURITY_VALIDATION.md) for the exact
archive and dependency checks performed. Docker copies only application inputs,
runs as UID 10001, and installs Cairo for SVG support. Run it with
`docker run --rm -p 127.0.0.1:8000:8000 storyboard-studio` after building locally.
Container execution remains unverified until a Docker-capable runner passes the
smoke and private-sentinel checks. Do not expose this unauthenticated local tool
directly to the Internet.

## Browser work retention

Project history stays in tab memory; no automatic browser storage is enabled.
Explicit JSON downloads preserve source excerpts and review decisions, which may
be sensitive. PowerPoint export does not replace project saving. See
[Saving projects](docs/SAVING_PROJECTS.md) for retention and recovery limits.

## Portable asset ingestion

Project inputs are bounded and checked before use; see
[Portable projects](docs/PORTABLE_PROJECTS.md) for exact limits. Only the five
named project routes have an 8 MB HTTP body allowance; other routes retain
200 KB. Project assets are explicitly supplied bytes, never implicitly fetched
from evidence locators or the server cwd. SVG CSS/styles and escaped attribute
values are rejected before Cairo to prevent hidden external references. ZIP
members are inspected before any editable inputs are restored. No remote model
receives project files. Removing evidence entries from a ZIP does not anonymize
the brief, speaker notes or asset data.
