---
name: python-ngc
description: Opinionated NGC baseline for private Python services and reusable libraries using uv. Use only when the user explicitly asks to adopt or apply NGC; select only the project and capability guidance that matches the repository.
---

# Build and Maintain an NGC Python Project

Apply a coherent baseline rather than adding independent tools. Make local commands, CI, the
container image, and runtime metadata describe and verify the same artifact.

## Apply This as One Skill With Conditional Profiles

Keep NGC as one skill. Apply the core project, dependency, configuration, quality, and verification
rules first, then select only the relevant guidance:

- Choose one project profile: private deployable service, reusable library, or uv workspace.
- Add capability guidance only when the repository actually uses it: Prettier/Jinja, tests, FastAPI,
  containers, Compose, and private image delivery.
- Treat star naming, private publication, unversioned services, lazydocker, and commit conventions as
  NGC organization policy rather than universal Python facts.
- Preserve established contracts and migrate incrementally when profile adoption would require a
  broad compatibility rewrite.

## Naming

NGC refers to our standard of using IAU-approved star names as project names.

## Start With Evidence

1. Inspect existing instructions, `pyproject.toml`, lockfiles, source layout, tests, container
   files, workflows, and dirty worktree state.
2. Preserve intentional project conventions and unrelated changes. Migrate incrementally when a
   strict baseline would create a repository-wide rewrite.
3. Identify whether the project is a deployable service, a reusable library, or a uv workspace.
   Optimize a service for one supported runtime; test a library across its declared Python range.
   For a workspace, also apply the workspace-specific installation guidance below.
4. Determine whether this is a Docker-deployed service or a genuinely reusable library before
   choosing a package layout. A service may still be an installable `src/` package. Under the NGC
   private-service profile, only reusable libraries produce wheels or sdists as CI artifacts.
5. Read [starter-files.md](references/starter-files.md) before creating or substantially editing
   configuration. Adapt its placeholders and optional sections; do not copy them blindly.
6. Read [official-sources.md](references/official-sources.md) when a version, setting, CLI flag, or
   security recommendation may have changed. Prefer current primary documentation.

## Establish Project and Dependency Boundaries

- Prefer the packaged application created by current `uv init`, a `src/<import_name>/` layout, and
  `uv_build` for a Docker-deployed service so local development and image installation use normal
  package semantics. Keep
  `version = "0.0.0"` fixed, use the image as the sole deployable artifact, and do not add routine
  `uv build`, wheel, or sdist jobs.
- Use `[tool.uv] package = false` and omit `[build-system]` only when the service deliberately does
  not need installation. Use `uv build` and inspect wheel/sdist contents only for a genuinely reusable
  library whose distributions are intentional artifacts.
- Extend the generated `.gitignore` with `/.env`, `/config.toml`, and `/data/`. Add `/.secrets/` only
  when the repository actually uses local secret files; do not create it solely for Compose. Mirror
  the selected secret and local-state exclusions in `.dockerignore`. Anchor these root paths so a
  runtime `src/<import_name>/data/` package directory is not accidentally ignored. Commit
  `.env.example` and `config.example.toml`; never commit real credentials or mutable runtime data.
- Use a `src/<import_name>/` layout for packaged services and libraries. Put runtime templates,
  migrations, and static data inside the package or declare them explicitly as package data. Verify
  the installed service image contains them; for a library, verify they are in the wheel.
- Keep mutable state under ignored `data/`. Keep one-off maintenance, migration, import, and audit
  entry points under `scripts/`; scripts may orchestrate package APIs but must not become a second
  home for business logic. Mirror `src/` modules in unit-test paths where that improves discovery.
- Declare project metadata through `[project]` and development tools through `[dependency-groups]`.
  Declare `[build-system]` for an installable package, even when a private service never publishes
  or directly builds distributions.
- Add and remove dependencies with `uv add` and `uv remove`. Commit `pyproject.toml` and `uv.lock`.
  Do not maintain a second hand-edited requirements file unless an external consumer requires an
  exported one.
- Rely on `uv run` to lock and synchronize the project automatically. Use `uv run --locked` in CI so
  stale metadata fails instead of rewriting `uv.lock`. Reserve explicit `uv sync` for installation
  as the goal, especially cache-efficient container layers.
- Let packaged local development use uv's editable installation. Install packaged services in images
  with `uv sync --locked --no-dev --no-editable`.
- Bound `uv_build` to the next incompatible minor version for packaged projects. Preserve an older range;
  otherwise use the range generated by the installed `uv init` or current uv documentation.
- Declare the actual minimum Python in `project.requires-python`. Pin the chosen local/runtime minor
  in `.python-version` and keep CI and the container aligned with it.
- Never publish repositories, Python distributions, JavaScript packages, or container images to a
  public service. Set `private = true` and `license = "UNLICENSED"` in `package.json`; npm refuses to
  publish a private package. Add `classifiers = ["Private :: Do Not Upload"]` to `[project]`; PyPI
  rejects distributions carrying a `Private ::` classifier. This classifier does not protect other
  registries, so omit Python publication credentials and workflows as a separate control.
- Prefer TOML for application and tool configuration whenever the tool supports it. Use YAML only
  for formats that require it, notably Compose and GitHub Actions.
- Keep shared agent instructions in `AGENTS.md` and general project setup and policy in `README.md`.
  Avoid duplicating authoritative instructions in vendor-specific files such as `CLAUDE.md` or
  Copilot instruction files. When a vendor-specific file is required, make it a thin pointer to the
  shared source of truth.
- Do not add `from __future__ import annotations`. Default new projects to 3.14 or above and write
  annotations using that version's native syntax. Preserve an existing project's explicit supported
  runtime, such as Python 3.13, unless the user authorizes an upgrade.

### uv Workspace Profile

- A uv workspace has a root `[tool.uv.workspace]` table and one or more member projects. Preserve
  member `pyproject.toml` files and decide which member owns each service image and command.
- In a lockfile-only Docker dependency layer, mount every member manifest needed to validate the
  workspace. When the full workspace is not yet present, use `uv sync --frozen
  --no-install-workspace`; after copying the members, use `uv sync --locked` with the production
  groups and installation mode required by the selected member.
- Do not copy the single-project Dockerfile mechanically into a workspace. Read current uv workspace
  and Docker guidance before choosing cache layers, build contexts, or install targets.

## Separate Configuration From Secrets and State

- Treat `config.example.toml` and every other `*.example.toml` file as a documented, safe
  configuration contract. Group settings in named TOML sections. Write every required non-secret
  setting as an active assignment with a safe example value; leave only optional settings that have
  working code defaults commented out. Copy the example to its ignored local filename, and validate
  unknown keys and invalid values at startup.
- Treat `.env.example` as an inventory of environment overrides and required secrets. Group entries
  under comment headings. Write every required variable as an active assignment; use an empty or
  unmistakably fake value for secrets. Leave only optional overrides that have working code defaults
  commented out, explain precedence, and copy the example to ignored `.env` locally. Apply the same
  active-required and commented-optional rule to `.env.example` and every `*.example.toml` file.
- Use a clear precedence such as process environment > `.env` > `config.toml` > code defaults.
  Use `pydantic-settings` or similar to do this automatically. Keep secrets out of TOML.
  Accept direct secrets from the process environment or local `.env`.
  Accept `_FILE` values only when the deployment platform actually mounts secret files and the
  application has an explicit resolver; do not introduce a repository `.secrets/` directory or
  Compose file-secret ceremony by default. Reject simultaneous direct and `_FILE` values, fail
  clearly on unreadable or empty required secrets, and verify the behavior. Add automated tests only
  when the repository's test policy includes them.
- Keep `data/` disposable from Git's perspective but durable from the application's perspective.
  Create it at startup with narrow permissions, or pre-create an owned `0750` mountpoint in the image
  when the runtime volume inherits that metadata. Validate that the effective runtime path is writable
  before accepting work, back it up where necessary, and never bake its contents into an image or
  delete it from an ordinary quality command.

## Configure Ruff and ty Deliberately

- Run Ruff as both linter and formatter: `ruff check` before `ruff format`. In CI, use non-mutating
  `ruff check .` and `ruff format --check .`.
- Treat `select = ["ALL"]` as an intentionally strict, higher-maintenance policy. Lock Ruff, document
  each project-wide ignore, and prefer the default rule set when the team does not want that churn.
- Ignore the formatter's specific incompatible rules, not entire useful families. Keep `PGH004`
  enabled so blanket `# noqa` comments are rejected. Keep the `RUF` family enabled and suppress only
  demonstrated false positives.
- Do not add `noqa`, `extend-ignore`, broad exclusions, or new per-file ignores to make checks pass.
  Fix or refactor the cause. A local suppression is a last resort only for a demonstrated false
  positive after the alternatives have been exhausted; require a narrow rule code and explanation.
- Let Ruff and ty infer the Python version from `requires-python` unless a deliberate override is
  needed.
- Run `uv run ty check`. Begin without broad suppressions; add the narrowest rule, file override, or
  boundary annotation only after inspecting a real diagnostic. Do not make `Any` the default escape
  hatch.

## Format Non-Python Files With Prettier

- Keep Ruff authoritative for Python and Prettier authoritative for JavaScript, TypeScript, CSS,
  HTML/Jinja, JSON, YAML, and Markdown. Do not add linter formatting rules that fight either formatter.
- Install exact local versions of Prettier and every plugin in `devDependencies`; commit `package.json`
  and the package-manager lockfile. Invoke the local binary through a package script so CI never
  downloads an unreviewed latest formatter implicitly.
- Use `.prettierrc.toml` for the starter configuration with `printWidth = 100`, `tabWidth = 4`, and
  `useTabs = false`.
- Commit a small Prettier config and `.prettierignore`. Ignore generated output, dependencies, caches,
  coverage artifacts, vendored/minified files, and any legacy subtree not yet adopted. Do not ignore
  hand-maintained files merely to make the check pass.
- When formatting Jinja HTML, pin `prettier-plugin-jinja-template` and scope its `jinja-template`
  parser override to the actual template paths. Do not force the Jinja parser onto unrelated HTML.
- Minimize every ignored range to the smallest independently safe element. Use either Jinja comments
  (`{# prettier-ignore-start #}` / `{# prettier-ignore-end #}`) or HTML comments
  (`<!-- prettier-ignore-start -->` / `<!-- prettier-ignore-end -->`) outside that element. Prefer
  Jinja comments when the markers should disappear from rendered HTML.
- Do not split one executable `<script>` into multiple executable tags merely to isolate a Jinja line;
  separate tags can change scope or execution semantics. Instead, move the templated value into a
  minimal ignored inert `<script type="application/json">`, then read it from normally formatted or
  external JavaScript. If that refactor is not safe, ignore the affected executable script as a whole.
  Do not use `{% raw %}` for formatter suppression because it changes template rendering semantics.
- Prefer external JavaScript for substantial logic. When server data must be embedded in a script,
  serialize it with Jinja's `tojson` filter rather than `safe` or hand-built JSON. A static inline script
  without Jinja does not need suppression.
- Keep separate mutating and checking scripts: `prettier . --write` locally and `prettier . --check`
  in CI. On a clean CI runner, run `bun install --frozen-lockfile` before the checking script; `bun
run` does not install missing project dependencies. Review formatting changes, especially template
  whitespace and Markdown wrapping.

## Make `just` the Human Interface

- Minimize the public command vocabulary. Start with `qa`, `ruff`, `ty`, and `prettier`; add `serve`
  or a test command only when the repository uses them frequently.
- Compose quality tools with dependencies: `qa: ruff ty prettier`. Let local `ruff` apply safe fixes
  and formatting, let `ty` type-check, and let `prettier` format its owned files. CI calls the same
  tools in check-only mode directly; it never auto-fixes.
- Set `default-list := true` so bare `just` lists recipes without a manual default recipe. Give only
  public recipes short, useful comments such as `# run qa` or `# start api`; long prose belongs in the
  README. Hide helpers with `_` or `[private]`.
- Expect `just` to be installed on developer machines. Do not add `rust-just` as a Python development
  dependency, and have CI invoke the repository's approved tools directly rather than recipes.
- Do not add `sync` recipes. `uv run` synchronizes Python dependencies automatically; install Bun
  dependencies explicitly during initial developer setup and on clean CI runners.
- Avoid extra recipes like `docker`, since we use `lazydocker`.
- Give `serve` and any other recipe that binds a local port an optional port parameter so developers
  can resolve conflicts without editing files.
- `just` uses `sh` by default, including on Windows when Git for Windows, GitHub Desktop, or Cygwin
  provides it. POSIX recipe lines are acceptable when the repository explicitly requires that
  complete `sh` toolchain. Otherwise use `windows-shell`, a script recipe, or a checked-in
  cross-platform script. Use a script when logic becomes more than a few commands.
- Keep destructive actions out of the starter interface. If one is genuinely frequent, require
  `[confirm]` and use an exact, narrow target.

## Test Behavior When the Repository Uses Tests

- Honor the repository's test policy. Do not introduce tests, pytest, coverage, or a test CI gate when
  the project explicitly does not want tests.
- When tests are in scope, use pytest with the `src` layout and `--import-mode=importlib`. Enable strict configuration and
  strict markers when the locked pytest version supports them.
- Organize tests by behavior: fast unit tests, boundary/integration tests, and explicitly selected
  end-to-end tests. Mark tests that require networks, credentials, clocks, or live services.
- Test public behavior rather than implementation detail. Use fixtures with narrow scope, deterministic
  clocks/randomness, explicit timeouts, and cleanup that runs even after failure.
- Keep `test` fast and coverage-free for iteration; make `coverage` the merge-gate command. Measure
  branch coverage, show missing lines, emit XML for CI, and set a realistic non-decreasing threshold.
- Mark end-to-end tests with `e2e`. Make `just test` exclude them and use `just test e2e` as the
  explicit opt-in that includes them. CI should express the same selection with pytest directly.
- Do not exclude difficult code simply to raise the percentage. Exclude only mechanically untestable
  lines with a specific pragma and reason.
- Run parallel tests only after confirming isolation. Shared ports, files, databases, and mutable
  process globals must be unique per worker.
- For services, include contract tests for settings validation, health endpoints, build metadata,
  OpenAPI generation when FastAPI is in use, and graceful startup/shutdown. For reusable libraries,
  test the public API, supported Python range, and installed wheel instead of service-only contracts.

## Prefer HTTPX2 Only Where Explicit HTTPX Would Be Needed

- Do not add an HTTP client by default.
- When implementing a use site that would otherwise require `import httpx`, add and write
  `import httpx2` instead. Make this change only where that explicit client import is needed; do not
  mechanically replace unrelated clients or rewrite an established integration without a concrete
  requirement. Avoid process-wide `alias_httpx()` unless an unmodifiable integration requires the
  old import name.
- `requests` is a separate, valid HTTP client. Preserve working `requests` code and dependencies; do
  not migrate them to `httpx2` solely because of this preference. Change clients only for a concrete
  project requirement or an explicitly requested migration.
- For async services, create a shared `httpx2.AsyncClient` in the FastAPI lifespan, inject it into
  callers, and close it on shutdown. Do not create clients inside hot request loops.
- Set explicit connect, read, write, and pool timeouts plus measured connection limits. Bound retries
  to safe failures and idempotent operations; propagate the request ID without forwarding unrelated
  inbound headers.
- Test ASGI applications with `httpx2.ASGITransport` and `httpx2.AsyncClient`. Manage lifespan
  separately because the transport does not trigger application startup or shutdown events.
- Use `httpx2.MockTransport` or dependency injection for deterministic outbound-client tests. Block
  accidental live network access in the default test suite.

## Build a Least-Privilege Container

- Default Python 3.14 services to `ghcr.io/astral-sh/uv:python3.14-trixie-slim`: it provides the
  supported Python runtime and uv without a per-repository base-image variable. Prefer Debian slim
  for broad wheel and native-library compatibility. Use the Alpine variant only after verifying the
  entire dependency stack on musl and establishing a concrete size or security benefit.
- Use a current Dockerfile syntax, trusted minimal base, `.dockerignore`, BuildKit cache mounts, and
  lockfile-first layers. Lock application dependencies. Treat base-image tags and digests as an
  explicit update policy; pin a digest only when the repository requires byte-for-byte repeatability.
- Keep a working single-stage image for a pure-Python non-package service when there are no compilers,
  build-only dependencies, or package artifacts to isolate. Use builder and runtime stages when they
  measurably keep native toolchains, build tools, or artifacts out of the runtime. Complexity alone is
  not hardening.
- Install production dependencies with `uv sync --locked --no-dev`; add `--no-editable` for packaged
  projects. Keep compilers, Git, caches, tests, and source-control data out of the runtime image.
- Run as an explicit non-root UID/GID. Use an absolute `WORKDIR`, exec-form `CMD`, a writable data
  volume only where needed, and graceful signal handling.
- Do not declare `VOLUME` in the Dockerfile. Image-level volume declarations force runtime
  mountpoints and can create anonymous volumes. Pre-create the intended data directory with narrow
  ownership, then let Compose or the deployment platform attach named storage explicitly.
- Never pass secrets through `ARG`, Dockerfile `ENV`, image labels, or the build context. Use BuildKit
  secrets for build-time credentials and process environment or the runtime platform's secret
  mechanism for application credentials.
- Define a cheap liveness endpoint that tests the process, and a bounded readiness endpoint that tests
  only dependencies required to accept traffic. Do not turn liveness into a cascading dependency check.
- Do not require a container smoke test in the service CI baseline. Services commonly require runtime
  configuration or secrets that do not belong in image-build CI. Add one only when the repository has
  a stable, non-secret startup contract that makes it useful.
- Docker labels form a string map. When inspecting a dotted OCI label with a Go template, use
  `{{ index .Config.Labels "org.opencontainers.image.revision" }}` rather than treating the dots as
  nested fields.

## Use Compose as an Explicit Environment Description

- Use the Compose Specification without the obsolete top-level `version` key. Treat every Compose
  file used by test, staging, trading, or production as runtime-only: specify `image` and never
  `build`. CI is the sole builder of deployable service images. If developers genuinely need a local
  container build, use `docker build` or a clearly development-only Compose file that deployment
  never loads.
- Prefer service DNS names, named volumes, internal networks, health checks, and dependency health
  conditions. Avoid `container_name`, host networking, mutable `latest` tags, and mounting the Docker
  socket.
- Quote port mappings. Publish only ports that the host must reach; use `expose` for container-only
  communication.
- Add `init`, a stop grace period, `read_only`, a small `/tmp` tmpfs, `cap_drop: [ALL]`, and
  `no-new-privileges` where the application supports them.
- Use `restart: unless-stopped` when single-host Compose owns service restarts; omit it when an
  external orchestrator owns that policy.
- When ignored `.env` is the repository's local runtime contract, pass it with `env_file`; Compose's
  automatic `.env` loading is only for interpolation. Do not manually repeat application defaults in
  `environment`. Keep that mapping only for genuine container-specific overrides. Accept direct
  runtime secrets from `.env` locally and use platform-managed secrets in shared environments; do
  not force a local Compose secret file.
- Use explicitly approved base images. An official public vendor base such as Astral's uv image is
  acceptable; keep the service's built and deployed image in the private registry.
- Require `image` to resolve to a real private-registry tag or digest. Never use a `:local` fallback
  or let production fall back to a source build. Leave `pull_policy` unset so a missing selected
  image can be pulled. Forbid `pull_policy: always` and `docker compose up --pull always`. Use exact
  reviewed digests for shared environments.
- Validate the merged result with `docker compose config` and test startup from a clean machine state.

## Expose Build Identity Without Release Versions

- Private services do not have release versions: no SemVer bumping, release tags, tag-triggered release
  jobs, changelog automation, version endpoints, or package publication. Do not invent a release flow.
- Inject Git branch, full commit SHA, and commit timestamp from the trusted build system. Generate a
  separate RFC 3339 image build timestamp for `org.opencontainers.image.created`. Do not copy
  `.git` or run Git in the production container. Use the commit as artifact identity; branch is display
  context only. Treat `main` and `pr-<number>` image tags as mutable CI channels, not release versions
  or deployment instructions. Deploy shared environments only after explicitly selecting an image
  digest.
- Return exactly `branch`, full `commit`, `commit_time`, `python_version`, and `platform` from a non-secret
  `/build-info` or `/info` endpoint and log them once at startup. Derive the runtime fields from
  `sys.version` and `platform.platform()`. Use `unknown` locally; never claim uninjected source data.
- Truncate the full commit only in human-facing presentation when space is limited. Preserve the full
  SHA in the API, logs, OCI revision label, and CI metadata.
- Do not expose a release version through FastAPI/OpenAPI for an unversioned service. A fixed
  `version = "0.0.0"` in `pyproject.toml` exists only because PEP 621 requires the field.
- For every CI image build, inject the revision of the source actually built rather than deriving
  identity from a different checkout or synthetic merge commit.
- Use Conventional Commits for every commit message. Prefer squash commits when repository policy
  allows it.
- Use Gitea as the private image registry. This NGC deployment does not have provenance or SBOM
  support, so set `provenance: false` and `sbom: false` in `docker/build-push-action`.

## Treat FastAPI's OpenAPI Schema as a Product

- Apply the following defaults to new APIs. Do not rewrite established paths, envelopes, operation
  IDs, or schemas without an explicitly authorized compatibility migration.
- Put public contracts below `/api/v1/` with an `APIRouter(prefix="/api/v1")`; do not version health,
  metrics, static assets, or browser pages by accident. Introduce `/api/v2` only for an intentional
  incompatible contract, not for ordinary additive changes.
- Accept a bounded `X-Request-ID` from the trusted edge or generate one. Store it in request context,
  propagate it to logs and downstream calls, and return it in the response header and JSON envelope.
- Use a stable success envelope such as `{request_id, status: "ok", data, meta}` and a stable error
  envelope such as `{request_id, status: "error", status_code, error: {code, message, details}}`.
  Keep machine-readable error
  codes stable; do not leak tracebacks or secrets. Apply the convention to validation and framework
  errors as well as route-raised errors.
- Use HTTP semantics deliberately: nouns in paths, plural collections, correct status codes,
  idempotent `PUT`/`DELETE`, `202` for accepted asynchronous work, explicit pagination bounds, and
  idempotency keys for retriable creates that can duplicate side effects.
- Construct `FastAPI` with a stable title, summary/description, tag metadata, and deployment-aware
  `servers`/`root_path` where needed. Use an explicit unversioned marker for a private service.
- Group routes with `APIRouter`, stable tags, and stable unique operation IDs. Make operation IDs
  intentional before generating clients.
- Model every request, success response, and important error response. Supply summaries, descriptions,
  status codes, examples, deprecation markers, and security schemes where they help consumers.
- Keep Swagger UI, ReDoc, and `/openapi.json` locations an explicit deployment policy. Disabling the UI
  is not access control; authenticate or network-restrict sensitive documentation.
- Generate `app.openapi()` in tests. Fail on warnings, duplicate operation IDs, broken schemas, or an
  unintended compatibility change. Publish or diff the schema when clients depend on it.
- Configure trusted proxy headers and `root_path` only for known proxies. Do not trust forwarded headers
  from arbitrary clients.
- Do not invent auth unless explicitly stated; we run our services behind a firewall and proxy.

## Harden CI and Private Image Delivery

- Trigger checks for pull requests and protected-branch pushes. Do not add release tag triggers or
  public publishing workflows for private unversioned services.
- Set `permissions: contents: read` at workflow or job scope and add the smallest extra permissions only
  where required. Do not give test jobs write tokens or production secrets.
- Treat pull-request metadata and all other contributor-controlled GitHub context as untrusted input.
  Pass it through a step's `env` mapping and quote shell variables; never interpolate an expression
  directly into a `run` script.
- Pin third-party actions to full commit SHAs and keep same-line tag comments as readable version
  documentation.
- Do not enable Dependabot version updates or add `.github/dependabot.yml`. Version-update pull
  requests require manual attention and bandwidth and conflict with "if it ain't broke, don't fix
  it." Enable only Dependabot security updates with Grouped security updates in the GitHub.com
  repository or organization settings; those settings do not require a Dependabot YAML file.
- Cache uv through the supported setup integration, keyed by the lockfile. Caches accelerate builds;
  they are never a substitute for `uv.lock`.
- Install JavaScript tooling in CI with `bun install --frozen-lockfile` before running package scripts.
  Do not let CI update or regenerate the Bun lockfile implicitly.
- Format GitHub Actions YAML with one blank line between step entries and between job definitions so
  workflow structure remains easy to scan.
- Run lock validation, Ruff lint, Ruff format check, Prettier check, ty, and the checks actually in
  repository policy. Build distributions only for libraries. After those checks pass, use one image
  job to publish `main` for protected `main` pushes and `pr-<number>` for same-repository,
  non-Dependabot pull requests. Skip image publication for forks and Dependabot. Do not add a separate
  pull-request `image-check` or non-pushing image-build job.
- Treat that gated CI image job as the only builder for shared environments. Test, staging, trading,
  and production select and pull a published image; they never run `docker build` or
  `docker compose build`.
- Use a pinned `docker/metadata-action` with only `type=ref,event=branch` and
  `type=ref,event=pr`. Trigger branch pushes only for `main`; these rules must produce only `main` and
  `pr-<number>`, with no SHA, `latest`, release, or other tags. Pass its `tags` and `labels` outputs to
  the Buildx step. Override its revision and created labels with the exact checked-out commit and build
  timestamp; accept its
  `org.opencontainers.image.version` label as a mutable CI channel, not a release version or a
  deployment instruction.
- Match build-argument names to the Dockerfile contract. Use `BUILD_GIT_BRANCH`, `BUILD_GIT_COMMIT`,
  `BUILD_GIT_COMMIT_TIME`, and `BUILD_CREATED_AT` in the baseline; do not silently substitute shorter
  `GIT_*` names that leave runtime metadata at `unknown`.
- Cancel superseded pull-request runs. Preserve JUnit, coverage XML, OpenAPI, and image metadata as
  artifacts when they aid diagnosis; do not upload credentials, `.env`, or verbose secret-bearing logs.
- Keep registry credentials private. Never target PyPI, npm, GHCR/Docker Hub, another public registry,
  or a public repository as a publication destination. Consuming an explicitly approved official
  vendor base image is allowed. Push one event-specific private channel tag—`main` or
  `pr-<number>`—after all quality jobs pass; do not rebuild separately for staging and production.
- Keep the private registry host and private image path in GitHub repository variables. Authenticate
  the private Git registry as `github.actor` with the narrowly scoped `DOCKER_TOKEN_GITEA`
  repository secret. Expose the token only to the gated image job for protected `main` pushes and
  same-repository, non-Dependabot pull requests; never expose it to fork or Dependabot jobs. This
  deliberately treats same-repository contributors as trusted to use the registry token.
  Require explicit digest selection before deployment, but leave Compose's pull policy unset so a
  missing selected image can be pulled. Keep the approved base image directly in the Dockerfile so
  builds do not depend on an unnecessary repository variable.

## Add Operational Baselines

- Parse typed configuration once at startup. Validate required values and redact secrets in logs and
  representations.
- Emit logs to stdout/stderr and propagate a request/correlation ID. Colored human-readable logs are
  acceptable both locally and in Docker when that is the repository's current operating model;
  structured logging is a later capability, not a prerequisite for NGC adoption. When structured
  logs are adopted, use UTC timestamps and include level, service, branch, commit, and request ID.
  Never log tokens, passwords, full request bodies, or personal data by default.
- Add request timeouts, outbound connection/read timeouts, bounded retries with backoff and jitter, and
  idempotency where retries can repeat writes.
- Use FastAPI lifespan hooks for resource ownership. Close clients, pools, and workers on shutdown;
  keep migrations and one-off administrative tasks separate from web-process startup.
- Keep CORS origins explicit, validate hosts and proxy trust, apply authentication/authorization at the
  boundary, and rate-limit abuse-sensitive endpoints at an appropriate layer.
- Document the minimum developer path in the repository README. Always cover the applicable uv setup;
  mention `just` only when a `justfile` exists, Bun only for the Prettier/Jinja capability, and Docker
  plus lazydocker only for a containerized service. Copy only configuration examples the repository
  actually uses. Run `bun install --frozen-lockfile` before Prettier when that capability is selected.
  Do not add a separate synchronization recipe.

## Verify Before Handoff

Run the closest available equivalents for the selected profile and capabilities:

```text
uv lock --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
# Run tests only when repository policy includes them.
# Run `uv build` only for a clearly reusable library.
# Run Bun commands only for the Prettier/Jinja capability.
bun install --frozen-lockfile
bun run format:check
# Run this only when a justfile exists.
just --dump
# Run this only for the Compose capability. Hosts may not have docker.
docker compose config
```

For a library, inspect and smoke-test the wheel. For a service, validate the workflow, Dockerfile, and
Compose configuration. The single publication job performs the actual image build and push for
qualifying `main` and pull-request events; do not duplicate it with a separate `image-check` job. Keep
a runtime smoke test conditional on a stable, non-secret startup contract. Report unavailable checks
and do not claim that a registry push was exercised locally when it was not.
