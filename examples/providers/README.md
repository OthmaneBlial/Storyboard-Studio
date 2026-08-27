# Provider fixtures

`openai-compatible-response.json` is a synthetic, non-network response used by
the loopback conformance test. It contains no private brief, source, asset, or
credential. The fixture describes only the bounded `/v1/chat/completions`
response shape; it is not evidence that a particular Ollama, LM Studio, or
other compatible server supports every model or option.

Keep provider tests local and deterministic. Any server-specific addition must
preserve the transfer boundary documented in
[`docs/PROVIDER_POLICY.md`](../../docs/PROVIDER_POLICY.md).
