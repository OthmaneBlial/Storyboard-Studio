# Proof-first launch kit

These are release-ready drafts, not permission to post them. Storyboard Studio
does not launch by asking for stars. Each narrative starts with one concrete
failure, links an inspectable artifact, and asks for one useful action.

## Hard launch gate

Do not publish a community post until all of these are true:

- a tagged v0.3-or-later GitHub release contains the Narrative Compiler,
  Doctor, Receipt, and app-only demo rather than the generic v0.2 promise;
- release CI, clean-wheel install, PyPI publication, current-source visual
  checks, checksum manifest, and SBOM are green and linked;
- the golden brief, benchmark raw outputs, Security, and Support pages are live;
- one maintainer is available to answer the launch thread and route reports;
- the community rules and account-eligibility requirements are reread on the
  day of posting.

Current status: **blocked at the tagged release and real-user evidence gates**.
These drafts must not be posted as if `main` were a published release.

Run the local gate before preparing a release or community post:

```bash
storyboard launch-check --format markdown
```

It reports the proof assets, exact tag/version alignment, research threshold,
maintainer-capacity declaration, and launch-policy state without changing the
repository or contacting a provider. Add `--allow-network` only when you want
an explicit read-only PyPI metadata check; it never publishes anything. A
`blocked` report is expected until the external evidence above is real.

## Four audience narratives

### Privacy-sensitive deck authors

**Hook:** A private decision should not have to become provider training data
just to become a useful deck.

Storyboard Studio compiles the audience, options, trade-off, evidence gaps, and
owned next step locally. The browser makes the argument editable before export;
the PowerPoint stays native and the Receipt records what was actually reviewed.
Optional providers are disclosed per run and are never the default proof path.

**Proof:** app-only demo, golden onboarding brief, Receipt verification, and
the privacy/provider policy.

**One ask:** try the golden brief locally and report where the first useful
decision story becomes confusing.

### Python and PowerPoint developers

**Hook:** Generating a `.pptx` is easy; preserving story semantics, editability,
evidence, and viewer limits is the engineering work.

The project exposes strict Pydantic models, a Python CLI, OpenAPI, deterministic
Markdown round-trips, typed blocks, native charts/tables, and a `python-pptx`
renderer. A 10-brief benchmark publishes every story, diagnostic, score, and
deck instead of summarizing quality with screenshots.

**Proof:** architecture map, schema files, benchmark manifest, test suite, and
viewer matrix.

**One ask:** reproduce the benchmark and open one bounded rubric or viewer
compatibility report.

### Local-first and self-hosted users

**Hook:** The useful path works without an account, database, analytics, or API
key.

Run the browser studio on loopback or in the documented container, create and
review a decision story, then keep the editable file. The provider catalog
shows network, cost, retention, timeout, and fallback boundaries before a draft.
The experimental OpenAI-compatible adapter accepts loopback endpoints only.

**Proof:** clean-wheel CI, Docker instructions, provider matrix, Security page,
the offline benchmark lane, and the release checksum/SBOM evidence.

**One ask:** run the golden brief in the documented environment and file one
reproducible install or viewer result.

### Agent and tool builders

**Hook:** An agent can create a reviewable deck artifact without receiving a
special path around schema, evidence warnings, or human review.

The JSONL tool server exposes only capabilities, create-draft, diagnose, diff,
render, and verify. It is local, size- and filesystem-bounded, returns stable
unsupported codes, and keeps rendering review-gated. CLI, HTTP, and tool
examples use the same golden brief.

**Proof:** developer integration guide, tool capability response, conformance
tests, and generated review bundle.

**One ask:** run the tool-client example and report one missing capability or
ambiguous unsupported state.

## Three release-post drafts

### Diagnose a decision deck offline

**Title:** Diagnose a decision deck offline before you polish it

A deck can look finished while the decision is still missing.

Storyboard Studio now turns an author-supplied decision brief into a local,
editable story; the Narrative Doctor points to weak decisions, hidden
trade-offs, repeated slides, dense copy, unresolved evidence, and missing
ownership. No account or provider key is required. Exporting a review bundle
adds the story and a verifiable Narrative Receipt beside the native PPTX.

Inspect the golden brief, Doctor JSON, deck, and Receipt here: **[release URL]**.

If you try one thing, run the golden brief and report the first Doctor finding
that feels wrong or unclear. Please use synthetic content.

### Native sourced charts, not chart screenshots

**Title:** Native sourced charts in a local-first PowerPoint workflow

The chart in a generated deck should still be editable, and its source should
not disappear after export.

Storyboard Studio renders checksum-verified local CSV/JSON data as native
PowerPoint charts, keeps source/license/attribution metadata in provenance, and
uses the same typed block in preview and export. Unsupported or missing assets
fail explicitly; the renderer does not fetch remote files.

Inspect the native-visual fixture, Receipt, and viewer limits here:
**[release URL]**.

If you use PowerPoint or LibreOffice, report one versioned viewer result against
the canonical fixture.

### Review PowerPoint stories in Git

**Title:** Review a PowerPoint story in Git before rendering the deck

Binary slide files are difficult to review, but the story does not have to be
binary.

Storyboard Studio round-trips a versioned decision story through strict JSON or
Markdown, preserves sources, notes, typed blocks, assets, and author
dispositions, then renders the same story in CLI, CI, HTTP, or the local tool
server. A reusable GitHub Action publishes the Doctor report and PPTX as review
artifacts without calling a provider.

Inspect the Markdown diff workflow and review Action here: **[release URL]**.

If this fits your workflow, contribute one synthetic template through the
offline `storyboard validate-contribution` gate.

## Community rule check before posting

Rules change; the release owner records the checked date and exact destination
before every post.

| Community | Relevant artifact | Same-day gate |
| --- | --- | --- |
| Show HN | Runnable tagged release and app-only demo | Follow the [Show HN guidelines](https://news.ycombinator.com/showhn.html): the project must be usable, the maker must be present, and nobody is asked to upvote. Check the current temporary account-familiarity notice too. |
| Python community | Schema, CLI, renderer, tests, benchmark | Check the destination rules; lead with Python engineering and reproducible code, not a generic product announcement. |
| Local-first/self-hosted | Offline path, container, provider boundaries | Recheck [r/selfhosted rules](https://www.reddit.com/r/selfhosted/about/rules) on posting day; do not post until a production-ready tagged release and complete install docs satisfy its current project-promotion rules. |
| PowerPoint automation | Native fixtures and viewer matrix | Share an editable artifact and exact viewer/version limitations; never use desktop-wide screenshots. |
| Presentation design | Doctor rubric and before/after story | Ask for a rubric or narrative critique, not stars or broad visual praise. |
| Agent-tool builders | JSONL contract and three integration examples | Lead with bounded capabilities and review gates; do not imply autonomous factual verification. |

## Allowed calls to action

Every public post uses exactly one of these:

1. Try the golden decision brief and report the first-success result.
2. Report one versioned viewer result using a canonical synthetic fixture.
3. Contribute one synthetic template through the validated contribution path.

Do not add “star the repo,” automated voting, follow-for-access, forced OAuth,
or a vague engagement question.

## Two-week review template

Fill this in 14 full days after each real launch. Do not prefill outcomes.

| Field | Evidence |
| --- | --- |
| Release/tag and launch URL | — |
| Launch date and 14-day review date | — |
| Completed golden workflows reported | — |
| Repeat users or second exports observed with consent | — |
| Useful viewer/install/Doctor issues | — |
| Synthetic templates or code contributions opened/merged | — |
| Issue quality: actionable / incomplete / spam | — |
| GitHub unique cloners, release downloads, PyPI downloads | — |
| What failed or confused users | — |
| Decision: continue, fix, narrow, or pause promotion | — |

Traffic or stars alone never justify another launch. Add scope only when the
review shows completed workflows, repeat use, useful reports, or contributions.
