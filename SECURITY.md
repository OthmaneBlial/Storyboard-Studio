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
- PPTX exports are isolated by random ID and automatically removed after 24 hours.
- This project is meant to run locally or behind an operator-controlled reverse proxy. The built-in in-memory rate limit is a safety measure, not a distributed abuse-prevention service.
