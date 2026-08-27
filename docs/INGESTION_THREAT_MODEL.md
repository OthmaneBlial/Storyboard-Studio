# Local ingestion threat model

Storyboard Studio supports two deliberately narrow interchange paths:

- reviewed story Markdown (`.md` / `.markdown`) is parsed by the CLI and browser;
- local source material (`.md` / `.txt`) stays in the browser tab, and only an
  author-selected excerpt of at most 300 characters plus its line boundary is
  copied into a source entry.

Neither path fetches URLs, resolves Markdown links, runs HTML, expands includes,
executes macros, or uploads a file to a provider. Unsupported Markdown stops at
the exact line instead of being silently flattened. A mapped excerpt remains
`unresolved` until an author supplies the separate ownership, locator, date, and
review fields required by the evidence contract.

## Boundaries and abuse cases

| Risk | Current control |
| --- | --- |
| Hidden network access | Import has no fetch step and no provider call. |
| Script or HTML execution | Markdown is parsed as bounded text and JSON comments; raw HTML is unsupported. |
| Parser ambiguity | Only one title, optional subtitle, strict slide headings, typed block comments, source comments, notes, and bounded bullets are accepted. |
| Private file leakage | The full source document is kept only in the active browser tab and is not added to story JSON, Markdown, PPTX, or receipts. |
| Lost provenance | Mapped excerpts store a relative local reference with exact `#Lx-Ly` boundaries and an explicit claim id. |
| Oversized input | Browser source material is capped at 20,000 characters and mapped excerpts at 300 characters; story schemas retain their existing size limits. |
| Path traversal | Local references remain relative POSIX paths and reject parent traversal. |

## Why DOCX and PDF remain deferred

DOCX is a ZIP/XML container that can carry relationships, external links,
embedded objects, comments, and macros in neighboring formats. PDF text order
can differ from visual order and may contain actions, attachments, forms,
scripts, OCR errors, or sensitive metadata. Flattening either format would also
destroy source boundaries that the evidence workflow relies on.

The project will not add DOCX or text-PDF ingestion until all of these gates are
met:

1. at least ten consented Markdown/source-material sessions show a repeated need;
2. a documented parser sandbox, archive/decompression limits, link policy, and
   metadata-retention policy are reviewed;
3. fixtures cover malformed containers, external relationships, encrypted
   files, mixed reading order, and resource exhaustion;
4. the UI can show page/paragraph boundaries before any excerpt is mapped;
5. the implementation remains local and provider transfer stays opt-in per
   selected excerpt.

This is an evaluation and explicit deferral, not a claim of DOCX/PDF support.
