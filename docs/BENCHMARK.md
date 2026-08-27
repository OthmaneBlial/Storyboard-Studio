# Reproducible decision-story benchmark

The `decision-v1` benchmark makes Storyboard Studio's release claims inspectable.
It is a deterministic engineering benchmark, not a claim that a machine score
captures taste, factual truth, or user value.

## Scope

The public suite contains 10 CC0 synthetic decision briefs. Every case declares:

- the same five expected story roles: context, constraints, options, trade-off,
  and an owned next step;
- expected claim-level evidence gaps and author-checked fixture counts;
- fields that are intentionally at risk of excessive copy density;
- the shared 16:9, editable, Latin LTR, PowerPoint/LibreOffice viewer boundary.

The content, design, and coherence categories are inspired by the three-part
evaluation in [PPTAgent and PPTEval](https://aclanthology.org/2025.emnlp-main.728/).
Our criteria also follow [PPT-Eval's published approach](https://microsoft.github.io/ppteval/)
of task-specific rubrics, partial credit, and explainable feedback. Storyboard's
implementation is deliberately deterministic and adds product-specific checks
for editability, provenance, privacy, and reproducibility; it does not reproduce
those projects' model-based evaluators.

## Published rubric

Each lane receives at most 100 points. Every individual criterion, awarded
point, and short evidence string is written to `score.json`.

| Category | Points | Deterministic criteria |
| --- | ---: | --- |
| Content | 20 | Decision-term coverage (6), audience/outcome coverage (4), option-title preservation (4), owner/next-step coverage (4), no numeric tokens beyond the brief or structural enumerators (2) |
| Design | 20 | Shared overflow budget (8), at least four semantic block roles (4), native text/no full-slide raster (5), true 16:9 canvas (3) |
| Coherence | 20 | Expected five-role sequence (8), explicit decision (4), visible trade-off (4), final action/owner signal (4) |
| Editability | 10 | Exported text frames (6), no full-slide rasterization (4) |
| Provenance | 10 | Claim inventory (3), unresolved gaps remain explicit (3), expected checked/unresolved state preserved (4) |
| Privacy | 10 | Network matches declared boundary (4), sensitive fields remain excluded (4), no remote presentation assets (2) |
| Reproducibility | 10 | A second safe run has the same canonical story digest (6), tool/schema versions recorded (4) |

The rubric awards structural evidence only. For example, “native editable” means
the PPTX contains native text frames and no full-slide picture; it does not mean
that every viewer will render every font identically.

## Run it

Install the development environment, then run both lanes:

```bash
make setup
make benchmark
```

Or select every boundary explicitly:

```bash
storyboard benchmark \
  --suite benchmarks/decision-v1/suite.json \
  --output-dir output/benchmark \
  --release local-check \
  --provider openai-compatible \
  --overwrite
```

The default optional-provider lane is intentionally **offline**. With no
provider network opt-in, it records `network_status: not-sent` and the precise
fallback reason. It exercises adapter selection, redaction, fallback, rendering,
and scoring, but it must not be cited as external-model quality.

To run a configured provider, explicitly allow it:

```bash
storyboard benchmark \
  --output-dir output/benchmark-provider \
  --provider openai-compatible \
  --allow-provider-network
```

The OpenAI-compatible adapter accepts loopback endpoints only. Gemini may use an
external network and account billing when selected and configured. The runner
does not repeat a completed live-provider call merely to earn repeatability
points.

## Inspect raw evidence

The checked-in source baseline is
[`benchmarks/decision-v1/baseline/main-2026-08-27/`](../benchmarks/decision-v1/baseline/main-2026-08-27/).
It is dated instead of labeled as a release because these benchmark changes are
currently unreleased on `main`.
It contains:

```text
report.json / report.md / manifest.json
cases/<case-id>/<lane>/
  story.json
  doctor.json
  evidence.json
  layout.json
  provider.json
  score.json
  deck.pptx
```

`manifest.json` records a SHA-256 digest for every raw artifact. PPTX ZIP bytes
are not promised to be identical across environments; the stable contract is
the canonical story digest and the rubric signals.

## Regression policy

`make benchmark-check` regenerates both lanes and compares them with the tracked
source baseline. A lower score for a comparable case/lane fails the command. A changed
provider or model is reported as `provider-not-comparable` instead of being
silently compared with a different system.

This catches score regressions; it does not replace the manual viewer matrix,
browser checks, accessibility review, or real user research.

## Known limitations

- The rubric is a deterministic heuristic, not a human or visual-model review.
- PowerPoint, Keynote, and Google Slides are not launched by the benchmark.
- Synthetic briefs cannot validate usefulness with real decision authors.
- The default provider result is an offline fallback, not provider-model quality.
- Semantic repeatability does not promise byte-identical PPTX archives.

## Improve it without widening scope

The bounded benchmark contribution in
[`docs/GOOD_FIRST_ISSUES.md`](GOOD_FIRST_ISSUES.md) accepts one viewer fixture or
one rubric assertion at a time. A contribution must use synthetic/public data,
state its license, keep provider networking opt-in, add a regression test, and
include the before/after raw score evidence.
