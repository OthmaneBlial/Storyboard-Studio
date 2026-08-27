# Release and provenance policy

Every release is built from a version tag by GitHub Actions. The workflow
builds a source distribution and wheel, installs both artifacts in clean virtual
environments outside the checkout, runs the installed CLIs, and exports the
packaged demo from each artifact. It then compiles the guided decision fixture,
verifies its Narrative Receipt, starts the packaged browser studio, and attaches
the exact artifacts to the GitHub release. The same verified distributions are
published to PyPI through the `pypi` GitHub environment and OIDC Trusted
Publishing; the project never stores a long-lived PyPI token.

When GitHub's artifact-attestation service is available to the repository, the
workflow publishes a build-provenance attestation for each GitHub artifact,
while PyPI's trusted-publishing action uploads its publish attestations. Users can
therefore verify that a downloaded wheel or sdist came from this repository's
tagged workflow rather than trusting a manually uploaded file. A release is
not described as reproducible until the clean-install and sample-export steps
have passed.

Each GitHub release also carries a `SHA256SUMS` manifest generated from those
exact verified distributions and a CycloneDX `SBOM.cdx.json` generated from the
clean-installed wheel's resolved environment. Both evidence files are attached
to GitHub releases only; they are deliberately kept out of the PyPI upload.

An existing GitHub tag whose matching package version has not reached PyPI can
be rebuilt with the manual `Release artifacts` workflow and its exact
`release_tag` input. The workflow checks out that tag, rejects a tag/version
mismatch, clean-installs its wheel, and publishes only through the `pypi`
environment. A manual run does not recreate or overwrite the GitHub release.

Before making the PyPI/`uvx` path the README default, verify the live registry
endpoint and run `uvx storyboard-studio demo --bundle` in an empty directory.
The distribution exposes both `storyboard` and `storyboard-studio`; the second
entry point exists so the short `uvx` package command does not need `--from`.

Run `make launch-check` from the checkout before creating a release tag. It
prints a conservative, machine-readable summary of proof assets, tag/version
alignment, PyPI publication, research evidence, maintainer capacity, and the
launch-policy state. A blocked result is expected until the external gates are
actually satisfied; do not bypass it by changing the reported counts.

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
- Review merged external pull requests and add consented contributor credits;
  generated GitHub notes are a starting point, not the recognition ledger.
- Link any shipped public template, fixture, viewer report, or other artifact
  from the contributor showcase without asking for stars.
- Never include `.env`, API keys, private briefs, or unreviewed generated decks.
