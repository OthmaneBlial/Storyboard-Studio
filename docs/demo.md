# Accessible transcript for the local workflow demo

This is the canonical, reproducible transcript for the proof recording. It uses
only the synthetic checked-in decision brief and local compiler; no API key or
network provider is required. Until the video asset is attached, treat this as
a transcript and reproduction guide—not as motion proof.

1. `make setup && make run`
2. Open `http://127.0.0.1:8000`.
3. Choose **Try a sample brief**, then select **Build decision story**.
4. Run **Narrative Doctor**. Accept the missing evidence-owner action, add the
   owner, and rerun the structural review.
5. Review the story map and five editable content frames.
6. Select **Export review bundle** and verify that the ZIP contains the native
   PPTX, versioned story, and Narrative Receipt.
7. Open `deck.pptx` and edit the title text box. The text remains selectable
   native presentation content.

For a terminal-only health check, run `make smoke`. It starts an ephemeral
local server, exercises both API endpoints, validates the downloaded ZIP
signature, and removes its temporary export before exiting.

The current showcase image is a static, privacy-safe companion to this flow. It
does not claim to be a recording or external-user evidence.
