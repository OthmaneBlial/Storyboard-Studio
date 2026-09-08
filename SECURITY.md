# Security policy

## Supported versions

Security fixes are applied to the latest release on the `main` branch.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability. Instead, use GitHub’s private vulnerability reporting for this repository when available, or contact the repository owner privately through their GitHub profile with:

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
