# Containers and Compose

Read this reference when Docker or Compose is selected.

When creating or substantially replacing a Dockerfile or Compose file, also read
[container-starters.md](container-starters.md).

## Contents

- [Audit the build contract](#audit-the-build-contract)
- [Build a least-privilege image](#build-a-least-privilege-image)
- [Describe environments with Compose](#describe-environments-with-compose)
- [Validate the result](#validate-the-result)

## Audit the Build Contract

- NGC CI builds from the repository root. Require `context: .` in the Buildx image job even when the
  Dockerfile is nested, and keep every `COPY`, `ADD`, and bind-mount source relative to that root. The
  bundled audit helper assumes this contract. Non-root local build contexts are outside the supported
  workflow.
- Enumerate every Dockerfile `COPY`, `ADD`, and `RUN --mount=type=bind` source. Compare each literal
  source with the effective root or Dockerfile-specific `.dockerignore`.
- The bundled helper lists literal sources and top-level runtime-asset hints but deliberately does not
  emulate Docker's ignore-pattern engine. Review nontrivial `.dockerignore` rules directly; the CI
  build is authoritative.
- Never ignore `pyproject.toml`, `uv.lock`, workspace member manifests, source roots, or runtime assets
  that the build consumes.
- Inventory root-level templates, static files, migrations, CSV data, certificates, and other runtime
  assets. Either package them or copy them explicitly. A starter `COPY src ./src` is insufficient when
  a service intentionally reads repository-root assets.
- Keep `.git`, real `.env` files, local configuration, mutable data, caches, tests, and build output out
  of the context unless a tested build stage explicitly needs one of them.
- Verify the CI workflow keeps the root context explicit; do not add context inference or alternate
  local build layouts to the baseline.

## Build a Least-Privilege Image

- Default Python 3.14 services to `ghcr.io/astral-sh/uv:python3.14-trixie-slim`. Prefer Debian slim for
  broad wheel and native-library compatibility. Use Alpine only after verifying the complete
  dependency stack on musl and demonstrating a concrete benefit.
- Use current Dockerfile syntax, a trusted minimal base, BuildKit cache mounts, and lockfile-first
  layers. Treat base-image tags and digests as an explicit update policy; pin a digest only when the
  repository requires byte-for-byte repeatability.
- Retain a working single-stage image for a pure-Python service when a split would not remove
  compilers, native headers, build tools, or package artifacts. Use builder/runtime stages when they
  measurably keep those items out of production.
- Install production dependencies with `uv sync --locked --no-dev`; add `--no-editable` for an
  installable package. Keep Git, caches, tests, source-control metadata, and build-only dependencies
  out of the runtime image.
- Run as an explicit non-root UID/GID. Use an absolute `WORKDIR`, exec-form `CMD`, and graceful signal
  handling.
- Do not declare `VOLUME` in the Dockerfile. Pre-create the intended data mountpoint with narrow
  ownership, then let Compose or the deployment platform attach storage explicitly.
- When the structured logging capability is selected, create `data/logs` under that mountpoint and let
  the application own bounded JSON-file rotation there. Do not write logs into the read-only image
  layer or an anonymous volume.
- Never pass secrets through `ARG`, Dockerfile `ENV`, labels, or the build context. Use BuildKit
  secrets for build-time credentials and the runtime platform's secret mechanism for application
  credentials.
- Define a cheap liveness endpoint that tests the process and a bounded readiness endpoint that checks
  only dependencies required to accept traffic. Do not turn liveness into a cascading dependency
  check.
- Do not require a container smoke test in the baseline when startup needs secret configuration. Add
  one only for a stable, non-secret startup contract.
- Docker labels form a string map. Inspect a dotted OCI label with
  `{{ index .Config.Labels "org.opencontainers.image.revision" }}` rather than treating dots as nested
  fields.

## Describe Environments With Compose

- Use the Compose Specification without the obsolete top-level `version` key.
- Treat Compose used by test, staging, trading, or production as runtime-only: specify `image` and
  never `build`. CI is the sole builder. Local operation selects a published CI image rather than
  maintaining a second source-build path.
- Prefer service DNS names, named volumes, internal networks, health checks, and dependency health
  conditions. Avoid `container_name`, host networking, mutable `latest` tags, and Docker socket mounts.
- Quote port mappings. Publish only ports the host must reach; use `expose` for container-only traffic.
- Add `init`, a stop grace period, `read_only`, a small `/tmp` tmpfs, `cap_drop: [ALL]`, and
  `no-new-privileges` where the application supports them.
- Mount the application data path when the selected logging profile writes its bounded JSON debug log;
  verify that the runtime UID can create and rotate files there.
- Use `restart: unless-stopped` when single-host Compose owns restarts; omit it when an external
  orchestrator owns that policy.
- When ignored `.env` is the local runtime contract, pass it with `env_file`. Compose's automatic
  `.env` loading performs interpolation but does not inject variables into the container.
- Do not repeat application defaults under `environment`; reserve it for genuine container-specific
  overrides. Use platform-managed secrets in shared environments rather than forcing local file
  secrets.
- Use explicitly approved vendor images. Keep the service's built image in the private registry. Read
  [stateful-services.md](stateful-services.md) for infrastructure image, storage, retention, and
  failure-isolation rules.
- Require the application `image` to resolve to a real private-registry tag or digest. Never use a
  `:local` fallback or production source build. Leave `pull_policy` unset so a missing selected image
  can be pulled. Do not use `pull_policy: always` or `docker compose up --pull always`.
- Treat `main` and `pr-<number>` as mutable CI channels. Select exact reviewed digests for shared
  environments.

## Validate the Result

- Run the bundled audit helper from the repository root when its source and asset inventory is useful.
- Confirm the image job uses `context: .`; CI is the authoritative image-build verification.
- Run `docker compose config` against each committed profile with safe placeholder values. Confirm the
  merged service images, ports, environment sources, networks, volumes, health checks, and commands.
- After CI publishes an image, verify required assets and runtime user from that artifact when the
  task includes image validation. Test clean-host startup only when deployment work requires it.
- Do not claim a private image pull, push, or clean-host startup was exercised when it was not.
