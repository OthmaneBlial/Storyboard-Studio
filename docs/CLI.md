# Native CLI

`storyboard --help` and `storyboard <command> --help` describe current options.

| Command | Result |
| --- | --- |
| `new brief.md` | Editable synthetic starting brief |
| `compile input -o deck.story.json` | Strict native story |
| `compile input -o deck.story.md` | Lossless versioned JSON fence in Markdown |
| `build input -o deck.pptx` / `render story -o deck.pptx` | Editable deck, story and receipt |
| `doctor input --json` / `--markdown` | Stable actionable local diagnostics |
| `inspect input --layout` | Validated story or shared geometry |
| `verify deck.receipt.json` | Hash, package, theme, story binding and diagnostics checks |
| `validate deck.pptx --json` | Bounded ZIP/XML/relationship/text validation |
| `diff old new --json` | Stable ID/content/order comparison |
| `preview input -o preview.html` | Standalone local navigation/grid preview |
| `preview input --svg --slide 2 -o slide.svg` | One shared-layout SVG |
| `serve input --port 4318` | GET-only preview on `127.0.0.1` |
| `themes --json`, `examples`, `schema` | Built-ins and inspectable contract |
| `benchmark --iterations 5 -o result.json` | Real compile/layout/PPTX timings for 10–250 slides |

Inputs accept authored Markdown, typed story/brief JSON and desktop `.storyboard`
projects. Unknown formats/versions fail. Custom projects carry their full theme;
`--theme` selects a built-in override, and `--brand examples/brand/kit.json` imports
local brand typography/palette/logo. Export directories must already exist.
Files are not overwritten without `--force`; receipt verification is not truth or
authorship verification. Evidence URLs and file references are not followed.

Optional drafting is an explicit request. Set a key outside the command line if
needed; it is read from `STORYBOARD_API_KEY` or the named `--api-key-env` variable:

```bash
storyboard draft brief.md \
  --endpoint http://127.0.0.1:11434/v1/chat/completions \
  --model YOUR_LOCAL_MODEL --allow-send -o draft.md
```

Use `--provider gemini` with the full `.../models/MODEL:generateContent` endpoint.
The exact input text (≤64 KiB) is sent with drafting instructions. No images or
project history are attached. No request occurs without `--allow-send`. Review
returned Markdown before compiling, especially factual claims and ownership.
