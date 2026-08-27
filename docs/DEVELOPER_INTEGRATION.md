# Stable developer and agent integration

All supported integration paths use the same canonical decision brief:
`examples/briefs/onboarding-decision.json`. The browser studio remains the
canonical review surface. CLI, HTTP, and tool callers receive structural and
evidence warnings; they do not gain factual-verification or review-bypass
capabilities.

## 1. Local CLI

```bash
bash examples/integrations/local_cli.sh
```

The example compiles the golden brief, runs Doctor and evidence coverage, then
writes a review bundle. Each command uses the same strict story models as the
browser.

## 2. Local HTTP API

In one terminal:

```bash
storyboard serve
```

In another:

```bash
python3 examples/integrations/http_api.py
```

The script inspects the provider catalogue, creates the deterministic local
decision story, runs Doctor, and downloads a temporary review bundle. It uses
only the loopback HTTP server and refuses to overwrite its prior output.

## 3. Agent-neutral JSONL tool server

```bash
python3 examples/integrations/tool_client.py
```

The client starts `storyboard tools --once` for each request. A long-running
caller can start `storyboard tools` and exchange one JSON request/response per
line on stdin/stdout:

```json
{"id":"caps","action":"capabilities","arguments":{}}
```

Stable actions are `create_draft`, `diagnose`, `diff`, `render`, and `verify`.
`capabilities` publishes action schemas, unsupported states, network/provider
status, and operational limits. Unknown actions and providers return stable
codes such as `unsupported-action` and `unsupported-provider`.

`render` returns `review-required` while Doctor findings or unresolved evidence
exist unless the caller sets `acknowledge_review_warnings: true`. Acknowledging
does not resolve findings or imply truth; the result still carries the complete
review summary and disclaimer. Existing output files are never overwritten.

## Self-hosted boundaries

| Surface | Rate | Request size | Retention | Filesystem |
| --- | --- | --- | --- | --- |
| Browser/HTTP | 20 rate-limited POST requests per client per 60 seconds; layout/evidence preflight is exempt | 200 KB request body | Request bodies are not stored; generated PPTX/ZIP files expire after 24 hours | Export directory from `STORYBOARD_OUTPUT_DIR`; API asset paths resolve under the server working directory |
| JSONL tool server | Sequential, one response per request line | 200,000 bytes per line | Requests/responses are not retained; acknowledged render artifacts persist until the operator removes them | `--workspace` is the hard read boundary; `--output-dir` must stay inside it; basenames only; no overwrite |
| CLI | Operator-controlled process rate | Canonical schema field limits | No request log; user-selected artifacts persist | Paths explicitly supplied by the operator; asset roots follow the input story directory |

The tool transport makes no network request and supports the local planner only.
Gemini and the loopback OpenAI-compatible drafting adapters remain browser/HTTP
choices with the separate policy in [`PROVIDER_POLICY.md`](PROVIDER_POLICY.md).
Files, evidence, sources, assets, and notes are not accepted by provider calls.

Integrity, schema, and rendering success never establish factual truth. Human
review in `storyboard serve` owns claim meaning, evidence status, and approval.
