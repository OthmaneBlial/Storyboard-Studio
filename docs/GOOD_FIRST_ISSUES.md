# Bounded contribution queue

These are intentionally small and have acceptance criteria. They can become
GitHub issues when a contributor is ready; no hidden product decision is
required.

1. **[Accessibility: preview focus order](https://github.com/OthmaneBlial/Storyboard-Studio/issues/8)** (`accessibility`, `good first issue`)
   — verify the editable preview with keyboard-only navigation and add a
   regression assertion for focus order.
2. **[Renderer: long-title fixture](https://github.com/OthmaneBlial/Storyboard-Studio/issues/9)** (`renderer`, `good first issue`) — add one
   approved wrapping fixture and document the viewer result.
3. **[Documentation: translated quick start](https://github.com/OthmaneBlial/Storyboard-Studio/issues/10)** (`documentation`, `help wanted`)
   — translate the no-key path while preserving privacy boundaries.
4. **[Template: nonprofit decision brief](https://github.com/OthmaneBlial/Storyboard-Studio/issues/11)** (`templates`, `good first issue`) —
   contribute synthetic content and evidence assumptions only.
5. **[Compatibility: viewer report](https://github.com/OthmaneBlial/Storyboard-Studio/issues/12)** (`renderer`, `help wanted`) — run the
   fixture in a supported viewer and attach versioned screenshots.
6. **[Provider conformance: local-server fixture](https://github.com/OthmaneBlial/Storyboard-Studio/issues/13)** (`provider`, `help wanted`) —
   add one synthetic Ollama or LM Studio response fixture to the bounded
   loopback conformance suite without expanding the transfer contract.
7. **[Benchmark: one viewer or rubric improvement](https://github.com/OthmaneBlial/Storyboard-Studio/issues/7)** (`benchmark`, `help wanted`)
   — change only `benchmarks/decision-v1/`, `storyboard_studio/benchmark.py`,
   `tests/test_benchmark.py`, or `docs/BENCHMARK.md`; use synthetic/public data
   with an explicit license, keep provider networking opt-in, add one failing-
   then-passing regression assertion, and attach before/after raw `score.json`
   evidence. Maintainers will answer contract questions in the issue; proposals
   that require private decks or redefine the product thesis are out of scope.
