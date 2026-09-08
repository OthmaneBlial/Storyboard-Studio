# Install and start the complete studio

These instructions install a locally built candidate. Changes on `main` after
0.2.0 are not included in the historical 0.2.0 release. PyPI publication is not
verified; do not assume `pip install storyboard-studio` resolves this candidate.

Obtain the candidate wheel from the maintainer or build it from the checkout:
`python -m pip install build`, then `python -m build`. Check its provenance before
installing it. Published release hashes will be listed with the corresponding
release; this document does not supply a hash for an unpublished build.

## macOS and Linux

From a directory outside the checkout (replace the wheel path):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install /absolute/path/to/storyboard_studio-0.2.0-py3-none-any.whl
.venv/bin/storyboard --version
.venv/bin/storyboard demo --bundle --output demo.pptx
.venv/bin/storyboard verify demo.receipt.json
.venv/bin/storyboard serve --open-browser
```

## Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install 'C:\Downloads\storyboard_studio-0.2.0-py3-none-any.whl'
.\.venv\Scripts\storyboard.exe --version
.\.venv\Scripts\storyboard.exe demo --bundle --output demo.pptx
.\.venv\Scripts\storyboard.exe verify demo.receipt.json
.\.venv\Scripts\storyboard.exe serve --open-browser
```

The remote CI run [34223348104](https://github.com/OthmaneBlial/Storyboard-Studio/actions/runs/34223348104)
exercises the wheel and sdist paths on Linux, macOS and Windows with Python
3.12, including a local server and HTTP export. This is runner evidence for the
documented baseline; see [the support matrix](SUPPORT_MATRIX.md) for the
remaining Python, architecture and viewer limits.

The browser address is http://127.0.0.1:8000. Stop the server with Ctrl+C.
`--open-browser` is optional; no development reloader is enabled by default.
The installed CLI and local planner work without a provider key. Installation
needs dependency downloads unless an operator supplies an offline wheelhouse.

If startup reports a port conflict, use `serve --port 8001`. If the export cache
is not writable, set `STORYBOARD_OUTPUT_DIR` to a writable private directory.
The startup check creates that directory and tests a temporary write; it does
not clean or migrate existing user files. A second process can still occupy the
port after the preflight; the server's bind error remains authoritative.

## Repeatable distribution test

```sh
python scripts/validate_installation.py dist/*.whl dist/*.tar.gz --output output/install-report.json
```

Run with a Python that can create virtual environments. Each archive is installed
independently in a temporary environment with an empty working directory whose
path includes spaces and an accent. The test invokes the installed CLI, creates
and verifies a real bundle, serves packaged web resources, generates content
with the local planner and inspects a downloaded PowerPoint archive. It records
OS, Python, dependency versions, duration and environment size, then removes the
temporary environment. It does not validate Windows, Linux or Office merely by
running on macOS, and it does not prove network isolation at the OS level.

The [latest dated local results](installation-validation-2026-09-08.json) record
successful base and `gemini,svg` wheel/sdist runs on macOS ARM64 / Python 3.14.6.
The older [installation-validation.json](installation-validation.json) file is
kept as historical evidence from an earlier dependency set.

## Optional features

The base installation includes the local planner, studio, editable native charts
and tables, and PNG/JPEG images. It does not load or install the Gemini SDK or
CairoSVG. Install extras from the **same candidate archive** to avoid mixing
unreleased source with a different public version:

```sh
.venv/bin/python -m pip install '/absolute/path/to/storyboard_studio-0.2.0-py3-none-any.whl[gemini]'
.venv/bin/python -m pip install '/absolute/path/to/storyboard_studio-0.2.0-py3-none-any.whl[svg]'
```

On PowerShell use `.\.venv\Scripts\python.exe` and the Windows archive path.
The SVG extra also needs native Cairo: `brew install cairo` on macOS or the
`libcairo2` package on Debian/Ubuntu. Windows native Cairo setup is not validated;
use PNG/JPEG until a tested distribution is available. The Dockerfile includes
Cairo and the SVG extra. No Cairo installation is required for base startup.

An unavailable SVG renderer gives a specific installation error; it does not
silently omit the image. A missing Gemini SDK uses the local fallback with an
explicit missing-dependency message and records that no request was sent.
The Gemini extra import is tested; no live provider call is claimed.

See [measured dependency footprint](DEPENDENCY_FOOTPRINT.md) for the base/extra comparison.
