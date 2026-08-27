# Release and provenance policy

Every release is built from a version tag by GitHub Actions. The workflow
builds a source distribution and wheel, installs the wheel in a clean virtual
environment outside the checkout, runs the installed CLI, exports the packaged
demo, compiles the guided decision fixture, verifies its Narrative Receipt,
starts the packaged browser studio, and attaches the exact artifacts to the
GitHub release. The same verified distributions are published to PyPI through
the `pypi` GitHub environment and OIDC Trusted Publishing; the project never
stores a long-lived PyPI token.

When GitHub's artifact-attestation service is available to the repository, the
workflow publishes a build-provenance attestation for each GitHub artifact,
while PyPI's trusted-publishing action uploads its publish attestations. Users can
therefore verify that a downloaded wheel or sdist came from this repository's
tagged workflow rather than trusting a manually uploaded file. A release is
not described as reproducible until the clean-install and sample-export steps
have passed.

## Maintainer checklist

- Update `pyproject.toml` and `CHANGELOG.md` together.
- Run `make lint`, `make format-check`, `make test`, `make smoke`, and the
  sample export locally.
- Create an annotated `vX.Y.Z` tag only after those checks pass.
- Confirm that the `storyboard-studio` PyPI publisher matches owner
  `OthmaneBlial`, repository `Storyboard-Studio`, workflow `release.yml`, and
  environment `pypi`.
- Copy the generated release notes from the changelog and mention the exact
  commit, Python versions, and verification jobs.
- Never include `.env`, API keys, private briefs, or unreviewed generated decks.
