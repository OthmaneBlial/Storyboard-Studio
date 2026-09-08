# Storyboard Studio 0.3.0 — release notes draft

> Draft for the next release. This file describes the current `main` candidate
> and is not evidence that `v0.3.0` has been tagged or published.

Candidate source used for the local distribution evidence: `9720becea598fe2e91e7ee9814b67b0b7b1039dc`
Package metadata currently remains `0.2.0` until the release owner freezes a
tagged candidate.

## What is ready in this candidate

- A guided decision brief that turns audience, outcome, options, trade-offs,
  evidence, ownership, and next action into a reviewable story.
- Narrative Doctor findings with explicit author dispositions and field-level
  correction paths.
- Native editable PowerPoint output, diffable story JSON/Markdown, portable
  project bundles, and hash-verifiable Narrative Receipts.
- Deterministic local planning with optional, explicitly selected provider
  adapters; no API key or network request is needed for the default path.
- A new **Private AI, Clear Decisions** example, native deck fixture, poster,
  and browser-only workflow preview.
- Reproducible wheel/sdist builds, checksum and CycloneDX SBOM validation, and
  clean-install smoke checks outside the checkout.

## Verification recorded

- Full Python suite: 189 tests passed.
- Chromium contract suite: 15 scenarios passed.
- Lint, format, site, asset, layout, contract-parity, and distribution checks
  passed locally.
- GitHub CI run [`34256139919`](https://github.com/OthmaneBlial/Storyboard-Studio/actions/runs/34256139919)
  passed all active jobs for the candidate commit.
- Current local distribution evidence is recorded in
  [`installation-validation-current-2026-09-08.json`](installation-validation-current-2026-09-08.json).
- The legacy Office recorder now fails closed unless `--allow-office` is
  explicitly passed; the browser-only recorder remains the recommended path.

## Known release gates

- The candidate is not yet published to PyPI or attached to a GitHub release.
- Native binaries remain build previews until downloaded, installed, signed,
  and tested on each retained OS/architecture.
- Interactive PowerPoint/Keynote/Google Slides validation is still pending.
- Consent-based external user research remains at 0/10 sessions and 0/5 real
  workflows.
- The browser-only AI video is a positioning preview. The release-candidate
  video must be recorded only after the public release and viewer gates pass.

## Suggested release checklist

1. Freeze a new version in `pyproject.toml`, `CHANGELOG.md`, and this note.
2. Run the exact-tag CI, distribution, viewer, privacy, and install gates.
3. Attach the validated wheel, sdist, `SHA256SUMS`, SBOM, attestations, and
   tested native artifacts to the GitHub release; publish to PyPI only after
   Trusted Publishing is verified.
4. Download the public artifacts again and record hashes and clean-install
   results before filming the final demonstration.
