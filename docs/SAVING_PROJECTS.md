# Save the project separately from the presentation

**Save project JSON** preserves the editable story: decision brief, slide order,
theme, native block data, source excerpts and metadata, author edits and Doctor
finding dispositions. It downloads a `.story.json` file locally without sending
the save to a provider. Asset manifests reference separate local files; the JSON
alone does not contain those files. Keep them with the project until the portable
asset-bundle workflow is available.

The browser can request a download but cannot prove that you kept it. Check the
file in your Downloads folder and use **I saved this project version** to confirm.
If the download was cancelled, do not confirm. Any subsequent edit makes the
project unsaved again; the confirmation applies only to the exact requested
snapshot. Open a saved file with **Open saved project** on the initial screen or
**Import story** in the editor. Invalid imports leave the current project intact.

**Export PowerPoint** produces a presentation snapshot. It does not save the
complete project or clear its unsaved status. Edits made during export stay in
the editor and are not retroactively included in the downloaded snapshot. If the
presentation changes during preflight, repeat the export for the new version.
A review bundle contains a story and integrity receipt for its exported snapshot;
requesting that download is not proof of a successful save either.

Undo/Redo keeps up to 50 complete story snapshots, including evidence and Doctor
choices. History is in memory only and is not included in project files. Imported
projects preserve their theme and decision metadata. Uncompiled changes in the
brief form are not in the compiled story; build the story again before saving
those changes. Building a new story starts a fresh edit history.

There is no automatic localStorage, IndexedDB or account recovery. Closing a tab,
crashing the browser or reloading can lose unsaved work; a browser unload warning
is a reminder, not a backup guarantee. Tabs are independent. Downloaded files
remain on your disk until you remove them; the server's 24-hour expiry affects
only its temporary export copies.
