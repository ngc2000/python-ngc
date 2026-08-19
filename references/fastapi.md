# Treat FastAPI's OpenAPI Schema as a Product

Read this reference only when FastAPI is selected. Apply these defaults to new APIs; do not rewrite
established paths, envelopes, operation IDs, or schemas without an authorized compatibility migration.

## Contents

- [Contract layout](#contract-layout)
- [Request identity and correlation](#request-identity-and-correlation)
- [Envelopes and error handling](#envelopes-and-error-handling)
- [HTTP semantics](#http-semantics)
- [OpenAPI quality](#openapi-quality)
- [Contract verification](#contract-verification)
- [Deployment boundaries](#deployment-boundaries)

## Contract Layout

- Put public contracts below `/api/v1/` with `APIRouter(prefix="/api/v1")`. Do not version health,
  metrics, static assets, or browser pages by accident.
- Introduce `/api/v2` only for an intentional incompatible contract, not ordinary additive changes.
- Group routes with `APIRouter`, stable tags, and stable unique operation IDs. Make operation IDs
  intentional before generating clients.
- Model every request, success response, and important error response. Supply summaries,
  descriptions, status codes, examples, deprecation markers, and security schemes where they help
  consumers.

## Request Identity and Correlation

- Let boundary middleware create the canonical request ID exactly once. Accept an inbound
  `X-Request-ID` only under a documented trust policy; otherwise replace it or retain it separately as
  an external correlation value. Bound its length, allow only log-safe visible characters, and reject
  or replace control characters and whitespace. A caller-supplied value is neither unique nor a
  security identity.
- Store the canonical value in request state and `contextvars`. Require the response header, JSON
  envelope when present, application logs, audit events, and approved outbound calls to carry exactly
  that value. Do not generate a late fallback while constructing a response because it can conceal
  missing middleware and create mismatched identities.
- Explicitly bind and reset correlation context when work crosses a task, executor, thread, queue, or
  process boundary. Propagate the validated ID across internal HTTP or message boundaries instead of
  copying arbitrary inbound headers. Reset context in `finally` so concurrent and later work cannot
  inherit a stale request.
- Return `X-Request-ID` on successful, validation, framework, and unhandled-error responses. Expose the
  header through CORS only when browser clients need to read it.
- Keep request IDs distinct from W3C trace context, idempotency keys, authentication identities, and
  durable operation IDs. For accepted asynchronous work, return a persistent operation or intent ID;
  the request ID correlates acceptance but is not the lifecycle identifier.

## Envelopes and Error Handling

- Use a stable success envelope such as `{request_id, status: "ok", data, meta}` and a stable error
  envelope such as
  `{request_id, status: "error", status_code, error: {code, message, details}}`.
- Preserve an established house envelope. RFC 9457 Problem Details is a valid choice for a new error
  contract, not a reason to rewrite a compatible existing API.
- Apply envelopes to JSON API responses, not mechanically to `204` responses, files, streams,
  redirects, HTML, or WebSocket frames. Correlate those protocols with headers, connection context, or
  message identifiers as appropriate.
- When the body duplicates the HTTP status, require exact equality. Prefer typed metadata models for
  pagination or other client-consumed fields rather than an unconstrained mapping.
- Keep machine-readable error codes stable. Do not leak tracebacks, credentials, internal paths, or
  secret-bearing upstream payloads.
- Apply the error convention to request validation, routing `404` and `405`, framework-raised HTTP
  errors, and unhandled `500` responses as well as route-raised errors. Register the Starlette
  `HTTPException` base when one handler must cover framework errors, and preserve headers such as
  `WWW-Authenticate`, `Retry-After`, and `Allow`.
- Give validation failures bounded structured details with safe field paths and stable codes. Omit raw
  submitted values and internal validator context by default.
- Ensure exception paths attach the request-ID header themselves when middleware ordering could bypass
  the ordinary successful-response branch.

## HTTP Semantics

- Use nouns in paths, plural collections, correct status codes, idempotent `PUT` and `DELETE`, `202`
  for accepted asynchronous work, and explicit pagination bounds.
- Require idempotency keys or an equivalent stable deduplication contract for retriable creates that
  can duplicate side effects.
- Apply bounded request, operation, and outbound deadlines. Do not allow a framework timeout to leave
  an untracked background side effect.

## OpenAPI Quality

- Construct `FastAPI` with a stable title, summary or description, tag metadata, and
  deployment-aware `servers` or `root_path` where needed. Use an explicit unversioned marker for a
  private unversioned service.
- Keep Swagger UI, ReDoc, and `/openapi.json` locations an explicit deployment policy. Disabling a UI
  is not access control; authenticate or network-restrict sensitive documentation.
- Declare reusable error response models and the `X-Request-ID` response header with FastAPI's
  `responses` metadata. Keep the documented validation status and schema aligned with the installed
  exception handlers rather than advertising FastAPI's default response accidentally.
- Do not add a generic middleware that wraps arbitrary response bodies: OpenAPI is generated from
  route declarations and cannot see that runtime transformation. Declare typed envelope models on
  JSON routes and use shared exception handlers. If a legacy wrapper must remain, derive its OpenAPI
  customization from the same models and contract-test the generated schema against runtime output.
- Returning `Response` or `JSONResponse` directly bypasses FastAPI's automatic response-model
  serialization, filtering, and validation. Return the declared typed model when possible. When a
  direct response is required, validate its payload deliberately and declare its status, media type,
  schema, and headers explicitly; `responses` metadata documents the contract but does not enforce it.
- Generate `app.openapi()` in tests. Fail on warnings, duplicate operation IDs, broken schemas, and
  unintended compatibility changes.
- Publish or diff the schema when generated clients depend on it.

## Contract Verification

- Exercise generated, accepted, malformed, and oversized request IDs. Assert the canonical value is
  identical in the response header, JSON body when applicable, logs, and a representative downstream
  boundary.
- Exercise success, validation, `404`, `405`, route-raised HTTP errors, and unhandled `500` responses.
  Assert the envelope schema, HTTP/body status agreement, request-ID header, stable error code, and
  preservation of protocol headers.
- Verify correlation isolation and cleanup under concurrent requests and across every thread, queue,
  process, or background-work handoff used by the service.
- Verify direct responses, streams, and no-content endpoints against their declared OpenAPI contracts
  without requiring an envelope where the protocol does not support one.

## Deployment Boundaries

- Configure trusted proxy headers and `root_path` only for known proxies. Do not trust forwarded
  headers from arbitrary clients.
- Do not invent authentication when it is not explicitly part of the service contract; NGC services
  commonly run behind a firewall and trusted proxy.
- Keep CORS origins explicit and validate allowed hosts. When the contract requires authentication or
  authorization, enforce it at a trusted boundary. Rate-limit abuse-sensitive endpoints at the layer
  that can reliably identify and constrain callers.
- Use FastAPI lifespan hooks for owned clients, pools, workers, and other resources. Close them on
  shutdown and keep one-off migrations outside web-process startup.
- Define liveness and readiness according to the container guidance. Keep health responses bounded and
  non-secret.
