# Dependency footprint — 2026-09-08

macOS ARM64, Python 3.14.6. Independent temporary virtual environments and empty working directories. Pip cache was warm; elapsed times are observations, not a speed guarantee.

| Install | Packages including pip | Environment bytes | pip install seconds |
| --- | ---: | ---: | ---: |
| Previous default, wheel | 47 | 110371823 | 6.88 |
| Previous default, sdist | 47 | 110371813 | 8.54 |
| Minimal, wheel | 19 | 68071293 | 3.69 |
| Minimal, sdist | 19 | 68071283 | 5.26 |
| Gemini + SVG, wheel | 42 | 103557045 | 6.61 |

All runs passed version, demo bundle, receipt verification, packaged web serving, local content generation and real HTTP PPTX download. The final runs also verified that startup imports neither CairoSVG nor Gemini. The extras run imported both optional libraries and rendered an actual SVG to PNG; no paid model call was made.

Native libraries outside the virtual environment are not counted. Dependency versions and raw measurements are recorded in [dependency-footprint.json](dependency-footprint.json). Windows/Linux and other Python versions remain unverified for this candidate.
