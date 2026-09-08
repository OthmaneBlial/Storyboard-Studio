# Distribution security validation — 2026-09-08

Scope: the working source following commit `4c00a35`, macOS ARM64, Python 3.14.
This is a local check, not a published release or a penetration-test certificate.

- Built wheel and sdist in a temporary source copy containing a synthetic private
  `output/private.zip` and `.env`. Both archives passed
  `scripts/validate_distribution.py`; neither sentinel path was packaged.
- The wheel contained 42 members (156570 bytes); the sdist contained 76 members
  (172890 bytes). Sizes describe that build, not reproducible release hashes.
- Required CLI, HTML, JavaScript, demo and token resources were present.
- Regression tests reject private paths, traversal, absolute tar members, links
  and missing runtime data. Archives are inspected without extracting them.
- `pip-audit --local --skip-editable` initially reported pip and pytest advisory
  findings. pip was upgraded to 26.2.1 and pytest to 9.1.1. A second audit found
  no known vulnerabilities in the installed environment. This does not audit
  application logic, native system libraries or future dependency resolutions.
- The full Python suite passed (129 tests), followed by the three archive tests
  after adding the tar traversal/link regression. Ruff lint and format passed.

Repeat with `python -m build`, `make validate-distribution`, and, after installing
`.[security]`, `make security-audit`. Upgrade pip using `make setup` when preparing
a new development environment. Preserve reports with each release candidate.

## Pending checks

Docker is not installed on this machine. The Dockerfile now uses explicit COPY
inputs, installs libcairo2 and switches to a non-root user, but no successful
image build, layer inspection, container health or container export is claimed.
A Docker-capable runner must insert synthetic private inputs, build the image,
inspect its filesystem and run the HTTP export smoke as UID 10001.

GitHub private vulnerability reporting was disabled when checked. SECURITY.md
therefore supplies the owner's actual public email contact; this audit did not
change repository settings or send a message.
