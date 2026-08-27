# Accessible transcript for the local workflow demo

This is the accessible transcript for the canonical
[31-second uncut proof recording](assets/storyboard-demo.mp4). It uses only the
synthetic checked-in decision brief and local compiler; no API key or network
provider is required.

1. `make setup && make run`
2. Open `http://127.0.0.1:8000`.
3. Choose **Try a sample brief**, then select **Build decision story**.
4. Run **Narrative Doctor**. Accept the missing evidence-owner action, add the
   owner, and rerun the structural review.
5. Review the story map and five editable content frames.
6. Select **Export PowerPoint** and download the native PPTX.
7. Open the file in LibreOffice Impress, select the title text box, and replace
   the title with “Onboarding pilot — reviewed live.” The recording shows that
   the text remains selectable native presentation content.

For a terminal-only health check, run `make smoke`. It starts an ephemeral
local server, exercises both API endpoints, validates the downloaded ZIP
signature, and removes its temporary export before exiting.

The recording is product proof on the maintainer's machine, not external-user
evidence. The full reproducible artifact set, including a versioned story and
verified Narrative Receipt, is in the [golden gallery](../gallery/README.md).
