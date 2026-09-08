# Release and provenance policy

## Current publication boundary

The latest release verified during the 8 September audit is `v0.2.0`, with a
wheel and source archive. It does not contain the current guided workflow or
receipt v2. PyPI returned 404 at that observation. This snapshot is not a live
registry check. The release workflow is active under `.github/workflows/`, with
a preserved reference under `.github/workflows-disabled/`. Its presence proves
neither execution nor publication; remote run URLs and downloaded artifacts
remain required evidence.

Before building a tagged release, the active workflow looks up a completed green
`ci.yml` run for the exact tag commit and checks the required Python, package,
container, Linux/macOS/Windows install, browser, and benchmark jobs by name. A missing run, a different SHA, or a failed
job stops the release before any artifact is published. This gate establishes
technical evidence only; it does not prove PyPI/GitHub publication, viewer
compatibility, signatures, or user adoption.

Both tag pushes and manual dispatches resolve the candidate SHA from the
checkout (`git rev-parse HEAD`) after selecting the requested tag. The workflow
waits briefly for the corresponding CI run to finish before rejecting the
candidate, so a manual dispatch cannot accidentally validate the branch that
launched it.

[`release-state.json`](release-state.json) inventories the README's product
claims, source files, test files and introduction boundary. `source-present`
means only that those files exist. It never means the test ran. Local validation
results belong in dated execution reports; remote CI requires its run URL and
source SHA, and public delivery requires downloaded artifact hashes and an
installation result for the exact version.

## Required release process (not a report of completed publication)

A candidate must build from its exact tag and pass the complete test, package,
viewer and privacy gates. Install both wheel and sdist outside the checkout,
run the packaged CLI/studio, export the demo bundle and verify its receipt.
Attach the exact distributions only after those checks pass. The intended PyPI
channel uses the `pypi` environment and OIDC Trusted Publishing; project/name
ownership and publisher configuration must be verified without a long-lived
PyPI token.

Build distributions with `make build-distributions` (or
`python scripts/build_distributions.py --output-dir dist`). The helper passes a
stable `SOURCE_DATE_EPOCH` to the PEP 517 build and rewrites wheel, tar and gzip
metadata into a canonical order. When no epoch is supplied it uses the checked
out Git commit timestamp, so two builds of the same commit produce identical
bytes. A release review should run the helper twice in separate directories and
compare both SHA-256 values before attaching the artifacts.

Generate `SHA256SUMS` from the verified distributions and a CycloneDX
`SBOM.cdx.json` from the clean-installed environment. Both are deliberately
kept out of the PyPI upload. Run `scripts/validate_release_evidence.py` before
uploading them. A definition containing these filenames is not proof that a
release has them. Attestations must be verified against the downloaded artifact
and tag; a configured attestation action alone is insufficient.

The optional native preview is built with `scripts/build_native.py` and
`packaging/storyboard-studio.spec`. It embeds the runtime and `python-pptx`
templates, records a SHA-256 and performs an offline demo smoke test. Native
workflow artifacts remain candidate evidence until the exact OS/architecture
has been tested after download; no signature, notarization or public release is
implied by the build.

Before recommending `uvx storyboard-studio`, verify the exact registry version
and run `uvx storyboard-studio demo --bundle` in an empty directory. Both
`storyboard` and `storyboard-studio` entry points are provided by the source.
Do not replace or move an existing published tag to update old metadata.

`make launch-check` is a conservative inspection, not a publication command.
It separates the source inventory, preserved workflow, actual local tag,
registry observation and pending human gates. A local tag must exist at clean
HEAD and match the package version. That check still does not prove a remote
release. A PyPI metadata response does not prove downloaded/installable files.
Use `--fail-on-blocked` when a gate must stop a command; the default prints a
report for diagnosis. Later release gates must distinguish prepublication
readiness from postpublication verification to avoid circular requirements.

Research counts, a prose declaration or a checked roadmap box cannot establish
user consent, availability of a maintainer, or publication. The structured
external gates remain pending until their evidence can be reviewed. Historical
Office reports and media retain their original dates; they do not validate a
changed candidate.

## Maintainer checklist

- Update `pyproject.toml` and `CHANGELOG.md` together.
- Run `make lint`, `make format-check`, `make test`, `make smoke`, `make sbom`,
  `make build-distributions`, and the sample export locally.
- Build twice from the same clean commit with the same epoch and compare the
  wheel and sdist SHA-256 values before generating release evidence.
- Keep the release evidence validator in the tagged workflow; it must run after
  `SHA256SUMS` is generated and before release evidence is uploaded.
- Create an annotated `vX.Y.Z` tag only after those checks pass.
- Confirm that the `storyboard-studio` PyPI publisher matches owner
  `OthmaneBlial`, repository `Storyboard-Studio`, workflow `release.yml`, and
  environment `pypi`.
- Copy the generated release notes from the changelog and mention the exact
  commit, Python versions, and verification jobs.
- Review merged external pull requests and add consented contributor credits;
  generated GitHub notes are a starting point, not the recognition ledger.
- Link any shipped public template, fixture, viewer report, or other artifact
  from the contributor showcase without asking for stars.
- Never include `.env`, API keys, private briefs, or unreviewed generated decks.
