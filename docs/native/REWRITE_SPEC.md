You are taking ownership of this repository:

https://github.com/OthmaneBlial/Storyboard-Studio

Your mission is to transform Storyboard Studio into a serious, polished, native, local-first presentation compiler built around Rust and Tauri.

Do not simply port files mechanically.

Re-architect the project properly around a reusable Rust core, a native desktop application, a powerful CLI, and a first-class PowerPoint generation engine.

The target architecture is:

```text
                 STORYBOARD STUDIO
                       │
             ┌─────────┴─────────┐
             │                   │
        Tauri Desktop           CLI
             │                   │
             └───────┬───────────┘
                     │
               storyboard-core
                     │
       ┌─────────────┼─────────────┐
       │             │             │
   narrative      layout        evidence
    compiler       engine         engine
       │             │             │
       └─────────────┼─────────────┘
                     │
                PPTX engine
                     │
                  .pptx
```

# CORE OBJECTIVE

Rewrite the current Python architecture into Rust while preserving the genuinely useful ideas already present in Storyboard Studio.

The end result should feel like a new generation of the project, not "the Python application rewritten in Rust."

The product should become:

- native
- fast
- lightweight
- local-first
- offline-capable
- cross-platform
- deterministic where possible
- scriptable
- CLI-friendly
- desktop-friendly
- easy to install
- easy to demo
- visually impressive
- technically impressive
- genuinely useful

The product should ultimately be describable as:

> A native local-first presentation compiler that turns structured ideas, briefs, Markdown and story definitions into editable PowerPoint presentations.

A stronger technical positioning is:

> A PowerPoint compiler written in Rust.

# IMPORTANT RULE

Do not retain Python as a hidden dependency just to make the migration easier.

The target product must NOT require:

- Python
- pip
- virtualenv
- python-pptx
- FastAPI
- a separate runtime

The final application should be based around compiled native binaries.

Temporary compatibility tooling is acceptable during migration, but it must not become part of the final architecture.

# RUST WORKSPACE

Create a clean Rust workspace.

A possible structure is:

```text
storyboard-studio/
├── crates/
│   ├── storyboard-core/
│   ├── storyboard-narrative/
│   ├── storyboard-layout/
│   ├── storyboard-evidence/
│   ├── storyboard-pptx/
│   ├── storyboard-model/
│   ├── storyboard-cli/
│   └── storyboard-ai/
│
├── apps/
│   └── desktop/
│       ├── src/
│       └── src-tauri/
│
├── examples/
├── gallery/
├── fixtures/
├── docs/
├── benchmarks/
├── tests/
└── website/
```

You may improve this structure if you discover a cleaner architecture.

Avoid unnecessary micro-crates.

The workspace should remain understandable.

# STORYBOARD CORE

Create a central reusable Rust library.

It should expose stable domain models for:

- Presentation
- Story
- Slide
- Block
- Text
- Heading
- Image
- Shape
- Table
- Chart
- Callout
- Quote
- Evidence
- Claim
- Citation
- Speaker note
- Theme
- Brand kit
- Layout
- Geometry
- Color
- Typography
- Metadata

Use strongly typed Rust structures.

Use serde where appropriate.

Avoid weak `HashMap<String, Value>` style architecture except for truly extensible metadata.

Provide versioned schemas where needed.

# NARRATIVE COMPILER

Rebuild and significantly improve the current narrative compiler.

The narrative compiler should turn structured inputs into coherent presentation stories.

Support inputs such as:

```text
JSON
Markdown
structured briefs
decision briefs
product briefs
strategy briefs
technical proposals
project updates
business reviews
research summaries
custom Storyboard files
```

The compiler should understand concepts such as:

- audience
- objective
- decision
- context
- problem
- evidence
- options
- trade-offs
- recommendation
- risks
- metrics
- owner
- timeline
- next action

It should create an inspectable intermediate representation before rendering.

A presentation must not be a pile of unrelated slides.

The compiler should reason about presentation progression such as:

```text
context
→ tension/problem
→ evidence
→ possible paths
→ recommendation
→ implications
→ action
```

Make the architecture extensible enough to support other story patterns.

# NARRATIVE DOCTOR

Preserve and expand the existing Narrative Doctor idea.

It should detect issues including:

- weak opening
- duplicated slides
- unsupported claims
- excessive density
- missing evidence
- unclear recommendation
- poor slide progression
- weak transitions
- missing owner
- missing next action
- inconsistent terminology
- vague titles
- slides without a purpose
- insufficient contrast between options
- overly generic AI language

Expose diagnostics through both the CLI and desktop UI.

Example:

```bash
storyboard doctor strategy.story.json
```

Output useful, actionable diagnostics rather than generic advice.

Support:

```bash
storyboard doctor file.story.json
storyboard doctor file.story.json --json
storyboard doctor file.story.json --markdown
```

# LAYOUT ENGINE

Create a real deterministic presentation layout engine in Rust.

This is a major part of the project.

The engine should reason about:

- slide dimensions
- grids
- margins
- spacing
- alignment
- typography
- text measurement
- overflow
- image placement
- aspect ratio
- columns
- cards
- charts
- tables
- titles
- footers
- speaker notes
- safe zones

Create reusable layout primitives.

Examples:

```text
Stack
Row
Column
Grid
Absolute
Padding
Margin
Align
Center
Card
Hero
Split
Sidebar
Overlay
```

Layouts should not depend on hardcoded pixel coordinates everywhere.

Create a proper geometry system.

# PPTX ENGINE

This is one of the most important technical goals.

Remove the dependency on `python-pptx`.

Implement native PowerPoint generation in Rust.

Treat PPTX as what it actually is:

```text
ZIP
└── OpenXML document structure
```

Generate the required OpenXML structure directly.

Support at minimum:

- presentations
- slides
- slide relationships
- text boxes
- paragraphs
- text styling
- shapes
- lines
- fills
- borders
- images
- tables
- simple charts
- hyperlinks
- speaker notes
- themes
- masters/layouts where appropriate
- metadata
- embedded assets

The resulting presentation must remain editable in PowerPoint.

DO NOT render each slide as a screenshot.

Text must remain text.

Shapes must remain shapes.

Images should remain image objects.

Tables should remain editable when practical.

Test compatibility with:

- Microsoft PowerPoint
- LibreOffice Impress
- Keynote where feasible
- Google Slides import where feasible

Create tests that inspect generated PPTX packages and their XML structure.

A powerful long-term ambition is to make `storyboard-pptx` reusable independently as an open-source Rust PowerPoint generation library.

Design the architecture accordingly.

# CLI

Build a first-class native CLI.

The CLI should feel polished enough to be useful without the desktop application.

Examples:

```bash
storyboard new
storyboard compile brief.json
storyboard compile brief.md
storyboard render story.json
storyboard doctor story.json
storyboard inspect story.json
storyboard verify receipt.json
storyboard diff old.story.json new.story.json
storyboard preview story.json
storyboard themes
storyboard examples
storyboard benchmark
storyboard serve
```

Useful patterns:

```bash
storyboard compile brief.md -o pitch.story.json

storyboard render pitch.story.json \
  -o pitch.pptx \
  --theme midnight

storyboard doctor pitch.story.json

storyboard build brief.md \
  --theme minimal \
  --output final.pptx
```

Support helpful errors.

Make CLI output beautiful but not noisy.

Support machine-readable output where relevant.

# TAURI DESKTOP APPLICATION

Build a polished Tauri desktop application on top of the Rust core.

Do not create an Electron-style heavyweight application.

The app should make the native/local-first philosophy visible.

The desktop product should provide an excellent flow:

```text
New project
→ input brief
→ compile story
→ inspect structure
→ edit slides
→ review diagnostics
→ preview
→ export PPTX
```

Important screens may include:

- Home
- Recent projects
- New presentation
- Brief editor
- Story map
- Slide editor
- Slide preview
- Narrative Doctor
- Evidence panel
- Theme editor
- Brand kit
- Export
- Settings
- Provider configuration

Create keyboard shortcuts.

Support drag and drop.

Support autosave.

Projects should remain local.

# UI QUALITY

The UI must become significantly better than the existing interface.

Aim for a premium creative-tool feeling.

Reference quality levels such as:

- Linear
- Raycast
- Arc
- Figma
- Framer
- Notion
- modern design tools

Do not clone them.

Use them only as a quality reference.

Prioritize:

- excellent typography
- strong spacing
- subtle transitions
- dense but understandable information
- responsive layouts
- polished empty states
- command palette
- keyboard navigation
- context menus
- excellent dark mode
- excellent light mode

Avoid generic AI SaaS aesthetics.

Avoid excessive gradients.

Avoid giant useless hero text.

Avoid glassmorphism everywhere.

# LIVE PRESENTATION PREVIEW

Create an accurate preview of the generated presentation.

The preview should use the same layout model as the PPTX engine so that the desktop preview and exported PowerPoint stay as close as possible.

Support:

- zoom
- slide navigation
- thumbnails
- fit width
- fit slide
- fullscreen
- grid overview

# THEMES

Create a serious theme system.

Ship multiple high-quality themes.

Examples:

```text
Minimal
Editorial
Midnight
Consulting
Product
Technical
Investor
Research
Mono
Swiss
Terminal
Modern
```

Each theme should be visually distinct.

Support:

- typography
- background
- palette
- spacing
- title styles
- card styles
- charts
- accent rules
- table styles

Allow users to create custom themes.

# BRAND KIT

Support importing a local brand definition.

Example:

```json
{
  "name": "Acme",
  "fonts": {},
  "colors": {},
  "logo": {},
  "presentation": {}
}
```

Allow:

```bash
storyboard render pitch.story.json --brand acme.json
```

# EVIDENCE ENGINE

Keep evidence and claims as first-class concepts.

Users should be able to associate claims with:

- URLs
- documents
- local files
- notes
- citations
- author-confirmed statements

The software must clearly distinguish between:

- presence of evidence
- verified link integrity
- author confirmation
- factual truth

Do not falsely claim that Storyboard Studio verifies truth.

# NARRATIVE RECEIPT

Preserve and improve the Narrative Receipt concept.

Generate alongside a deck:

```text
presentation.pptx
presentation.story.json
presentation.receipt.json
```

The receipt can contain:

- story hash
- presentation hash
- theme
- build version
- timestamp
- input digests
- evidence references
- diagnostics summary
- renderer version

Allow:

```bash
storyboard verify presentation.receipt.json
```

# OPTIONAL AI

AI should remain optional.

The program must remain valuable without any AI model.

Create a provider abstraction.

Possible providers:

- OpenAI-compatible endpoints
- Gemini
- local Ollama
- LM Studio
- future adapters

AI may help with:

- generating drafts
- suggesting story structures
- rewriting slide copy
- compressing text
- generating speaker notes
- improving titles
- identifying weak reasoning

But the deterministic presentation compiler should remain independent.

Users should always be aware when data leaves their computer.

# PERFORMANCE

Benchmark the project.

Track:

- startup time
- compile time
- render time
- PPTX generation
- memory usage
- binary size
- large-deck performance

Create benchmarks for:

```text
10 slides
25 slides
50 slides
100 slides
250 slides
```

Publish real numbers.

Do not fabricate benchmark results.

# WEBSITE

Completely improve the public website.

The website must sell the project immediately.

It should explain in seconds:

1. what Storyboard Studio is
2. why it exists
3. why it is different
4. how it works
5. what the output looks like

The homepage should feature actual presentations generated by the software.

Potential structure:

```text
Hero
↓
interactive generated presentation
↓
brief → compiler → editable PPTX
↓
gallery
↓
native/local-first advantages
↓
CLI demo
↓
Narrative Doctor
↓
themes
↓
architecture
↓
benchmarks
↓
install
↓
GitHub
```

Create a highly polished responsive website.

# WEBSITE HERO

Potential messaging:

```text
Storyboard Studio

The native presentation compiler.

Turn briefs, Markdown and structured ideas
into editable PowerPoint decks.

Built in Rust.
Runs locally.
Exports real PPTX.
```

Test alternative messaging and use whichever best describes the actual product.

Never make unsupported claims.

# PRESENTATION GALLERY

The repository and website need a large, impressive gallery.

Generate many REAL presentations using Storyboard Studio itself.

Create examples such as:

```text
startup pitch deck
product roadmap
AI strategy
engineering architecture
quarterly business review
consulting recommendation
market analysis
launch plan
incident postmortem
design review
research report
investment memo
sales proposal
technical RFC
project kickoff
executive briefing
company strategy
competitive analysis
security review
open source project overview
```

Each example should include when useful:

```text
input brief
story JSON
PPTX
preview images
receipt
diagnostic result
```

Organize them cleanly.

For example:

```text
gallery/
├── startup-pitch/
├── product-roadmap/
├── strategy/
├── consulting/
├── technical/
├── research/
└── executive/
```

# GENERATED PPTX EXAMPLES

Create enough examples that a visitor can assess output quality without installing the application.

Create representative decks with different:

- themes
- slide counts
- industries
- layout types
- data densities
- narrative structures

Use synthetic/non-confidential content.

Never imply that synthetic examples are real client work.

# SCREENSHOTS

Generate polished screenshots showing:

- dashboard
- editor
- Story Map
- Narrative Doctor
- theme selection
- live preview
- export
- CLI
- final PowerPoint

Use them throughout the README and website.

# VIDEO DEMO

Create a reproducible demo workflow for a product video.

Target a short demo showing:

```text
brief.md
↓
storyboard build brief.md
↓
Story Map
↓
Narrative Doctor
↓
theme selection
↓
live preview
↓
export
↓
opening editable PowerPoint
```

Target:

- approximately 30–60 second short demo
- optional longer 2–3 minute walkthrough

Where automation is possible, provide scripts for capturing or reproducing the demo.

Store appropriate demo assets in the repository.

Do not commit huge unnecessary video files if GitHub-hosted release assets or other storage would be more appropriate.

# README

Completely redesign the README.

It must be exceptionally clean and convincing.

The top of the README should immediately communicate the product.

Potential structure:

```text
logo
headline
one-line explanation
demo GIF/video
badges

Why Storyboard Studio?

screenshots

30-second example

Installation

CLI

Desktop

Gallery

How it works

Architecture

PPTX engine

Themes

Narrative Doctor

Evidence

Benchmarks

Roadmap

Contributing
```

Avoid walls of text.

Use strong visuals.

Use comparison diagrams where useful.

Keep technical details below the product explanation.

# README VISUALS

Include:

- architecture diagram
- terminal recording or GIF
- app screenshots
- generated presentation screenshots
- example deck montage
- theme gallery
- compiler flow

Keep images optimized for GitHub.

# INSTALLATION

Aim toward extremely simple installation.

Desired eventual experience:

macOS:

```bash
brew install storyboard-studio
```

Cargo:

```bash
cargo install storyboard-studio
```

Or downloadable binaries from GitHub Releases.

Desktop:

```text
macOS .dmg
Windows .msi/.exe
Linux .AppImage/.deb
```

Do not publish to registries unless credentials and release permissions are properly available.

Prepare everything needed for releases.

# CROSS PLATFORM

Target:

- macOS Intel
- macOS Apple Silicon
- Windows x64
- Linux x64

Add other architectures where practical.

# TESTING

Create serious automated tests.

Test:

- narrative compilation
- schemas
- invalid input
- layout determinism
- overflow
- XML generation
- PPTX archive integrity
- relationships
- images
- fonts
- notes
- tables
- charts
- CLI
- desktop commands
- receipt verification

Create golden fixtures.

Avoid giant fragile snapshot files where more semantic tests are possible.

# PPTX VALIDATION

Generated decks must not merely exist.

Validate them.

At minimum:

- archive opens
- required OpenXML files exist
- XML is well formed
- relationships resolve
- slide count matches
- referenced media exists
- text content can be recovered
- no dangling internal relationships

Where practical, include manual compatibility validation documentation for PowerPoint and LibreOffice.

# BENCHMARKS

Add a benchmark section to the README and website once genuine measurements exist.

Show things like:

```text
startup
10-slide render
50-slide render
100-slide render
memory
binary size
```

Include hardware and operating system.

Never create invented numbers.

# OPEN SOURCE QUALITY

Make the repository feel like a serious open-source project.

Improve:

- CONTRIBUTING.md
- ARCHITECTURE.md
- ROADMAP.md
- SECURITY.md
- CHANGELOG.md
- issue templates
- PR template
- development instructions

Create useful starter issues where appropriate.

# ROADMAP

Create an ambitious but realistic roadmap.

Potential phases:

```text
0.3 — Rust core
0.4 — Native PPTX renderer
0.5 — Tauri desktop
0.6 — themes + brand kits
0.7 — advanced charts
0.8 — plugin architecture
0.9 — compatibility stabilization
1.0 — stable file format and renderer
```

Only mark features as completed when they genuinely work.

# PROJECT FILE FORMAT

Design a stable Storyboard project format.

Potential extensions:

```text
.story.json
.story.md
.storyboard
```

Document versioning and migration rules.

The format should remain inspectable and friendly to Git.

# FUTURE PLUGIN SYSTEM

Design the core so future extensions can support things such as:

- new renderers
- new input formats
- themes
- narrative strategies
- AI providers
- asset providers
- export formats

Do not over-engineer the plugin implementation now.

Keep boundaries clean enough to support it later.

# POSSIBLE FUTURE EXPORTS

Keep architecture flexible enough for future support of:

```text
PPTX
PDF
HTML presentation
SVG slides
PNG previews
Markdown
JSON
```

PPTX remains the main priority.

# SECURITY

Continue the project's local-first philosophy.

Be careful with:

- path traversal
- ZIP generation
- ZIP bombs on imports
- untrusted XML
- malicious images
- external URLs
- local file access
- shell commands
- AI provider credentials

Never expose secrets in logs or generated files.

# MIGRATION STRATEGY

Study the current repository carefully before removing anything.

Create a migration map of existing functionality.

Classify features as:

```text
preserve
rewrite
redesign
remove
defer
```

Use current tests and example outputs as behavioral references where useful.

Do not delete the working implementation until the corresponding Rust path has sufficient test coverage.

However, do not preserve poor architectural decisions merely for backwards compatibility.

# CODE QUALITY

Prefer:

- clear Rust
- strong types
- small cohesive modules
- explicit errors
- deterministic behavior
- useful documentation

Avoid:

- enormous files
- unnecessary abstractions
- premature generic frameworks
- clone-heavy code
- panics in normal user flows
- `unwrap()` throughout production paths
- placeholder modules that claim functionality without implementing it

Run:

```bash
cargo fmt
cargo clippy
cargo test
```

frequently.

Keep the repository buildable.

# GITHUB

Work directly on the GitHub repository owned by:

```text
OthmaneBlial
```

If the migration is being done in the existing repository, preserve its Git history.

If a new repository becomes technically necessary, use the owner's GitHub account and document why.

Do not create random alternative repositories unless justified.

# COMMITS

Make frequent, meaningful commits.

Examples:

```text
feat(core): introduce typed presentation model
feat(pptx): generate basic OpenXML slide package
feat(layout): add deterministic grid engine
feat(cli): add compile and render commands
feat(desktop): scaffold Tauri editor
feat(gallery): add generated strategy deck
docs(readme): redesign project landing page
```

Push completed, coherent work to `main` when repository permissions and workflow allow it.

Do not leave major completed work only in the local working tree.

Before pushing:

```bash
cargo fmt --check
cargo clippy
cargo test
```

plus relevant frontend checks.

# AUTONOMOUS WORKING MODE

Work continuously on the project.

Do not stop after creating scaffolding.

Do not stop after creating TODO comments.

Do not stop after writing a roadmap.

Implement real functionality.

When one task is complete, identify the next highest-value task and continue.

Constantly ask:

```text
What makes the product more usable?
What makes the architecture stronger?
What makes the output more impressive?
What makes the repository easier to trust?
What makes the README easier to understand?
What produces an actual visible result?
```

Prioritize working software over speculative documentation.

# ITERATION LOOP

Repeat:

```text
1. inspect current state
2. select highest-value improvement
3. implement
4. test
5. generate real artifact
6. inspect result
7. improve
8. document
9. commit
10. push
11. continue
```

Do this repeatedly.

# DEFINITION OF SUCCESS

The rewrite should eventually reach a state where a new visitor can:

```bash
git clone ...
cargo build --release
```

or download a release,

then:

```bash
storyboard build examples/startup-pitch.md -o pitch.pptx
```

and receive a professional, editable PowerPoint presentation generated completely through the native Rust stack.

The same engine should power the Tauri desktop application.

The GitHub repository should immediately demonstrate that this works through:

- beautiful README
- screenshots
- demo video
- generated PPTX files
- gallery
- CLI examples
- architecture diagrams
- benchmarks
- tests
- downloadable binaries

The project should look technically ambitious while remaining genuinely useful.

The final impression should be:

> "They built an actual presentation compiler in Rust."

Not:

> "They wrapped another AI slide generator."

Start by deeply inspecting the existing repository and mapping its current architecture and behaviors.

Then begin the Rust migration in incremental, tested, working stages.

Do not ask me what to work on next unless you are genuinely blocked by an external decision or credential.

Otherwise continue improving, testing, committing and pushing.