# Browser and Python contract parity

The canonical public models live in `storyboard_studio.schemas`. The editor
also validates before it sends or exports a presentation, so a browser-side
validator must reject the same unsafe shape instead of silently accepting data
that the API will refuse later.

`tests/test_contract_parity.py` runs both validators against the checked-in
product, semantic-block, evidence, native-visual, and decision-story fixtures,
then applies representative mutations for missing or non-sequential slide
numbers, private IPv6 URLs, unsafe asset paths, mismatched asset media types,
non-ASCII claim IDs, oversized local references, and story-envelope mistakes.
The test invokes the repository's `validation.js` in a clean Node VM and
compares only the acceptance decision; error wording remains an interface for
the editor and API respectively.

This is a curated regression corpus, not proof that every possible JSON value
has been exhaustively enumerated. New public fields or constraints must add a
fixture or mutation here and update the canonical Pydantic model first.
