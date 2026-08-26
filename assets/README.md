# Local asset manifest

Storyboard Studio currently renders text and shapes only. This folder is the
safe extension point for a future reference-template or image workflow:

- keep files local and commit only synthetic or permissioned assets;
- list every file in `manifest.json` with a SHA-256 checksum, license, and
  attribution;
- reject URLs, missing files, and checksum mismatches before rendering;
- never download or cache a remote asset implicitly.

Validate the manifest with `make validate-assets`. An empty manifest is valid
and is the current default because the core renderer has no image dependency.
