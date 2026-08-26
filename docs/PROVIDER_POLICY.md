# Provider and enrichment policy

The local planner is the default and works without credentials. Gemini is an
explicit, optional co-writer: when enabled and configured, the brief is sent
to Google's Gemini API and the returned outline is treated as an unverified
draft. The UI identifies the provider, failures fall back to the local planner,
and no provider response or API key is persisted by Storyboard Studio.

Users are responsible for their provider account, regional availability, and
costs. Do not send confidential material to a provider without authorization.
The local checkbox is the one-click no-network path.

Images, document-to-deck conversion, and deep research are separate
experiments. They require a privacy review, an explicit consent/cost boundary,
local caching and licensing rules, source traceability, and a deterministic
fallback before they can enter the default workflow.
