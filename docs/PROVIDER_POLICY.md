# Provider and enrichment policy

The deterministic local planner is the default. A provider must be selected for
each freeform draft; configuration alone never activates network access. Before
generation, the browser shows model, network boundary, supported state, timeout,
cost ownership, and retention ownership. After generation it records the
selected and actually used provider, network status, and stable fallback reason.

## Supported-state matrix

| Provider | State | Network boundary | Structured output | Files/evidence | Model configuration |
| --- | --- | --- | --- | --- | --- |
| Deterministic local planner | Supported | Offline | Native deterministic object | Unsupported | `deterministic-v1` |
| Google Gemini | Supported, optional | External Google provider | JSON response mode | Unsupported | `GEMINI_MODEL` (default `gemini-2.5-flash`) |
| Local OpenAI-compatible | Experimental | Loopback only | `response_format: json_object` | Unsupported | `OPENAI_COMPATIBLE_MODEL` |

All three adapters have a named maintainer, capability declaration, deterministic
local fallback, and conformance coverage in `tests/test_providers.py`. Adding a
provider requires those artifacts plus policy documentation; provider count is
not a product goal.

## Exact transfer boundary

Provider requests can contain only `topic`, `brief`, `slide_count`, and explicit
slide-focus text for that request. Story assets, local files, evidence excerpts,
source metadata, URLs, speaker notes, and the current presentation are excluded.
The request schema rejects unknown `files`, `assets`, or `evidence` fields. The
current adapters do not support file/evidence transfer at all; a future adapter
must add a separate, per-request selection UI and threat-model review before
that capability can become true.

Provider output is always an unverified draft. It cannot mark evidence as
author-checked, prove factual truth, or bypass schema, Doctor, evidence, layout,
and renderer validation.

## Cost, retention, and timeout

- Local planner: no provider charge and no provider-side retention.
- Gemini: the user's Google account, regional availability, model pricing, and
  API data policy apply. Storyboard does not estimate cost or retain the
  provider response.
- Local OpenAI-compatible endpoint: the endpoint operator owns compute, cost,
  logs, and retention. Storyboard connects only to `localhost` or a loopback IP
  and stores no provider response.

`PROVIDER_TIMEOUT_SECONDS` defaults to 30 and is bounded to 1–120 seconds. A
missing configuration fails before any request (`not-sent`). A runtime failure
records `external-attempted` or `loopback-attempted`, reduces the error to a
stable non-secret code, and runs the deterministic local planner.

## Local OpenAI-compatible configuration

The experimental adapter is for a locally operated Ollama, LM Studio, or
equivalent endpoint exposing `/v1/chat/completions`:

```bash
export OPENAI_COMPATIBLE_BASE_URL="http://127.0.0.1:11434/v1"
export OPENAI_COMPATIBLE_MODEL="your-local-model"
# Only if the local endpoint requires it:
export OPENAI_COMPATIBLE_API_KEY="local-endpoint-token"
```

Remote hosts, embedded credentials, URL queries, and fragments are rejected.
Storyboard does not claim conformance for every OpenAI-compatible server; the
checked-in suite covers the exact bounded request/response contract above.

Images, document-to-deck conversion, and deep research remain separate
experiments. They require their own privacy, consent, licensing, caching,
source-traceability, cost, retention, and fallback review.
