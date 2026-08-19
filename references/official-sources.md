# Official Sources

Use this index to re-check guidance that changes with tool releases. Prefer the linked primary source
over blog posts and copied snippets.

## Contents

- [Packaging, uv, Ruff, and ty](#packaging-uv-ruff-and-ty)
- [Formatting, commands, tests, and coverage](#formatting-commands-tests-and-coverage)
- [Configuration, logging, and state](#configuration-logging-and-state)
- [Containers and supply chain](#containers-and-supply-chain)
- [FastAPI and CI security](#fastapi-and-ci-security)

## Packaging, uv, Ruff, and ty

- [uv project initialization](https://docs.astral.sh/uv/concepts/projects/init/): packaged
  applications, generated `src` layout, build system, and project files.
- [uv build backend](https://docs.astral.sh/uv/concepts/build-backend/): backend selection, version
  bounds, package layout, and file inclusion.
- [uv project locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/): `--locked`,
  `--frozen`, dependency groups, and partial installs.
- [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/): cache mounts, layer ordering,
  bytecode, workspaces, and non-editable installs.
- [uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/): supported setup and cache
  behavior.
- [Python Packaging User Guide: `pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/):
  standardized project/build metadata and the `Private :: Do Not Upload` PyPI rejection classifier.
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/) and
  [Ruff formatter conflicts](https://docs.astral.sh/ruff/formatter/#conflicting-lint-rules): file
  discovery, Markdown code-block formatting, version inference, formatter checks, and incompatible
  lint rules.
- [Ruff `PGH004`](https://docs.astral.sh/ruff/rules/blanket-noqa/): why blanket `noqa` comments hide
  diagnostics.
- [ty configuration](https://docs.astral.sh/ty/reference/configuration/) and
  [type checking](https://docs.astral.sh/ty/type-checking/): environment discovery, file selection,
  rules, and terminal behavior.

## Formatting, commands, tests, and coverage

- [Prettier installation](https://prettier.io/docs/install/): exact local versions, configuration,
  ignore files, editor integration, and `--write` versus `--check`.
- [Prettier configuration](https://prettier.io/docs/configuration): config discovery, overrides, and
  parser scoping.
- [Prettier ignore syntax](https://prettier.io/docs/ignore/): whole-file, node, and range ignores.
- [`prettier-plugin-jinja-template`](https://github.com/davidodenwald/prettier-plugin-jinja-template):
  Jinja parser overrides and range ignores for `<script>` and `<style>` blocks.
- [Jinja template documentation](https://jinja.palletsprojects.com/en/stable/templates/): comment
  behavior, raw-block semantics, autoescaping, and the `tojson` filter for HTML and script contexts.
- [Bun install](https://bun.sh/docs/pm/cli/install), [Bun runtime](https://bun.sh/docs/runtime), and
  [`bunfig.toml`](https://bun.sh/docs/runtime/bunfig): frozen CI installs, package scripts, and default
  project dependency auto-install behavior.
- [npm `package.json`](https://docs.npmjs.com/cli/configuring-npm/package-json/): `private = true`
  prevents npm publication.

- [just programmer's manual](https://just.systems/man/en/): recipes, dependencies, private recipes,
  confirmation, working directory, dotenv behavior, recipe listing, and Windows `sh`/`windows-shell`
  behavior.
- [pytest good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html):
  `src` layout, `importlib` mode, and strict configuration.
- [coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html): branch coverage,
  reports, exclusions, and failure thresholds.
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html): pytest integration
  and report behavior.

## Configuration, logging, and state

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): typed environment,
  dotenv, secrets, TOML sources, source customization, and precedence.
- [Python `tomllib`](https://docs.python.org/3/library/tomllib.html): standard-library TOML parsing and
  its read-only scope.
- [Python logging cookbook: contextual data](https://docs.python.org/3/howto/logging-cookbook.html#use-of-contextvars):
  request context propagation across threads and asynchronous tasks with `contextvars`.
- [Python `QueueHandler` and `QueueListener`](https://docs.python.org/3/library/logging.handlers.html#queuehandler):
  moving slow handler work off latency-sensitive threads and tasks.
- [Python `compression.zstd`](https://docs.python.org/3.14/library/compression.zstd.html): Python 3.14's
  optional standard-library Zstandard file and streaming interfaces.
- [`colorlog`](https://github.com/borntyping/python-colorlog): colored standard-library logging,
  stream detection, and explicit color controls.
- [structlog standard-library integration](https://www.structlog.org/en/stable/standard-library.html)
  and [context variables](https://www.structlog.org/en/stable/contextvars.html): shared processing for
  structlog and standard records, multiple renderers, and request-context binding.
- [OpenTelemetry log data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/): stable event,
  severity, trace, timestamp, body, and attribute concepts for interoperable structured logs.
- [Grafana Loki label cardinality](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/):
  keeping labels low-cardinality and putting unbounded identifiers in structured metadata or log
  fields.
- [SQLite online backup API](https://www.sqlite.org/backup.html): consistent live snapshots without
  copying an actively changing database file directly.
- [SQLite write-ahead logging](https://www.sqlite.org/wal.html): WAL behavior, concurrency tradeoffs,
  checkpointing, and the same-host filesystem requirement.

## Containers and supply chain

- [Docker build best practices](https://docs.docker.com/build/building/best-practices/): multi-stage
  images, minimal bases, cache use, non-root users, and digest pinning.
- [Dockerfile `VOLUME`](https://docs.docker.com/reference/dockerfile/#volume): image-declared
  mountpoints and their runtime behavior.
- [Compose services](https://docs.docker.com/reference/compose-file/services/) and
  [Compose volumes](https://docs.docker.com/reference/compose-file/volumes/): `env_file`, restart and
  hardening fields, and named-volume declarations.
- [Compose Build Specification](https://docs.docker.com/reference/compose-file/build/): build
  configuration, which belongs outside image-only deployment Compose files.
- [Set environment variables in Compose](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/): container environment injection with `environment` and
  `env_file`, distinct from interpolation.
- [`docker compose up`](https://docs.docker.com/reference/cli/docker/compose/up/): detached mode and
  selectable pull behavior.
- [Compose secrets](https://docs.docker.com/reference/compose-file/secrets/): explicit secret grants
  when the deployment actually uses file-mounted secrets.
- [OCI image annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md):
  standard `version`, `revision`, `created`, and `source` keys.
- [`docker/metadata-action`](https://github.com/docker/metadata-action): event-derived image tags,
  OCI labels, and outputs for `docker/build-push-action`.

## FastAPI and CI security

- [HTTPX2 documentation](https://httpx2.pydantic.dev/),
  [async clients](https://httpx2.pydantic.dev/async/), and
  [transports](https://httpx2.pydantic.dev/advanced/transports/): maintained client namespace,
  connection reuse, ASGI testing, mock transports, and lifespan boundaries.
- [HTTPX2 migration guide](https://httpx2.pydantic.dev/migration/): compatibility boundaries when an
  existing integration changes from HTTPX to HTTPX2.
- [FastAPI metadata and documentation URLs](https://fastapi.tiangolo.com/tutorial/metadata/): OpenAPI
  metadata, tags, and docs/schema paths.
- [FastAPI client generation](https://fastapi.tiangolo.com/advanced/generate-clients/): stable, unique
  operation IDs and tags.
- [FastAPI behind a proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/): `root_path`, servers,
  and forwarded proxy behavior.
- [FastAPI middleware](https://fastapi.tiangolo.com/tutorial/middleware/) and
  [bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/): response headers,
  request middleware, router prefixes, and modular APIs.
- [FastAPI error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/),
  [custom responses](https://fastapi.tiangolo.com/advanced/custom-response/), and
  [additional responses](https://fastapi.tiangolo.com/advanced/additional-responses/): Starlette HTTP
  exceptions, preserved headers, direct-response validation boundaries, and documented error models.
- [HTTP Semantics (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110) and
  [Problem Details for HTTP APIs (RFC 9457)](https://www.rfc-editor.org/rfc/rfc9457): method/status
  semantics and a standard alternative to a house error envelope.
- [W3C Trace Context](https://www.w3.org/TR/trace-context/): standard trace propagation and trust
  boundaries, distinct from application request IDs and idempotency keys.
- [FastAPI in containers](https://fastapi.tiangolo.com/deployment/docker/): exec-form commands,
  graceful shutdown, and worker tradeoffs.
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use): least
  token permissions, immutable action references, secrets, and supply-chain hardening.
- [GitHub secret types](https://docs.github.com/en/code-security/reference/secret-security/secret-types):
  repository secret scope and withholding from fork and Dependabot pull requests.
- [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments):
  required reviewers and environment-scoped secrets for manually approved publication jobs.
- [Secure pull-request workflows](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target):
  trust boundaries when checking out and executing pull-request code.
- [Configuring Dependabot security updates](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configuring-dependabot-security-updates):
  repository and organization UI controls for security updates and grouped security updates.
- [Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches):
  required reviews, checks, and push restrictions for trusted publication branches.
