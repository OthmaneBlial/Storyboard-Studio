# Test coverage

The repository exposes `make coverage` for a reproducible branch-coverage
measurement. It runs the complete Python suite with Coverage.py, prints the
annotated report, and writes the machine-readable result to the ignored
`output/coverage.json` path.

The latest local run on 2026-09-08 used macOS ARM64, Python 3.14.6, Coverage.py
7.16.0 and 188 tests:

| Measurement | Result |
| --- | ---: |
| Statements covered | 89% |
| Branches covered | 73% |
| Combined report | 86% |

These figures describe the current source and are diagnostic rather than a
release gate. The critical contract tests remain the authority for receipt,
request-limit, asset, layout, packaging and launch behavior; coverage does not
prove cross-platform execution, viewer compatibility or factual correctness.
