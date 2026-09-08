# Architecture and trust boundaries

Storyboard Studio has one canonical story contract and several narrow entry
surfaces. The browser remains the review surface; the CLI, HTTP API, CI action,
and JSONL tool server do not bypass validation or evidence warnings.

```text
Browser studio    CLI    HTTP API    GitHub Action    JSONL tools
       \           |        |             |               /
        +----------+--------+-------------+--------------+
                           |
                    schemas.py contracts
                           |
          +----------------+----------------+
          |                                 |
 decision compiler / import          provider adapters
          |                          local by default;
          |                          explicit bounded transfer
          +----------------+----------------+
                           |
         StoryDocumentV2 + typed semantic blocks
                           |
       +-------------------+--------------------+
       |                   |                    |
 Narrative Doctor    evidence coverage    layout preflight
       +-------------------+--------------------+
                           |
                  native PPTX renderer
                           |
          PPTX + story + Narrative Receipt
```

## Ownership map

| Contract | Owner files | What may depend on it |
| --- | --- | --- |
| Public models | `schemas.py` | Browser/API payloads, CLI, Doctor, renderer, benchmark |
| Decision compilation and import | `storyboard_studio/story.py`, `storyboard_studio/markdown.py` | Browser, CLI, API, tools |
| Provider boundary | `storyboard_studio/providers.py`, `ai_helper.py` | Draft generation only; never Doctor, evidence, or renderer truth |
| Narrative and evidence review | `doctor.py`, `evidence.py`, `receipt.py` | Browser, CLI, API, CI, tools |
| Preview/export geometry | `layout.py`, `themes/storyboard-tokens.json` | Browser preview and PowerPoint renderer |
| Native output | `generate_pptx.py`, `assets.py` | PPTX exports and review artifacts |
| Browser review | `storyboard_studio/web/`, `web/static/validation.js` | Human editing, dispositions, explicit export, shared client-side contract validation |
| External integration | `server.py`, `cli.py`, `tool_server.py` | Validated orchestration around canonical modules |
| Quality proof | `tests/`, `browser_tests/`, `benchmarks/` | CI, release gates, public raw evidence |

## Trust boundaries

- The local planner, compiler, Doctor, evidence report, layout preflight, and
  renderer make no provider request.
- Gemini is external; the OpenAI-compatible adapter is loopback-only. Both are
  explicit per request and receive only the documented bounded text fields.
- Local files, evidence, sources, assets, and speaker notes are excluded from
  provider requests.
- A URL, checked source, Doctor result, benchmark score, or receipt does not
  establish factual truth.
- The server keeps isolated export files only for the documented expiry window;
  there is no account, analytics, or presentation database.
- Automated callers can create artifacts, but the browser is the canonical
  place to review copy, evidence warnings, and author dispositions.

## Extension rule

Add behavior beside the canonical contracts, not around them. A new entry
surface must validate with the same models, preserve the local path, disclose
network/filesystem boundaries, return machine-readable unsupported states, and
add tests. A new template or fixture must pass
`storyboard validate-contribution`; a new provider must pass the conformance
suite and update the supported-state matrix.

## Browser contract boundary

`web/static/validation.js` owns the browser-side validation of story envelopes,
outlines, semantic blocks, sources, assets, and brand kits. The studio wires it
to the current theme catalog and block choices at startup; the validator does
not read the filesystem, call a provider, or infer missing evidence. Import,
Markdown round-trip, save, and export flows call these functions before they
mutate the active story or request an artifact. The Python models in
`schemas.py` remain the authoritative server boundary, while the browser
validator provides immediate, equivalent feedback for interactive editing.

The Markdown interchange implementation lives in `storyboard_studio/markdown.py`.
The historical top-level `outline_markdown.py` path is a compatibility shim, so
installed callers and older scripts continue to work while package code imports
the canonical module directly.
