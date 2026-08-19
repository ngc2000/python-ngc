# Prefer HTTPX2 Only Where an Explicit HTTP Client Is Needed

Read this reference only when implementing or changing a use site that needs an explicit HTTP client.

- Do not add an HTTP client by default.
- When new code would otherwise require `import httpx`, add and write `import httpx2` instead. Do not
  mechanically replace unrelated clients or rewrite a working integration without a concrete
  requirement.
- Avoid process-wide `alias_httpx()` unless an unmodifiable integration requires the old import name.
- `requests` remains a valid separate client. Preserve working `requests` code and dependencies; do
  not migrate them solely because NGC prefers HTTPX2 for new explicit client code.
- Match sync versus async clients to the execution model. Do not run blocking sync calls on an event
  loop.
- For async services, create a shared `httpx2.AsyncClient` in the owning lifespan, inject it into
  callers, and close it on shutdown. Do not create clients in hot request loops.
- Set explicit connect, read, write, and pool timeouts plus measured connection limits.
- Bound retries to safe failures and idempotent operations. Apply backoff and jitter, honor one overall
  operation deadline, and do not retry a write that can duplicate side effects without an idempotency
  contract.
- Propagate the approved request or correlation ID. Do not forward unrelated inbound headers.
- Test ASGI applications with `httpx2.ASGITransport` and `httpx2.AsyncClient`. Manage lifespan
  separately because the transport does not trigger startup or shutdown.
- Use `httpx2.MockTransport` or dependency injection for deterministic outbound-client tests. Block
  accidental live network access in the default suite.
