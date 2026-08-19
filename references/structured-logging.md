# Structured Logging

Read this reference for logging in a deployable application and whenever structured application or
audit logs are selected. For a new deployable application, use `colorlog` for the human stdout sink and
`structlog` for structured event data and JSON serialization. Preserve a sound established logging API
and output contract during incremental adoption.

## Contents

- [Choose ownership and output](#choose-ownership-and-output)
- [Choose the default package](#choose-the-default-package)
- [Set useful default levels](#set-useful-default-levels)
- [Compress closed segments with Zstandard](#compress-closed-segments-with-zstandard)
- [Use a stable event schema](#use-a-stable-event-schema)
- [Propagate context safely](#propagate-context-safely)
- [Redact at the serialization boundary](#redact-at-the-serialization-boundary)
- [Control cardinality and volume](#control-cardinality-and-volume)
- [Keep delivery non-blocking](#keep-delivery-non-blocking)
- [Separate audit events from state](#separate-audit-events-from-state)
- [Test the logging contract](#test-the-logging-contract)

## Choose Ownership and Output

- Applications own logging configuration. Reusable libraries must not configure the root logger, add
  global handlers, select a JSON formatter, or emit logs during import. Libraries emit normal records
  through `logging.getLogger(__name__)`; the application owns routing and serialization.
- Configure two application-owned sinks by default for a deployable service:
    - stdout/stderr at `INFO` using `colorlog`, for local terminals, Docker logs, and immediate operator
      feedback;
    - JSON Lines at `DEBUG` under `data/logs/<service>.jsonl`, for detailed structured diagnosis.
- Make the colored line informative rather than minimal. Include an RFC 3339 UTC timestamp with
  milliseconds, padded level, logger name, module and line, request ID and stable event name when
  present, and the human message. A representative shape is:

    ```text
    2026-08-19T14:23:18.417Z INFO     example.api routes:87 [request_id=01K... event=request.completed] Request completed
    ```

    A filter or adapter must supply neutral values for optional fields so ordinary third-party records
    cannot break formatting.

- Enable level-based color for local and Docker stdout by default, with an explicit `auto`, `always`,
  or `never` override for environments that do not accept ANSI output. Never put ANSI sequences in
  the JSON file, Loki payloads, or other machine data.
- Keep the structured file on the application data mount, not the read-only container layer. Create
  its directory with the runtime user's ownership and use bounded rotation and retention. Choose bounds
  from expected volume and available storage; `25 MiB` per file with eight retained files is a
  reasonable starting point, not a universal limit. Keep the active segment as plain JSONL and
  compress closed segments with Zstandard.
- Configure logging once during startup before application work begins. Avoid duplicate handlers and
  repeated serialization when an ASGI server or process manager also configures logging.
- Do not monkey-patch `logging.Logger.makeRecord` or the process-wide record factory merely to reshape
  structured fields. Prefer a documented `extra` contract, `LoggerAdapter`, filters, or an
  application-owned event helper; preserve an established patch until its callers can migrate safely.

## Choose the Default Package

- Add both `colorlog` and `structlog` for a new deployable service. Keep standard-library logging as the
  integration layer so application, framework, and dependency records share routing and level policy.
- Use structlog to build and bind the event dictionary, then preserve its fields through the
  standard-library boundary. Render each handler independently: `ColoredFormatter` owns the stdout
  line and a structlog JSON renderer owns the file payload. Do not pre-render one string for both
  sinks, stack two renderers on one handler, or let either formatter mutate the shared record.
- A small non-service command-line tool that needs only a human console may use `colorlog` alone. A
  reusable library normally uses neither package directly and emits standard-library records.
- Do not add Loguru as an NGC default or intercept every logger process-wide. Do not add
  `python-json-logger` beside structlog merely to render JSON; it remains a reasonable lightweight
  formatter for an established standard-library pipeline that does not need structlog.
- Treat package choice as an application concern. Libraries may depend on structlog only when their
  public logging API deliberately exposes structlog events; otherwise they emit standard records.

## Set Useful Default Levels

- Set the application namespace to `DEBUG`. Route it to the JSON file at `DEBUG` and stdout at `INFO`;
  handler levels, not duplicate logger calls, determine which sink receives each record.
- Default the root logger and ordinary third-party libraries to `WARNING`. This suppresses routine
  dependency chatter while retaining warnings and errors. Raise a specific dependency to `INFO` or
  `DEBUG` only for a demonstrated operational need, and expose narrow per-logger overrides through
  application configuration.
- Keep ASGI lifecycle and server error logging at `INFO`. Keep access logging at `INFO` only when it is
  the canonical request log; otherwise disable or raise the server access logger after the application
  emits its own correlated request-completion event. Do not emit both copies.
- Use `DEBUG` for detailed diagnostic state, `INFO` for lifecycle changes and successful externally
  meaningful operations, `WARNING` for recoverable abnormal conditions or degradation, `ERROR` for a
  failed operation, and `CRITICAL` only when the process or service cannot continue safely.
- Suppress or sample successful health probes and high-frequency loops. Never suppress warnings,
  errors, failed audit events, or exceptions merely to reduce volume, and log an exception with its
  traceback once at the layer that handles or terminates it.

## Compress Closed Segments With Zstandard

- On Python 3.14, use the standard-library `compression.zstd` module rather than adding a third-party
  compression package. The module is optional in CPython builds, so verify its import in the selected
  development, CI, and container runtimes; keep uncompressed bounded rotations as the safe fallback if
  a supported runtime omits it.
- Keep the active file as `<service>.jsonl` so operators can tail it and a crash cannot strand a live
  compressed stream. After rollover closes a segment, compress it to a sortable `.jsonl.zst` name.
  Do not append unrelated rotations into one compressed file.
- Use `RotatingFileHandler` or `TimedRotatingFileHandler` with a deterministic `namer` and a tested
  `rotator`, or an equivalent small application-owned implementation. Preserve the suffix ordering the
  handler needs for retention.
- Compress rollover work away from request and event-loop execution. A `QueueHandler`/`QueueListener`
  pipeline or a single bounded maintenance worker is sufficient; do not introduce a network logging
  system merely to compress local files.
- Write a compressed segment to a temporary sibling, close it successfully, and atomically replace the
  final `.zst` path before deleting the uncompressed source. If compression fails, retain the source,
  emit a bounded diagnostic, and retry during later maintenance or startup.
- Apply retention across compressed and pending uncompressed segments. Never delete the active file,
  and do not let a compression failure bypass the configured storage bound indefinitely.

## Use a Stable Event Schema

Use stable field names and types. A representative application record contains:

```json
{
    "timestamp": "2026-08-18T06:12:34.567Z",
    "level": "INFO",
    "logger": "example_service.orders",
    "service": "example-service",
    "environment": "production",
    "branch": "main",
    "commit": "fb1ee87d9b7c4a1086e4201f8d6173ae4c92b650",
    "event": "order.accepted",
    "message": "Order accepted",
    "request_id": "01K2...",
    "dimensions": { "venue": "example" },
    "metrics": { "quantity": 2 },
    "timings": { "duration_ms": 12.4 }
}
```

- Use an RFC 3339 UTC event timestamp. Preserve the original event time when a collector adds a
  separate observed timestamp.
- Keep `level`, `logger`, `service`, `environment`, `event`, and `message` stable. Attach full build
  identity as process-static context or collector resource metadata.
- Use a stable dotted `event` name for the event class. Put changing values in fields; never embed an
  account, symbol, request ID, or error text in the event name.
- Keep a short human-readable `message` in addition to the machine event name. Do not make parsers
  extract fields from prose.
- Reserve standard `LogRecord` attributes and top-level schema fields. Detect collisions explicitly;
  never let caller-provided `extra` overwrite severity, logger, timestamp, build identity, or request
  context.
- Preserve native JSON types. Durations use a named unit such as `duration_ms`; timestamps are strings;
  counts and amounts remain numbers rather than formatted text.
- Build one logical event and render it independently for each handler. A formatter or handler must not
  mutate the shared `LogRecord`, event dictionary, message, arguments, or exception data; copy before
  adapting values so handler order cannot change another sink's output.
- Use consistent namespaces such as `dimensions` for bounded categorical context, `metrics` for
  measured values, `timings` for durations, and `snapshot` for bulky diagnostic state. Keep commonly
  queried stable fields at the top level.
- Add a `schema_version` only when consumers need explicit log-schema evolution. Changing a field's
  meaning or type requires an intentional migration.

## Propagate Context Safely

- Accept or generate a bounded request/correlation ID at the trusted boundary. Return it to the caller
  when the protocol supports that and propagate it to approved downstream calls.
- Use `contextvars` for request-local context across asyncio and ordinary threaded execution. Explicitly
  copy or bind context when work moves to a new task, executor, thread, or process, and reset it in a
  `finally` block.
- Do not rely on mutable module globals or thread-local storage alone in mixed async/threaded services.
- Include trace and span identifiers when tracing exists. Do not invent tracing solely to populate log
  fields.
- Log build identity once at startup and attach it automatically thereafter. Do not run Git from the
  production process to discover it.

## Redact at the Serialization Boundary

- Never log tokens, passwords, authorization headers, cookies, private keys, connection strings with
  credentials, full request/response bodies, or personal data by default.
- Prefer an allowlist of safe structured fields. Recursively redact known secret keys before JSON
  serialization so nested `extra`, exception context, and snapshots cannot bypass filtering.
- Treat field names case-insensitively for redaction and cover common aliases such as `token`,
  `secret`, `password`, `authorization`, `cookie`, and credential-specific project names.
- Bound string, collection, and snapshot sizes. Mark truncation explicitly rather than emitting invalid
  JSON or silently dropping the entire record.
- For exceptions, record a stable event, exception type, sanitized message, and stack trace at the
  appropriate severity. Do not log the same exception repeatedly at every layer.
- Keep client responses sanitized independently; a safe response is not proof that server logs are
  safe.

## Control Cardinality and Volume

- For Loki, use only a small set of low-cardinality, long-lived labels such as service, environment,
  and level when operationally useful.
- Keep request IDs, trace IDs, user IDs, order IDs, symbols, URLs, and timestamps out of index labels.
  Store them in the JSON body or structured metadata.
- Do not turn every structured field into a label. Review the combined label set because several
  individually bounded labels can still multiply stream count.
- Sample or suppress successful health probes and high-frequency debug loops. Always retain errors and
  policy-required audit events.
- Use aggregation or metrics for high-rate counters and latency distributions. Logs are for discrete
  events and diagnosis, not a replacement for metrics.
- Document retention and expected volume for audit, application, and debug records separately.

## Keep Delivery Non-Blocking

- Keep the default stdout and bounded local JSON-file sinks simple. Ordinary local writes may remain
  synchronous when measured latency is acceptable, but rollover compression always runs away from
  request and event-loop execution.
- Prefer an external collector that reads Docker stdout or the mounted JSON file over a synchronous
  in-process network handler.
- A direct Loki or other network handler is an application exception, not the generic NGC transport
  default. Accept one only with an explicit bounded queue, failure policy, timeouts, shutdown flush,
  and evidence that request or event-loop paths never perform network I/O.
- If the application must deliver logs over a network, keep network I/O off request and event-loop
  paths. Use `QueueHandler`/`QueueListener` or an equivalent bounded asynchronous transport.
- Define queue capacity, enqueue behavior, flush deadline, shutdown ordering, and the policy for a full
  queue. Logging failure must not deadlock a request or crash core business processing.
- Make loss visible through a bounded local diagnostic or metric without recursively logging the
  logging failure.
- Apply explicit network timeouts and bounded retry/backoff. Do not retry forever or retain an
  unbounded in-memory backlog.
- Flush within a bounded shutdown grace period. Stop producers before the listener and report records
  that could not be delivered.

## Separate Audit Events From State

- Use stable audit events for security decisions, administrative actions, externally visible state
  transitions, and sensitive business operations.
- Include actor, action, target, result, request ID, and relevant before/after identifiers when safe.
  Do not include credentials or unnecessary personal data.
- Do not use logs as the only authoritative business state, transaction ledger, or migration record.
  Persist required state transactionally and treat audit logs as an operational trail.
- Define which audit events must never be sampled and what durability/retention the deployment
  provides. An application's stdout call alone is not a durability guarantee.

## Test the Logging Contract

- Capture representative records, parse each JSON line, and assert required fields, types, timestamp
  format, stable event names, and build/request context.
- Assert stdout includes the timestamp, level, logger, module/line, optional request/event context, and
  message. Assert forced-color output contains ANSI sequences, no-color output does not, and every JSON
  or network payload remains ANSI-free.
- Assert an application `DEBUG` event appears in the structured file but not the default stdout sink,
  while `INFO` and above appear in both. Assert ordinary third-party `INFO` chatter is filtered and its
  warnings and errors remain visible.
- Render the same record through handlers in different orders. Assert the original record is unchanged
  and structured output is byte-for-byte equivalent regardless of whether the console ran first.
- When structlog is selected, exercise both native structlog events and ordinary standard-library
  records from the application, ASGI server, and a representative dependency.
- Test context isolation across concurrent requests or tasks and verify context is cleared after each
  operation.
- Test recursive redaction with nested mappings, sequences, exception messages, and mixed-case secret
  keys. Assert forbidden values are absent from the serialized text.
- Test truncation and serialization of non-JSON-native values. A logging formatter should degrade
  safely rather than raise into application code.
- Test exception records without asserting unstable full stack strings.
- Exercise file rotation with small test-only bounds, and verify retention never writes outside the
  configured data directory.
- Decompress a rotated `.jsonl.zst` segment with `compression.zstd`, parse every JSON line, and test
  that a simulated compression failure preserves the uncompressed source.
- Test queue saturation and shutdown behavior when an in-process transport is selected.
- For Loki, review configured labels and ensure high-cardinality identifiers remain fields or structured
  metadata.
