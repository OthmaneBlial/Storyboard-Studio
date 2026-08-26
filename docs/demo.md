# 60-second local demo

This is the canonical, reproducible demo for release notes and the README. It
uses only the checked-in example and the local planner; no API key or network
provider is required.

1. `make setup && make run`
2. Open `http://127.0.0.1:8000`.
3. Choose **Try a sample brief**, leave Gemini disabled, and select **Build my
   storyboard**.
4. Review the title slide and the three editable content frames.
5. Select **Export PowerPoint**, open the downloaded file, and edit the title
   text box. The text remains selectable native PowerPoint content.

For a terminal-only health check, run `make smoke`. It starts an ephemeral
local server, exercises both API endpoints, validates the downloaded ZIP
signature, and removes its temporary export before exiting.

The showcase image is a static, privacy-safe companion to this live flow; it
does not claim to be a recording of a user’s private presentation.
