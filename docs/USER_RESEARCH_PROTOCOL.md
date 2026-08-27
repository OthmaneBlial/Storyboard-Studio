# Consented first-success research protocol

This protocol replaces synthetic personas with observed behavior without
collecting private presentation content. It is preparation only: the current
public research count is **0/10 sessions and 0/5 real workflows**. Do not turn
empty rows or maintainer walkthroughs into user evidence.

## Research questions

1. Can a first-time product, operations, consulting, enablement, or automation
   user install Storyboard Studio and export a useful editable deck unaided?
2. Does the decision-story workflow help more than a generic topic-to-slides
   generator for the job the participant actually has?
3. Which Doctor findings are useful, confusing, or false positives?
4. Where do evidence entry, review, export, and viewer compatibility create
   friction?
5. Is there repeated observed demand for one second template?

## Participant and workflow mix

Recruit 10 adults who are not repository maintainers:

- at least 4 product or operations decision authors;
- at least 2 consultants, customer-success, or enablement authors;
- at least 2 Python, PowerPoint-automation, or local-first developers;
- the remaining 2 may come from any primary audience above.

At least 5 sessions must use a real current decision workflow. The participant
keeps the brief on their own machine; the observer records only workflow state,
not the decision text, company, people, sources, screenshots, or exported file.
The other sessions use the public golden synthetic brief.

## Consent script

Read this before timing begins:

> We are evaluating the Storyboard Studio workflow, not you. Participation is
> voluntary and you can stop at any time. We will record only timing, friction
> codes, completion outcome, and an optional anonymized quote. We will not
> collect your brief, deck, sources, screen recording, name, employer, email,
> or API key. You can skip any question. May we proceed under those terms?

Record `consent: yes` and the date. If consent is absent or withdrawn, stop and
do not retain the session row. Ask separately before retaining a quote:

> May we publish this sentence anonymously and edit it only to remove identifying
> details without changing its meaning?

No recording is the default. A participant who wants to share a screenshot must
use the synthetic fixture and crop it to the application window; recording is
not required for a valid session.

## Session procedure

1. Give the participant only the repository URL and the first-success goal:
   “Create, review, edit, and export one decision deck.”
2. Start the timer when they begin reading. Do not coach unless they become
   blocked; record every intervention.
3. Record setup outcome and time to the first editable story.
4. Ask them to explain the decision, trade-off, evidence state, and next action
   shown by the story without revealing private wording.
5. Have them inspect Doctor findings, edit one item, and export the native PPTX
   plus Receipt.
6. Open the deck in their normal viewer when available and record only viewer
   name/version plus PASS, PARTIAL, or FAIL.
7. Ask what they would use again, what felt generic, which finding was wrong,
   and which other workflow they expected. Do not promise a template.
8. Stop timing at a usable export or explicit abandonment.

## Allowed session record

Copy this block to a private local note. Never commit raw notes:

```yaml
session_id: SXX
consent_date: YYYY-MM-DD
audience_band: product-ops | consulting-enablement | developer-automation
workflow: golden-synthetic | real-private-content-not-collected
setup:
  outcome: completed | abandoned
  seconds: 0
first_editable_story_seconds: 0
export:
  outcome: completed | abandoned
  total_seconds: 0
  viewer: name-and-version | not-run
friction_codes: []
doctor:
  useful_codes: []
  false_positive_codes: []
evidence_friction: none | short-anonymized-description
interventions: 0
outcome: short-anonymized-description
quote:
  permission: no | yes
  text: optional-anonymized-sentence
```

For repeatable local validation, the same fields can be stored as one JSON file
per session. The repository ships a strict, offline validator and aggregator;
these commands never contact a provider and never read a brief or deck:

```bash
storyboard research validate /private/research/S01.json --output /private/research/S01.validation.json
storyboard research aggregate /private/research \
  --output-dir /private/research/aggregate
```

The aggregate writes only `aggregate.json` and `aggregate.md`; it includes
timing, completion, friction, suppressed small audience segments, and quotes
whose publication permission is explicitly `yes`. It does not copy raw
records, and it defers the second-template and thesis decisions until the
10-session/5-real-workflow threshold is actually met. Review the generated
report manually before publishing it. A valid local record is tooling output,
not user evidence; the status page remains **0/10 sessions and 0/5 real
workflows** until consented sessions happen.

[`examples/research/session.example.json`](../examples/research/session.example.json)
is a command-contract fixture only. It is synthetic, is not included in the
research count, and must not be copied into a public findings report.

Allowed friction codes are `setup-abandonment`, `install-ambiguity`,
`generic-output`, `doctor-false-positive`, `evidence-friction`,
`preview-confusion`, `export-confusion`, `viewer-mismatch`, and `other`.

## Privacy and retention

- Never collect names, employers, contact details, source files, brief/deck
  text, screenshots of private workflows, API keys, or screen recordings.
- Store raw timing/notes outside the repository with access limited to the
  researcher. Delete them within 30 days of the aggregate report.
- Publish only counts, medians, failure categories, anonymized outcomes, and
  quotes with explicit quote permission.
- Suppress a segmented result when fewer than 3 participants are in that
  segment; report it only in the aggregate.
- A consented session that fails is still evidence and must not be removed from
  completion-rate calculations.

## Analysis and decision rules

Publish successes and failures together using
[`USER_RESEARCH_STATUS.md`](USER_RESEARCH_STATUS.md). At minimum report setup
abandonment, generic output, Doctor false positives, evidence friction, viewer
mismatches, completion, and time to first useful export.

Do not select a second template until all 10 sessions and 5 real workflows are
complete. A candidate must be requested or naturally attempted by at least 3
independent participants, fit the local evidence-aware product thesis, and have
a maintainer/fixture path. If no candidate meets that bar, keep only the
decision brief.

Revisit the thesis rather than changing the benchmark when most completed real
workflows prefer generic generation and participants cannot explain added value
from the decision, evidence, or Receipt workflow. Record the decision and the
contrary evidence publicly.
