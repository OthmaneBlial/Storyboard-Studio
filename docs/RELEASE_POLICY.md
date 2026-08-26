# Release and provenance policy

Every release is built from a version tag by GitHub Actions. The workflow
builds a source distribution and wheel, installs the wheel in a clean virtual
environment, runs the sample export and smoke test, and attaches the exact
artifacts to the GitHub release.

When GitHub's artifact-attestation service is available to the repository, the
workflow publishes a build-provenance attestation for each artifact. Users can
therefore verify that a downloaded wheel or sdist came from this repository's
tagged workflow rather than trusting a manually uploaded file. A release is
not described as reproducible until the clean-install and sample-export steps
have passed.

## Maintainer checklist

- Update `pyproject.toml` and `CHANGELOG.md` together.
- Run `make lint`, `make format-check`, `make test`, `make smoke`, and the
  sample export locally.
- Create an annotated `vX.Y.Z` tag only after those checks pass.
- Copy the generated release notes from the changelog and mention the exact
  commit, Python versions, and verification jobs.
- Never include `.env`, API keys, private briefs, or unreviewed generated decks.
