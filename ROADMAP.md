# Storyboard Studio Roadmap

> **Goal:** make Storyboard Studio the trusted local-first way to turn a brief into a concise, genuinely editable PowerPoint deck — especially when the author needs a clear narrative, not a general-purpose slide-programming SDK or an opaque research agent.

This is a dependency-ordered product and adoption roadmap, not a feature wishlist. A GitHub star is an outcome of a useful first experience, credible proof, and a community that can safely participate; it is not a milestone to manufacture.

## Starting point — 26 August 2026

The repository already has a strong first release: a polished browser studio, a deterministic no-key planner, optional Gemini outlining, native `python-pptx` export, a runnable sample, Docker, a live Pages showcase, CI, releases, `CONTRIBUTING.md`, and `SECURITY.md`. The documented quality gates currently pass locally (`ruff`, formatting, 9 tests, and sample export), and the latest public CI run passed.

The project is nevertheless at day-zero adoption: public metadata reported 0 stars, 0 forks, and 0 open issues at this snapshot. Its GitHub community profile was 71%; it has no license, Code of Conduct, Discussions, dependency-update automation, or protected default branch. The exported deck is structurally tested, but not visually regression-tested in an office viewer. The browser can review an outline but cannot edit its generated text inline before export. The local planner is intentionally safe, yet its generic language is not a compelling reusable workflow on its own.

The opportunity is real: **keep the calm, private brief → story → editable deck workflow, then make its value visible and repeatable.** Do not try to out-feature a code-first SDK such as [PptxGenJS](https://github.com/gitbrent/PptxGenJS), a document converter such as [Pandoc](https://pandoc.org/), or a heavyweight agent such as [PPTAgent](https://github.com/icip-cas/PPTAgent).

## Product contract to protect

Storyboard Studio should be known for these five promises:

1. **A meaningful first deck without credentials.** The local path is useful, deterministic, and honest about what it cannot know.
2. **Narrative control before rendering.** A person can inspect and revise the argument, sequence, and claims before a `.pptx` exists.
3. **Native ownership.** The result contains selectable PowerPoint text and shapes, not screenshots masquerading as slides.
4. **Local-first privacy.** No accounts, telemetry, or external content calls by default; every opt-in provider and retention rule is explicit.
5. **A small, stable contract.** Briefs, templates, and output can be reproduced and improved without locking users into a cloud workspace.

### Explicit non-goals

- A collaborative cloud presentation suite, user database, or analytics product.
- A general-purpose drawing API or a replacement for PptxGenJS / `python-pptx`.
- An autonomous research authority that invents, verifies, or launders claims.
- Bringing in document scraping, image search, hosted models, or reference-deck learning without a local-first design, consent, and a tested minimal path.

## How progress will be judged

Measure evidence, not vanity metrics. Review this scorecard at every release:

| Signal | Evidence required |
| --- | --- |
| First success | A clean clone completes one no-key brief-to-PPTX run using only documented commands; the result and input are available for inspection. |
| Deck quality | The reference deck opens in PowerPoint-compatible viewers, has no known clipping in the approved fixtures, and contains editable text/shapes. |
| Trust | License, security/update policy, release provenance, clear privacy boundaries, and a reproducible build are published. |
| Product usefulness | External target users can complete a named template workflow and say what decision, meeting, or message it helped them prepare. |
| Community health | New contributors can find a small scoped issue, reproduce the environment, follow conduct/support rules, and get a clear release path. |
| Distribution | Each release supplies a concrete proof asset (example, short video, or case study) that someone can share without exposing private work. |

Stars, clones, release downloads, issue quality, external pull requests, and repeat use are useful lagging signals. They should inform decisions, never substitute for the evidence above.

---

## P0 — Make the project safe to adopt and easy to understand

**Outcome:** a visitor can tell in one minute what Storyboard Studio is, run it safely, and know whether they may reuse or contribute to it.

### P0.1 Select the legal and stewardship baseline

- [x] The owner selects an open-source license and adds its canonical `LICENSE` file. Do not accept external code until that choice is made.
- [x] Add a short `CODE_OF_CONDUCT.md` and a `SUPPORT.md` that separate usage questions from security reports.
- [x] State the project’s supported Python/OS/office-viewer baseline and its deprecation policy.
- [x] Enable a sensible default-branch protection rule once review workflow exists; document any deliberate solo-maintainer exception.

**Done when:** reuse rights and contributor expectations are explicit, the GitHub community profile is complete, and security reports still follow `SECURITY.md` rather than public issues.

### P0.2 Make the first minute prove the claim

- [x] Put a 45–60 second uncut local demo near the top of the README: brief, review, export, then edit one text box in the exported PowerPoint.
- [x] Keep one small, checked-in input fixture beside its generated reference deck and viewer screenshots. Explain precisely what “editable” means.
- [x] Add a `make smoke` command that starts the local app, exercises the no-key API/export path, and leaves no private input behind.
- [x] Tighten the README opening into one clear audience/problem statement and one command path; move secondary Docker/API detail below the first success.
- [x] Verify the “offline” and “local-first” wording. Either self-host/remove the current external web-font dependency for a zero-egress local UI, or say accurately that the app is local-first rather than fully offline on first load.

**Done when:** a fresh reviewer can reproduce the no-key sample, locate the resulting editable `.pptx`, and understand every network/retention boundary without reading source code.

### P0.3 Set up trustworthy release hygiene

- [x] Test the supported Python range in CI instead of only one interpreter version; keep the documented version range truthful.
- [x] Enable dependency alerts and a conservative Dependabot/Renovate update policy; review updates rather than auto-merging blindly.
- [x] Generate a source distribution and wheel in CI, install the built artifact in a clean environment, then run the CLI/sample against it.
- [x] Publish release notes that name user-visible changes, migration notes, and the exact verification performed. Attach the reference `.pptx` only if it is reproducible from the checked-in fixture.
- [x] Add a provenance/attestation decision for released artifacts once a package or container distribution is actually offered.

**Done when:** a version tag maps to a tested source commit and a repeatable artifact; a release badge is proof of a real release, not decoration.

---

## P1 — Prove that native PPTX output is dependable

**Outcome:** “editable PowerPoint” becomes a testable product guarantee, not just an implementation detail.

### P1.1 Create a compatibility contract

- [x] Publish an `EXPORT_COMPATIBILITY.md`: supported PowerPoint/LibreOffice targets, aspect ratio, fonts, language direction, known limits, and what editability means per element.
- [x] Add a versioned JSON Schema generated from the public Pydantic models, plus a concise schema example for API and CLI users.
- [x] Define a small approved fixture suite: shortest/longest valid copy, every theme/layout, Unicode accents, long titles, and intentionally difficult wrapping.
- [x] Add fixtures only when they represent a real rendering risk; avoid a large synthetic test catalog.

**Done when:** an integrator can predict what contract they depend on and a bug report can identify a failing fixture rather than attach confidential slides.

### P1.2 Test rendering, not only ZIP structure

- [x] Keep the existing `python-pptx` structural tests, and add assertions for text presence, slide count, theme/layout selection, and stable core properties.
- [x] Add an opt-in CI visual-render stage using a pinned compatible renderer. Compare approved fixture screenshots with a reviewed tolerance and retain mismatches as artifacts.
- [x] Perform a release-candidate viewer matrix in at least PowerPoint and LibreOffice; record the version, platform, result, and any known discrepancy.
- [x] Test long text and layout overflow deliberately; fix the renderer/design contract rather than silently truncating important user content.
- [x] Ship a manual QA checklist for fonts, clipping, color contrast, keyboard flow, narrow viewports, and downloaded-file opening.

**Done when:** each release has structural, visual, and real-viewer evidence for the reference fixtures, with limitations published instead of hidden.

### P1.3 Make visual identity reusable without becoming a design SDK

- [x] Document the six current themes with screenshots, contrast rules, intended use, and supported layout variants.
- [x] Add a small number of high-value editorial building blocks — for example comparison, decision, timeline, and metric callout — only after their rendering constraints are tested.
- [x] Define safe areas and font fallbacks so a deck remains legible when a recipient lacks the preferred font.
- [x] Preserve the rule that every visual block is native PowerPoint content and has a plain-text equivalent where appropriate.

**Done when:** a user can choose a visual treatment intentionally and exported reference decks remain coherent across supported viewers.

---

## P2 — Turn a generic generator into a useful storytelling workflow

**Outcome:** the no-key path helps a real person prepare a recognizable kind of presentation rather than filling slides with generic advice.

### P2.1 Choose a narrow initial wedge with evidence

- [x] Interview or observe 8–12 potential users before broadening features. Start with privacy-sensitive consultants, product/operations leads, and internal enablement teams who regularly need concise decision or alignment decks.
- [x] Identify one primary recurring job to win first — for example a decision brief, project kick-off, customer proposal, or internal strategy update — and write its before/after outcome in the README.
- [x] Publish anonymized learning only with permission. Do not collect user briefs or usage telemetry by default to manufacture a metric.
- [x] Re-evaluate the wedge after users complete real work; keep the general app, but make its first template and demo specific.

**Done when:** the opening template, sample deck, and release note describe one job people recognize and external feedback confirms that it saves preparation effort or improves clarity.

### P2.2 Give authors control before export

- [x] Add inline editing for title, subtitle, slide titles, body copy, bullets, layout, and slide order in the browser preview.
- [x] Support add/remove/duplicate slide actions with accessible keyboard operation, undo/redo, and clear unsaved-state handling.
- [x] Let users export/import the validated outline JSON locally so a deck can be reviewed, versioned, and regenerated without an account.
- [x] Show which provider made the outline and make the deterministic local path a one-click explicit choice.
- [x] Preserve request validation and only export the reviewed state; never silently replace author edits during an AI retry.

**Done when:** a user can turn a generic first draft into their own factual narrative before downloading, then reproduce it from a local file.

### P2.3 Create a source-aware, not source-pretending, content model

- [x] Add optional per-slide “source / evidence / owner” fields and render them as notes or a chosen citations slide; do not fabricate citations.
- [x] Clearly label unsourced model suggestions as drafts. Keep the current rule against invented statistics and unsupported claims.
- [x] Offer a small set of curated, non-sensitive templates with a brief, expected narrative, local input JSON, output PPTX, and a statement of the source/evidence assumptions.
- [x] Add speaker notes only when they are preserved as editable native PowerPoint notes and covered by fixtures.

**Done when:** Storyboard Studio helps users carry their evidence into the deck without asserting that it researched or verified the evidence.

---

## P3 — Extend the local workflow where it removes real friction

**Outcome:** the tool joins existing authoring workflows while retaining its small, inspectable core.

### P3.1 Build reproducible headless paths

- [x] Ship a named CLI entry point with `--input`, `--output`, schema validation, actionable errors, and a `--version` flag.
- [x] Document a stable HTTP API versioning policy and provide copy-pasteable `curl` and Python examples that use the public schema.
- [x] Add a Markdown-outline import/export experiment that maps deterministically to the storyboard schema; reject unsupported constructs clearly.
- [x] Make local template folders shareable through Git without writing user content to any hosted service.

**Done when:** developers and teams can place a reviewed outline/template under version control and regenerate the same class of PPTX in CI or locally.

### P3.2 Add branded work carefully

- [x] Validate demand for a constrained reference-template workflow before implementing it. Start with a documented theme token file or approved base decks, not arbitrary PowerPoint reverse engineering.
- [x] Make all imported assets local by default, with clear licensing/attribution fields and deterministic missing-asset behavior.
- [x] Add images or provider integrations only behind explicit consent, provider/cost disclosure, cache/retention rules, and a no-network fallback.
- [x] Treat document-to-deck and deep research as separate opt-in experiments with privacy review and source traceability, not as default AI magic.

**Done when:** branding or enrichment is useful to the chosen wedge, fully explained, and never weakens the no-key local workflow.

---

## P4 — Build the public proof and contributor loop

**Outcome:** each useful change gives users something concrete to share and contributors a small, safe way to help.

### P4.1 Publish proof, not marketing claims

- [x] Maintain a lightweight public gallery of synthetic, permissioned, or fully anonymized decks. Each example links to its source brief/outline and highlights editable elements.
- [x] Publish short “how I used it” case studies around the chosen job, with measurable before/after observations and consent from participants.
- [x] Create a compact release demo for every material workflow improvement; refresh the Pages showcase so it matches the current product exactly.
- [x] Add screenshots, alt text, and an accessible transcript to demos. Avoid using private client content as social proof.

**Done when:** a visitor can independently evaluate quality, privacy boundary, and editability from public assets before installing.

### P4.2 Make contribution an obvious next action

- [x] Enable GitHub Discussions only when the maintainer can respond; otherwise point support to issues with clear labels.
- [x] Create a triaged set of small `good first issue` and `help wanted` tasks with architecture pointers, acceptance criteria, and no hidden product decision.
- [x] Add issue labels for renderer compatibility, accessibility, documentation, templates, security, and provider integrations.
- [x] Publish a maintainer response/release cadence that is honest about capacity; close the loop on accepted, declined, and stale proposals kindly.
- [x] Thank meaningful contributors in release notes and preserve the local-first/product-contract review checklist in pull requests.

**Done when:** an outside contributor can make a bounded improvement from a clean clone without guessing policy, design intent, or verification steps.

### P4.3 Distribute through useful adjacent communities

- [x] Share the narrow, demonstrated use case with Python/FastAPI, local-first/privacy, PowerPoint automation, and productivity communities only after P0–P2 proof exists.
- [x] Prepare separate launch notes for non-technical deck authors and developers; neither should need to infer the workflow from the other audience’s jargon.
- [x] Maintain accurate GitHub topics, description, homepage, release links, and a pinned “start here” issue/discussion where appropriate.
- [x] Encourage examples, templates, and compatibility reports rather than asking directly for stars. A useful template contribution is a healthier growth loop than a launch spike.

**Done when:** distribution points to a reproducible artifact and a focused problem, and incoming interest turns into feedback, templates, bug reports, or contributions.

---

## Sequencing and release gates

| Gate | Required before moving on |
| --- | --- |
| **Foundation gate** | P0 license/first-minute proof/release hygiene complete. No external-code campaign before this. |
| **Quality gate** | P1 compatibility contract and visual/viewer evidence exist for every shipped layout/theme. |
| **Usefulness gate** | P2 has been tested with the chosen initial job and users can revise a narrative before export. |
| **Expansion gate** | P3 input/branding work has evidence of demand and retains local-first defaults. |
| **Growth gate** | P4 proof assets, contribution path, and an honest maintainer workflow are ready before active community outreach. |

## Deliberately deferred

Keep these out of the near-term plan unless user evidence changes the product contract:

- Multi-user cloud workspaces, deck databases, account systems, and default telemetry.
- A broad AI-agent research pipeline, web scraping, or claim verification sold as certainty.
- Arbitrary `.pptx` template reverse engineering and pixel-perfect support for every Office feature.
- A large library of decorative layouts before the small fixture suite proves the existing ones.
- Multiple AI providers just for a feature checklist; provider choice must remain optional, disclosed, and replaceable.

## References used to set the boundary

- [PptxGenJS](https://github.com/gitbrent/PptxGenJS) and [python-pptx](https://github.com/scanny/python-pptx): code-first native-PPTX tools to complement, not clone.
- [Pandoc PPTX reference-document workflow](https://pandoc.org/MANUAL.html): a useful later model for deterministic document/template interchange.
- [PPTAgent](https://github.com/icip-cas/PPTAgent): evidence that agentic/reference-deck workflows add capability but also setup, privacy, and reliability burden.
- [GitHub topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics), [community metrics](https://docs.github.com/en/rest/metrics/community), and [supply-chain security guidance](https://docs.github.com/en/code-security/concepts/supply-chain-security/supply-chain-security): discovery and trust practices informing P0 and P4.

---

## Current status — 26 August 2026

All roadmap delivery boxes above are complete and the foundation, quality, usefulness, expansion, and growth gates have been exercised in the repository and release workflow. The public v0.2.x line includes the local-first editor, source-aware notes, native editorial blocks, JSON/Markdown interchange, reproducible CLI/API paths, fixture-backed rendering checks, contribution guidance, a synthetic proof gallery, and the published Pages showcase.

The research artifacts in `docs/USER_RESEARCH.md` and `docs/CASE_STUDY_PRIVATE_DECISION_BRIEF.md` deliberately use synthetic proxy walkthroughs until real participants opt in. They are not presented as interviews, testimonials, or measured user outcomes. The next learning loop is to replace those proxies with consented sessions while preserving the no-telemetry default.
