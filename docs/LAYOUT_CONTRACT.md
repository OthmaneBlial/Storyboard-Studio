# Shared layout contract

Storyboard Studio uses one validated runtime contract for the browser preview
and PowerPoint renderer: `themes/storyboard-tokens.json`. The installed wheel
contains the same contract at `storyboard_studio/data/storyboard-tokens.json`.
`make validate-layout` fails if those copies diverge.

The v2 contract defines the 16:9 canvas, safe area, local font fallback stacks,
typography scale, heading/summary/content/visual geometry for `left`, `right`,
and `focus`, overflow budgets, and all six public color systems. Validation
rejects frames outside the canvas, remote font URLs, missing generic fallbacks,
unknown public theme ids, and color pairs below the documented WCAG contrast
thresholds.

The browser obtains the validated values from `GET /api/v1/layout-contract`.
The PowerPoint renderer loads the same file for every export. To test an
explicit local contract without modifying the repository:

```bash
storyboard export \
  --input examples/product-brief.json \
  --output output/contract-test.pptx \
  --theme-tokens /absolute/path/to/storyboard-tokens.json
```

`STORYBOARD_THEME_TOKENS=/absolute/path/to/storyboard-tokens.json make run`
applies an explicit validated contract to both the API and renderer. Invalid
input stops startup or export with the failing field; there is no network
fallback.

## Overflow preflight

The studio checks valid copy against layout-specific budgets before export.
It highlights the affected 16:9 canvas and offers deterministic actions:
shorten at a word boundary, use the wider focus layout, split a standard slide,
or review dense semantic-block copy. The browser will not export while an open
layout finding remains.

CLI and API integrations can run the same check:

```bash
storyboard preflight examples/product-brief.json --fail-on-overflow
curl -s http://127.0.0.1:8000/api/v1/layout/preflight \
  -H 'content-type: application/json' \
  --data-binary @examples/product-brief.json
```

## Constrained local brand kit

Start from `themes/brand-kit.example.json`. A kit can choose one public base
theme, seven local RGB colors, and display/body font fallback stacks. It cannot
include URLs, CSS, macros, templates, or remote assets. Normal text requires at
least 4.5:1 contrast and the accent requires 3:1 against the background.

```bash
storyboard brand-kit themes/brand-kit.example.json
storyboard export \
  --input examples/product-brief.json \
  --output output/branded.pptx \
  --brand-kit themes/brand-kit.example.json
```

In the browser, use **Import brand kit** after creating or importing a story.
The JSON remains in the local presentation payload and the same validated
colors/fonts are used in preview and export.
