# Storyboard Studio Roadmap — v0.3 to v1.0

> **Product bet:** make Storyboard Studio the local-first **narrative compiler for decision decks**: turn a brief and author-owned evidence into a story that can be inspected, challenged, diffed, and regenerated before it becomes a natively editable PowerPoint.

This roadmap replaces the completed v0.2 delivery plan. It is ordered by dependency and adoption leverage, not by feature count. GitHub stars are a lagging signal of a useful product, credible proof, and a healthy community; they are not a deliverable and cannot be promised.

## Executive verdict — 27 August 2026

Storyboard Studio has real potential, but it is **not yet differentiated enough to break out**.

The repository already looks unusually trustworthy for a young project: the browser studio is distinctive and responsive; the no-key path works; exports are native PowerPoint; strict validation, privacy boundaries, CI, release provenance, branch protection, viewer checks, contribution files, and a public showcase exist. After the documented setup, lint, format, 14 tests, asset validation, and the end-to-end smoke export pass locally.

The problem is not missing polish. The problem is that the first result still feels like a generic slide generator:

- the deterministic planner mostly returns the same reusable “opportunity / context / approach / choices / action” copy for unrelated topics;
- every content block is forced through three generic bullets, even when it claims to be a comparison, metric, decision, or timeline;
- the browser is a good outline editor but not a layout-faithful preview, and a long title visibly clips in a compact preview card;
- the product has no native chart, table, or local image workflow, so decks remain text-heavy;
- evidence support exists in the schema, but the UI only exposes part of it;
- the GitHub release is not a one-command installable studio, and the clean-wheel CI check does not actually exercise the installed CLI outside the checkout;
- the “user research” and case study are explicitly synthetic proxies, not external validation;
- at the initial snapshot, the public “60-second demo” was a transcript rather
  than motion proof and GitHub still used a generated social preview; P0.3 now
  records the resolved proof work.

The repository is one day old at this snapshot and reports 0 stars, 0 forks, one open issue, and two release-asset downloads. That is day-zero adoption, not proof that the idea failed. The right next move is to sharpen the product hook before promoting it widely.

## The category and the opening

[Presenton](https://github.com/presenton/presenton) already competes on breadth with desktop and Docker distribution, many model providers, document import, images, charts, templates, API, MCP, and editable export. [Slidev](https://github.com/slidevjs/slidev) owns developer presentations; [PptxGenJS](https://github.com/gitbrent/PptxGenJS) and [python-pptx](https://github.com/scanny/python-pptx) own programmatic generation; [PPTAgent](https://github.com/icip-cas/PPTAgent) explores heavyweight reference-deck generation.

Storyboard Studio should not become a smaller copy of those projects. Its opening is a narrow job they do not own:

> **“Before you make slides, make the decision story defensible.”**

The memorable feature should be a deterministic **Narrative Doctor** and a portable **Narrative Receipt**:

- the Doctor explains missing context, duplicate ideas, unsupported claims, unclear trade-offs, weak sequencing, copy-density risks, and absent owners or next steps;
- the Receipt records the reviewed story, author-supplied evidence, unresolved gaps, planner/provider, renderer version, input digest, and verification result without claiming that a source is true;
- both work locally and remain useful without an API key.

That turns Storyboard Studio from “another AI deck generator” into an inspectable decision-deck workflow.

## Product contract to protect

1. **Useful without credentials.** The no-key workflow must produce a topic-specific result from structured author input, not generic filler.
2. **Review before render.** The argument, evidence, sequence, and next action stay editable before a `.pptx` exists.
3. **Native ownership.** Supported text, shapes, tables, charts, notes, and local images remain editable or independently movable in PowerPoint.
4. **No evidence laundering.** Sources are author-supplied, provenance is visible, and missing evidence stays visibly missing.
5. **Local-first by default.** No account, telemetry, remote asset fetch, or provider call is required. Every optional network boundary is explicit.
6. **Portable contracts.** A reviewed story can live in JSON or Markdown, be diffed in Git, diagnosed in CI, and regenerated deterministically.
7. **Honest compatibility.** Preview and viewer limitations are tested and published, never hidden behind a “professional” claim.

## North-star workflow

The v1 experience should be explainable in one sentence:

> Add a decision, audience, constraints, options, evidence, and next step; Storyboard Studio diagnoses the narrative, shows exactly what is weak, then exports the reviewed version as a native PowerPoint plus a verifiable receipt.

The primary user remains a privacy-sensitive consultant, product/operations lead, or enablement author preparing a concise decision or alignment deck. Developers and agents are an important distribution surface, not the product’s only audience.

## Success scorecard

Do not gate releases on stars. Gate them on evidence that can cause healthy adoption.

| Outcome | v0.3 target | v1 target |
| --- | --- | --- |
| First success | 8 of 10 clean-machine testers export the sample in under 5 minutes without maintainer help | One verified `uvx`/`pipx` command opens the studio and exports a deck on macOS, Windows, and Linux |
| Narrative usefulness | 5 external users can explain the decision, trade-off, and next step from the generated story | 10 consented users complete real work; at least 5 voluntarily use it again within 30 days |
| Local quality | Golden briefs produce topic-specific, non-duplicated narratives and actionable Doctor findings | Content, design, and coherence benchmark is published for every release candidate |
| Output fidelity | Current output is regenerated before structural and visual CI; supported layouts have no known fixture clipping | Browser/PPTX parity is fixture-tested for every supported block, theme, and data element |
| Trust | Installed artifacts, not checkout files, pass clean-directory verification | PyPI/GitHub artifacts, checksums, provenance, SBOM, viewer matrix, and privacy boundaries match the release tag |
| Community | Every starter item exists as a labeled public issue with acceptance criteria | 3 external merged contributions and a documented response/release cadence |
| Proof | One privacy-safe app-only workflow demo and three reproducible synthetic examples | Three consented case studies or anonymized workflow reports, with no private briefs published |

Track stars, forks, unique cloners, PyPI downloads, release downloads, repeat contributors, and issue quality as context. Never add default telemetry or dark-pattern star prompts to manufacture these numbers.

---

## P0 — Make the claim true and the first run effortless

**Outcome:** a stranger can install the actual studio with one command, reproduce the current product claims, and see proof before investing time.

### P0.1 Ship a complete installable application

- [x] Replace the single-purpose `storyboard --input ...` entry point with explicit commands: `storyboard serve`, `storyboard demo`, `storyboard export`, `storyboard doctor`, and `storyboard --version`.
- [x] Package `index.html`, `static/`, schema files, and the canonical sample as real package data; make `storyboard serve` work from an installed wheel outside the repository.
- [x] Change CI to build the wheel, install it in a clean temporary directory, leave the checkout, run the installed command, start the installed server, and complete health → local outline → PPTX export.
- [ ] Publish `storyboard-studio` to PyPI through Trusted Publishing only after the package name, ownership, release policy, and clean-install proof are confirmed. The package endpoint is currently absent.
- [ ] Make `uvx storyboard-studio demo` or an equally short documented command the default README path; keep clone + `make setup` as the contributor path.
- [x] Decide whether the renderer-only CLI remains a supported subcommand or a separate lightweight package. The renderer remains the explicit `storyboard export` subcommand inside the complete studio wheel.

**Done when:** a user in an empty directory can run one documented command, open the studio, generate the no-key sample, and export a PPTX without relying on repository files.

### P0.2 Test the experience people actually use

- [x] Add an automated browser contract for sample brief → local planner → inline edit → reorder → undo/redo → export, including keyboard-only operation and visible provider state.
- [x] Cover 320 px, 375 px, and desktop widths; assert no horizontal overflow and no clipped editable title or action controls.
- [x] Add accessibility checks for labels, focus order, error announcements, contrast, reduced motion, and file import errors.
- [x] Regenerate the reference PPTX from current source inside visual CI before rendering and comparison. A checked-in old fixture must not let a broken renderer stay green.
- [x] Add a parity fixture proving that each browser preview block maps to the expected PowerPoint layout and copy.
- [x] Resolve or pin the Starlette/httpx deprecation path before it becomes a compatibility failure.

**Done when:** the main author journey, not only the Python API, fails CI when it regresses.

### P0.3 Show the product in 60 seconds

- [x] Record one privacy-safe app-only demo: start the app, load the decision brief, run the Doctor, fix one finding, export, then select and edit a PowerPoint element. Stop capture during the application hand-off so the desktop and background windows are never recorded.
- [x] Put an optimized GIF/video and accessible transcript above the README fold; stop calling the transcript itself a demo.
- [x] Create a custom 1280×640 GitHub social preview showing the story map, Doctor finding, and editable PPTX result.
- [x] Reduce the opening README to one audience, one pain, one proof, one command, and one “why not Presenton/Slidev?” comparison link.
- [x] Add three downloadable golden examples with input, output, receipt, screenshot, viewer result, and exact regeneration command.

**Done when:** a visitor can understand the unique workflow and inspect a real artifact without cloning the repository.

---

## P1 — Build the moat: Narrative Doctor and Narrative Receipt

**Outcome:** the no-key path provides decision-quality guidance that broad prompt-to-slide tools do not.

### P1.1 Replace generic filler with a structured decision brief

- [x] Introduce a versioned story schema with explicit fields for decision, audience, desired outcome, current context, constraints, options, trade-offs, evidence, owner, next step, and review date.
- [x] Let authors choose “guided decision brief” or “freeform outline.” Make the guided no-key flow the first demo.
- [x] Generate local copy from the author’s actual fields; never fabricate facts, measures, sources, or certainty.
- [x] Add deterministic templates for decision brief, project alignment, proposal, and incident/retrospective, but launch only the decision brief until external evidence supports expansion.
- [x] Create a migration path from schema v1; do not silently reinterpret old outlines.
- [x] Build golden tests with unrelated topics and assert semantic variation, field coverage, stable ordering, and absence of unsupported claims.

**Done when:** two unrelated briefs no longer receive the same generic narrative with only a changed title.

### P1.2 Make narrative quality inspectable

- [x] Implement `storyboard doctor <outline>` as a deterministic engine shared by CLI, browser, and API.
- [x] Diagnose missing decision, unclear audience, repeated points, unsupported factual claims, absent trade-offs, weak slide-to-slide progression, excessive copy, missing owner, and missing next action.
- [x] Explain every finding with location, severity, rationale, and a concrete author action. Never hide reasoning behind a single opaque score.
- [x] Add an in-browser story map showing each slide’s role in the arc and how it connects to the next slide.
- [x] Let the user accept, ignore with a reason, or manually resolve a finding. AI may suggest wording only when explicitly enabled.
- [x] Export Doctor results as stable JSON and readable Markdown for CI and code review.

**Done when:** the same outline produces the same actionable report offline, in the browser, CLI, and API.

### P1.3 Produce a portable Narrative Receipt

- [x] Define a versioned receipt containing outline digest, template/schema version, planner/provider, provider warning, author edits, Doctor findings and dispositions, source coverage, unresolved gaps, renderer version, fixture/viewer status, and output digest.
- [x] Embed a short provenance summary in PowerPoint notes or document properties without polluting the visible deck.
- [x] Export `deck.pptx`, `deck.story.json`, and `deck.receipt.json` together through an optional local bundle.
- [x] Add `storyboard verify <receipt>` to validate structure, hashes, and internal references. State clearly that integrity does not prove factual truth.
- [x] Add `storyboard diff old.story.json new.story.json` for readable changes to decisions, claims, evidence, sequence, and ownership.
- [x] Keep receipts local and deterministic; signing is deferred until real organizational demand exists.

**Done when:** a reviewer can see what changed, what is sourced, what remains unresolved, and which tool version created the deck without opening private source material.

---

## P2 — Make the output genuinely presentation-grade

**Outcome:** decision decks are visually useful, semantically correct, and still natively editable.

### P2.1 Give every block a real semantic model

- [x] Replace the universal three-bullet payload with typed blocks: comparison sides and criteria, decision/options/rationale, timeline steps and owners, metric/value/context/source, process steps, quote/evidence, table, and standard narrative.
- [x] Keep block limits explicit and validate them before rendering; provide a v1 compatibility adapter.
- [x] Render meaningful native PowerPoint structures for every supported block instead of restyling the same bullet list.
- [x] Add block-specific authoring controls and accessible plain-text fallbacks in the browser.
- [x] Add structural, screenshot, overflow, and real-viewer fixtures for every block in dark and light themes.

**Done when:** a comparison, metric, timeline, and decision are different data contracts and remain editable as the expected PowerPoint elements.

### P2.2 Add evidence-aware native visuals

- [x] Support local CSV/JSON data for a bounded set of native bar, line, and donut charts with editable labels and an explicit source note.
- [x] Support native tables with row/column limits, wrapping checks, and accessible text export.
- [x] Support local PNG/JPEG/SVG assets through the existing manifest, checksum, license, attribution, and alt-text contract; never fetch remote URLs implicitly.
- [x] Show asset and data provenance in the evidence panel and Narrative Receipt.
- [x] Reject unreadable, unlicensed, oversized, missing, or checksum-mismatched assets with a precise recovery message.
- [x] Keep generative image providers outside the core; evaluate them later as explicit optional adapters only.

**Done when:** the canonical decision brief can include one sourced chart or local visual without weakening editability, privacy, or reproducibility.

### P2.3 Make preview and export share one layout contract

- [x] Define a renderer-neutral layout specification for safe areas, typography, tokens, block geometry, overflow behavior, and font fallbacks.
- [x] Drive the HTML preview and PowerPoint renderer from the same layout tokens instead of maintaining visual intent in separate hand-written implementations.
- [x] Replace compact text-field cards with a zoomable 16:9 editing surface plus an outline/list mode for small screens.
- [x] Add overflow indicators before export and offer deterministic fixes such as shorten, split, or choose another supported layout.
- [x] Make `themes/storyboard-tokens.json` a validated runtime input with contrast and fallback checks; add a constrained local brand-kit workflow.
- [x] Publish the exact parity limits for browser, PowerPoint, LibreOffice, Keynote import, and Google Slides import.

**Done when:** fixture text, block role, ordering, and major geometry match between preview and exported deck within documented tolerances.

### P2.4 Complete the evidence workflow

- [x] Expose all supported sources per slide, including label, excerpt/evidence, owner, URL or local reference, checked date, and optional license.
- [x] Add an evidence coverage view for claims and slides; do not auto-mark a claim as verified because a URL exists.
- [x] Support a dedicated appendix/citations slide generated from author-approved entries while preserving native notes.
- [x] Preserve sources through JSON, Markdown, copy/duplicate, reorder, import/export, Doctor, Receipt, and schema migration.
- [x] Add malicious/invalid URL, long evidence, Unicode, and missing-owner fixtures.

**Done when:** authors can trace every material claim or deliberately mark it unresolved without losing information during export.

---

## P3 — Join existing workflows without losing focus

**Outcome:** reviewed stories enter and leave Storyboard Studio through useful, stable interfaces.

### P3.1 Turn interchange experiments into supported commands

- [x] Promote deterministic Markdown import/export into `storyboard import` and `storyboard export`, with sources, notes, typed blocks, and clear unsupported-construct errors.
- [x] Add paste/import for `.md` and `.txt` source material locally; preserve source boundaries and let the author map excerpts to claims.
- [x] Evaluate `.docx` and text-based `.pdf` ingestion only after the Markdown path has real users and a privacy/threat model.
- [x] Publish JSON Schema, OpenAPI examples, migrations, and compatibility promises from the same canonical models.
- [x] Add a GitHub Action that diagnoses and renders a reviewed story file into a release/PR artifact without network providers.

**Done when:** a team can review a story diff in Git and regenerate the same deck class locally or in CI.

### P3.2 Add provider choice as adapters, not product identity

- [x] Define a small provider interface with capabilities, network boundary, cost/retention disclosure, structured-output support, timeout, and deterministic fallback behavior.
- [x] Keep Gemini as one adapter; add one OpenAI-compatible adapter that can point to a local Ollama/LM Studio endpoint only after conformance tests exist.
- [x] Show the selected provider, model, network status, and fallback reason before and after generation.
- [x] Never send local files, evidence, or assets to a provider unless the user explicitly selects them for that request.
- [x] Do not add providers simply to increase a feature count; require a maintainer, tests, policy documentation, and a supported-state matrix.

**Done when:** provider changes do not alter the core story, Doctor, Receipt, or renderer contracts.

### P3.3 Expose a narrow agent/developer surface

- [ ] Add an optional MCP or tool server only for stable actions: create a structured draft, diagnose, diff, render, and verify.
- [ ] Return machine-readable unsupported states and capability metadata; never imply that an agent verified factual truth.
- [ ] Provide three complete examples: local CLI, HTTP API, and agent/tool integration using the same golden decision brief.
- [ ] Publish rate, size, retention, and filesystem boundaries for self-hosted use.
- [ ] Keep the browser studio the canonical review surface; automated callers must not bypass schema and evidence warnings.

**Done when:** an external tool can generate a reviewable artifact without forking internal modules or weakening user control.

---

## P4 — Turn proof into an ethical GitHub growth loop

**Outcome:** useful releases create artifacts worth sharing and contribution opportunities worth completing.

### P4.1 Replace proxy research with real evidence

- [ ] Run 10 consented first-success sessions across the primary audience; record only timing, friction, outcome, and anonymized quotes with permission.
- [ ] Observe at least 5 real decision briefs from start to export without collecting private content.
- [ ] Publish what failed as well as what worked: setup abandonment, generic output, Doctor false positives, evidence friction, and viewer mismatches.
- [ ] Use findings to choose the second template; do not expand from synthetic personas alone.
- [ ] Revisit the product thesis if users value generic generation more than defensible decision narratives.

**Done when:** roadmap priorities cite observed behavior rather than only maintainer intuition or synthetic walkthroughs.

### P4.2 Publish a benchmark people can reproduce

- [ ] Create 10 synthetic briefs with expected story roles, evidence gaps, copy-density risks, and viewer constraints.
- [ ] Evaluate content, design, and coherence with published criteria inspired by PPTAgent/PPTEval, plus editability, provenance, privacy, and reproducibility.
- [ ] Run the benchmark on the no-key planner and optional provider path; publish raw outputs and known limitations.
- [ ] Track regressions release to release rather than claiming subjective “amazing” quality.
- [ ] Invite external compatibility and rubric improvements through bounded issues.

**Done when:** anyone can reproduce the claims from fixtures and inspect failures, not just watch a polished demo.

### P4.3 Convert documentation into contribution

- [ ] Turn every item in `docs/GOOD_FIRST_ISSUES.md` into a real labeled GitHub issue with scope, files, fixtures, acceptance criteria, and maintainer availability.
- [ ] Pin a “Start here” issue that offers one user path and one contributor path; link the live demo, golden fixture, architecture map, and current release goal.
- [ ] Add a template/fixture contribution command that validates privacy, license, schema, rendering, and attribution before a pull request.
- [ ] Celebrate shipped contributors in release notes and the showcase; do not use contribution bait or automated star requests.
- [ ] Open Discussions only when there is capacity to answer consistently.

**Done when:** an outside contributor can find, implement, verify, and submit a useful change without a private design conversation.

### P4.4 Launch where the proof is relevant

- [ ] Prepare separate launch narratives for privacy-sensitive authors, Python/PowerPoint developers, local-first/self-hosted users, and agent-tool builders.
- [ ] Launch only after P0 and the first P1 Doctor/Receipt workflow are public; broad promotion of v0.2 would advertise a generic result.
- [ ] Share the reproducible artifact—not a star request—with relevant communities such as Python, local-first/self-hosted, PowerPoint automation, Show HN, and presentation-design communities while following each community’s rules.
- [ ] Create release posts around concrete improvements: “diagnose a decision deck offline,” “native sourced charts,” and “review PowerPoint stories in Git.”
- [ ] Ask users for one of three high-signal actions: try the golden brief, report a viewer result, or contribute a synthetic template.
- [ ] Review activation, repeat use, issue quality, and external contributions two weeks after each launch before adding more scope.

**Done when:** attention converts into completed workflows, useful reports, templates, or code—not only a temporary traffic spike.

---

## Release sequence

| Release | Promise | Required scope |
| --- | --- | --- |
| **v0.3 — Narrative Compiler** | Diagnose a private decision story locally, fix it, and export a receipt-backed editable deck | P0 complete; P1.1–P1.3 complete; one-command install; real demo; current-source visual CI |
| **v0.4 — Evidence & Native Visuals** | Carry typed evidence, native data visuals, and faithful block semantics into PowerPoint | P2.1, P2.2, P2.4; three golden decks; full evidence preservation |
| **v0.5 — Preview & Workflow Interop** | Trust what you see and regenerate it from Markdown/Git/CI | P2.3; P3.1; cross-platform clean-install and viewer matrix |
| **v1.0 — Proven Decision-Deck Workflow** | A stable, documented, externally validated local-first contract | 10 user sessions; 5 real workflows; benchmark; schema/API compatibility; artifact provenance; no unresolved P0/P1 defects |

Provider adapters, MCP, document ingestion, and desktop packaging are candidates for v0.5+ only when the core workflow and maintainer capacity can support them.

## 30 / 60 / 90-day execution plan

### Days 1–30: truth, install, and product hook

1. Complete P0.1 and fix clean-wheel verification.
2. Add browser and current-source visual regression contracts.
3. Ship the guided decision schema, Narrative Doctor v1, and one real motion demo.
4. Run the first five consented usability sessions before promoting the release.
5. Release v0.3 only when a stranger can complete the golden workflow unaided.

### Days 31–60: presentation quality and evidence

1. Replace generic block payloads with typed semantics.
2. Build the complete evidence editor and Narrative Receipt verification.
3. Add one native sourced chart, table, and local image path.
4. Publish three reproducible golden decks and the first benchmark report.
5. Run the remaining five user sessions and choose the next template from observed demand.

### Days 61–90: interop, contributors, and launch

1. Ship preview/export parity and supported Markdown/Git workflow.
2. Convert the contribution queue into real issues and mentor the first external changes.
3. Add one provider-neutral local adapter only if core conformance tests are stable.
4. Publish v0.4/v0.5 proof assets and launch to relevant communities with reproducible artifacts.
5. Decide the v1 scope from activation, repeat use, user outcomes, and maintenance load.

## Explicit non-goals through v1

- A collaborative cloud workspace, account system, deck database, or default telemetry.
- A broad “generate anything” competitor to Presenton, Gamma, Canva, or Beautiful.ai.
- Dozens of providers, templates, themes, or layouts without fixtures and maintainers.
- Autonomous web research presented as factual verification.
- Arbitrary PowerPoint template reverse engineering before the constrained token/brand workflow is dependable.
- Image-first slides that flatten text and data into screenshots while claiming native editability.
- Pixel-perfect parity with every Office feature, animation, transition, or viewer.
- Mobile slide design as a primary editing workflow; mobile must review and make small fixes well.
- Star popups, forced GitHub OAuth, telemetry, spam launches, or promises of virality.

## Decision rules for new ideas

Accept a feature only when it answers all five questions:

1. Which decision-deck failure does it fix?
2. Can it work locally or expose its network boundary clearly?
3. Does it preserve native ownership and evidence provenance?
4. Can it be proven with a fixture, browser test, viewer result, or user observation?
5. Is there a maintainer and a migration/support story?

If the answer is “it makes the feature list look competitive,” defer it.

## Research references

- [Presenton](https://github.com/presenton/presenton) — broad self-hosted/desktop AI presentation competitor and the reason not to compete on provider count.
- [PPTAgent](https://github.com/icip-cas/PPTAgent) — two-stage presentation workflow and content/design/coherence evaluation framing.
- [Slidev](https://github.com/slidevjs/slidev) — evidence that a sharp audience, portable source, live preview, and ecosystem can build durable adoption.
- [PptxGenJS](https://github.com/gitbrent/PptxGenJS) and [python-pptx](https://github.com/scanny/python-pptx) — mature generation layers Storyboard Studio should compose with rather than imitate.
- [GitHub repository customization](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository) — README, topics, and social-preview discovery surfaces.
- [GitHub community profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories) — contribution readiness and public health signals.

---

## Next three issues to open

1. **P0: make the installed wheel run the complete studio outside the checkout.**
2. **P1: define decision-story schema v2 and a deterministic Narrative Doctor report.**
3. **P0: add browser first-success and current-source visual regression tests.**

Do these before adding another AI provider, theme, or decorative layout.
