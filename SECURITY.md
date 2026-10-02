# Security

Compilation, Doctor, layout, preview and PPTX export run locally without network
requests. The optional draft assistant sends only explicitly approved text to the
configured endpoint. Keys are never stored in projects or receipts. No telemetry,
accounts, automatic source fetching or embedded scripts are required.

Inputs are bounded and typed. Unknown versions/fields fail. Image imports reject
absolute/parent paths, escaping symlinks, unsupported formats and excessive sizes
or dimensions. Imported/exported images use immutable content-addressed sidecars.
Native dialogs and real drop events grant desktop import access; arbitrary frontend
paths do not. Saves are atomic and bundle replacement retains rollback protection.

The PPTX validator bounds ZIP entry/expanded sizes, rejects traversal/duplicates
and XML DTDs, and checks relationships and namespaces. It does not establish that
third-party office software has no vulnerabilities. Evidence references remain
metadata; author confirmation is distinct from factual truth. Receipts are unsigned
consistency records and cannot authenticate a wholly replaced bundle.

Provider requests require approval, use HTTPS except on loopback, prohibit embedded
credentials/query strings, disable redirects and proxies, set timeouts and bound
responses. Provider errors do not echo keys or response bodies. Generated drafts
are untrusted authored input; review them before compiling or using their claims.

Report a vulnerability privately through the repository's GitHub security advisory
flow. Include the native version, platform, a minimal synthetic reproduction and
impact. Do not put credentials or private decks in public issues.
