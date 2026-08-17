# Starter Files

Use these as adaptable baselines. First decide whether the repository is a Docker-deployed service or
a reusable library. The service baseline below is a private, unversioned, installable `src/` package,
but it does not run `uv build` or treat Python distributions as artifacts.

## Private service policy

- The Docker image is the sole deployable artifact.
- Do not publish the repository, Python distributions, JavaScript packages, or container images to
  public services.
- Do not create release versions, release tags, tag-triggered workflows, or version-bump automation.
- `version = "0.0.0"` is fixed PEP 621 metadata, not a release number.
- Push successful protected-branch service images to the Gitea registry as `main`, and successful
  same-repository, non-Dependabot pull-request images as `pr-<number>`. Skip fork and Dependabot image
  publication. Use the same image job for both channels; do not add a separate `image-check` job.
- This NGC Gitea deployment does not have provenance or SBOM support; keep both disabled in the image
  build step.
- Authenticate the private Gitea registry as `github.actor` with the narrowly scoped
  `DOCKER_TOKEN_GITEA` repository secret. Treat registry tags as mutable channels. CI is the only
  builder for shared environments: deployment Compose files are image-only, select a reviewed
  digest, and leave Compose's pull policy unset.
- Do not enable Dependabot version updates or add `.github/dependabot.yml`. Version-update pull
  requests require manual attention and bandwidth and conflict with "if it ain't broke, don't fix
  it." Enable only Dependabot security updates with Grouped security updates in the GitHub.com UI.
- Use Conventional Commits whenever a commit is eventually created.

## Service `pyproject.toml`

```toml
[project]
name = "example-service"
version = "0.0.0"
description = "Private internal service."
readme = "README.md"
requires-python = ">=3.14"
classifiers = ["Private :: Do Not Upload"]
dependencies = [
    "fastapi>=0.135,<1",
    "pydantic-settings>=2.14,<3",
    "uvicorn[standard]>=0.42,<1",
]

[dependency-groups]
dev = [
    "ruff>=0.15,<0.16",
    "ty>=0.0.62,<0.1",
]

[build-system]
requires = ["uv_build>=0.12.3,<0.13"]
build-backend = "uv_build"

[tool.ruff]
line-length = 100
output-format = "concise"

[tool.ruff.format]
docstring-code-format = true

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    # Add only formatter conflicts and deliberate, documented project policy.
    "COM812",
    "D203",
    "D213",
    "E501",
    "ISC001",
]

[tool.ty.terminal]
output-format = "concise"

```

PyPI rejects the `Private :: Do Not Upload` classifier. It does not block alternative registries;
do not configure Python publishing credentials or workflows. Do not add an HTTP client by default.
Preserve `requests` when already used; if choosing between new explicit `httpx` and `httpx2` code,
prefer `httpx2`.

Do not add `noqa`, `extend-ignore`, broad exclusions, or per-file ignores merely to pass CI. Refactor
the cause. A narrow suppression with a rule code and explanation is a last resort for a demonstrated
false positive.

## `package.json`

```json
{
  "name": "example-service-dev",
  "private": true,
  "license": "UNLICENSED",
  "scripts": {
    "format": "prettier . --write --cache",
    "format:check": "prettier . --check --cache"
  },
  "devDependencies": {
    "prettier": "3.9.6",
    "prettier-plugin-jinja-template": "2.2.0"
  }
}
```

Commit the JavaScript lockfile. `private: true` makes npm refuse publication. Do not add a
package-publish script or public registry configuration.
Clean CI runners must run `bun install --frozen-lockfile` before invoking the formatting check.

## `.prettierrc.toml`

Use TOML, a 100-column width, and four spaces:

```toml
printWidth = 100
tabWidth = 4
useTabs = false
proseWrap = "always"
plugins = ["prettier-plugin-jinja-template"]

[[overrides]]
files = ["src/example_service/templates/**/*.html"]

[overrides.options]
parser = "jinja-template"
```

Remove the plugin and override when the repository has no Jinja templates.

## `.prettierignore`

```gitignore
/node_modules/
/.venv/
/build/
/dist/
/htmlcov/
/.pytest_cache/
/.ruff_cache/
/.ty_cache/
/data/
/.env
/config.toml
```

## Root ignore entries

Anchor local state and secrets so similarly named package-data directories remain trackable:

```gitignore
/.env
/config.toml
/data/
```

Use the same root exclusions in `.dockerignore`, together with source-control data, caches, virtual
environments, tests, and build output. Public certificates may be committed when policy allows;
tokens, passwords, private keys, client-key material, and private certificate bundles belong in the
deployment platform's secret store. Add `/.secrets/` to the ignore files only when the project
actually uses local mounted secret files; do not create it solely to satisfy Compose.

## Configuration examples

Group TOML settings into named sections. Write required non-secret settings as active assignments
with safe example values. Leave only optional settings with working code defaults commented out:

```toml
# Copy to config.toml. Process environment > .env > config.toml > code defaults.

[application]
# environment = "development"
# data_dir = "data"

[server]
# host = "127.0.0.1"
# port = 8000

[logging]
# level = "INFO"

[integrations]
api_base_url = "https://internal.example.test"
```

Apply the same rule to `.env.example`: write every required variable as an active assignment, using
an empty or unmistakably fake value for secrets. Leave optional overrides with working defaults
commented out:

```dotenv
# Copy to .env. Never commit real values.

# Required image selection for Compose
APP_IMAGE=registry.example.test/team/example-service@sha256:0000000000000000000000000000000000000000000000000000000000000000

# Application overrides
# APP_ENVIRONMENT=development
# APP_DATA_DIR=data

# Server overrides
# SERVER_HOST=127.0.0.1
# SERVER_PORT=8000
# HOST_PORT=8000

# Logging overrides
# LOG_LEVEL=INFO

# Required secret for local runs
INTERNAL_API_TOKEN=
```

Never put secrets in `config.toml`. Use direct environment variables, including an ignored local
`.env`, by default. Add a `_FILE` alternative only when the actual deployment platform mounts secret
files and the application implements an explicit resolver. Then validate direct values, file values,
conflicts, unreadable files, and empty results.

## `justfile`

Keep the interface small and do not add Docker lifecycle recipes; operate containers with lazydocker.
Do not add a test recipe when the repository does not use tests.

```just
set quiet := true
set default-list := true

# run qa
qa: ruff ty prettier

ruff:
    uv run ruff check . --fix
    uv run ruff format .

ty:
    uv run ty check

prettier:
    bun run format

# start api
serve port="8000":
    uv run uvicorn example_service.api:app --reload --host 127.0.0.1 --port {{ port }}
```

Developer machines provide `just`; do not add `rust-just` to Python development dependencies. CI
runs `bun install --frozen-lockfile` and then invokes the underlying check commands directly. Add
test dependencies, configuration, and recipes only when repository policy includes tests.

## Single-stage service `Dockerfile`

A builder/runtime split is useful when it keeps compilers, native headers, build tools, or package
artifacts out of production. A pure-Python service often has none of those; retain a working single
stage when the split provides no measurable isolation or size benefit.

```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    APP_ENVIRONMENT=production

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

ARG BUILD_GIT_BRANCH=unknown
ARG BUILD_GIT_COMMIT=unknown
ARG BUILD_GIT_COMMIT_TIME=unknown
ARG BUILD_CREATED_AT=1970-01-01T00:00:00Z

LABEL org.opencontainers.image.revision="${BUILD_GIT_COMMIT}" \
      org.opencontainers.image.created="${BUILD_CREATED_AT}"

ENV BUILD_GIT_BRANCH="${BUILD_GIT_BRANCH}" \
    BUILD_GIT_COMMIT="${BUILD_GIT_COMMIT}" \
    BUILD_GIT_COMMIT_TIME="${BUILD_GIT_COMMIT_TIME}"

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid 10001 --no-create-home app \
    && install -d -m 0750 -o 10001 -g 10001 /app/data

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

CMD ["python", "-m", "uvicorn", "example_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Use the Debian slim variant by default for wheel and native-library compatibility. Use
`python3.14-alpine` only after verifying the complete dependency stack on musl and demonstrating a
concrete benefit.

The `0750` `/app/data` directory is an owned mountpoint whose metadata a named volume can inherit.
Keep the code default at `data`, relative to `WORKDIR /app`. At application startup, validate that
the effective data path exists, remains narrowly permissioned, and is writable; create it with narrow
permissions when the deployment platform supplies an absent path instead. Do not add a Dockerfile
`VOLUME` instruction: runtime configuration owns the mount, and an image-declared mountpoint can
silently create anonymous volumes.

Keep `.git`, `.env`, `config.toml`, data, caches, tests, and build output out of the build context.
Never pass credentials through build arguments, labels, Dockerfile `ENV`, or the build context.

## `compose.yaml`

This is a hardened, image-only deployment baseline for test, staging, trading, and production. CI is
the sole builder for those environments. A local developer may build with `docker build` or an
explicit development-only Compose file that deployment automation never loads.

```yaml
name: example-service

services:
  api:
    image: "${APP_IMAGE:?Set APP_IMAGE to an approved private image tag or digest}"
    restart: unless-stopped
    init: true
    stop_grace_period: 30s
    ports:
      - "127.0.0.1:${HOST_PORT:-8000}:8000"
    env_file:
      - .env
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    volumes:
      - app_data:/app/data

volumes:
  app_data:
    driver: local
```

Do not add the obsolete top-level Compose `version` key, public image names, mutable release tags, or
Docker socket mounts. Never add `build` or a `:local` image fallback to a deployment Compose file.
Set `APP_IMAGE` to a real image in the private registry; use an exact reviewed digest for a shared
environment. Leave `pull_policy` unset so Compose can pull the selected image when it is absent. Do
not use `pull_policy: always` or `docker compose up --pull always`; run `docker compose up --detach`.

Compose automatically reads `.env` for interpolation, but that alone does not inject the variables
into the container. `env_file` does. Prefer it when `.env` is the runtime configuration source, and
let application defaults handle absent optional values instead of repeating every default under
`environment`. Use the deployment platform's managed secrets for shared environments; add Compose
file secrets only when that platform actually mounts them and the application supports `_FILE`.

## Build information

Private services expose source and runtime identity, not a release version:

```python
import os
import platform
import sys

from pydantic import BaseModel, ConfigDict


class BuildInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    branch: str
    commit: str
    commit_time: str
    python_version: str
    platform: str


BUILD_INFO = BuildInfo(
    branch=os.getenv("BUILD_GIT_BRANCH", "unknown"),
    commit=os.getenv("BUILD_GIT_COMMIT", "unknown"),
    commit_time=os.getenv("BUILD_GIT_COMMIT_TIME", "unknown"),
    python_version=sys.version,
    platform=platform.platform(),
)
```

Expose exactly these fields from `/build-info` or `/info`, and log them once at startup. A representative
payload is:

```text
branch=main
commit=fb1ee87d9b7c4a1086e4201f8d6173ae4c92b650
commit_time=2026-08-12 19:05:18 +0800
python_version=3.14.7 (main, Aug  5 2026, 16:32:19) [GCC 14.2.0]
platform=Linux-6.8.0-107-generic-x86_64-with-glibc2.41
```

Do not add a release version field or derive an OpenAPI version from package metadata for an
unversioned service.

## Private CI image flow

Pin third-party actions to full commit SHAs and retain same-line version comments as readable
metadata. Do not enable Dependabot version updates or add `.github/dependabot.yml`; enable only
Dependabot security updates with Grouped security updates in the GitHub.com UI. Quality jobs should
run only the repository's approved gates; do not invent tests or package builds. Use one blank line
between step entries and between job definitions in GitHub Actions YAML.

The image job must follow this order:

1. Run `bun install --frozen-lockfile` before the Prettier check.
2. Read `branch`, full `commit`, and `commit_time` from the exact checked-out source. Generate a
   separate RFC 3339 UTC `created_at` value for the image build time. When a shell consumes GitHub
   context or step outputs, bind them through `env` and quote the shell variables instead of
   interpolating expressions directly into `run`.
3. After the approved quality and test gates pass, publish from protected `main` pushes and
   same-repository, non-Dependabot pull requests. Skip fork and Dependabot image publication. Gate the
   single image job with:

   ```yaml
   if: >-
     github.event_name == 'push' || (github.event.pull_request.head.repo.full_name ==
     github.repository && github.actor != 'dependabot[bot]')
   ```

4. Store the narrowly scoped Gitea registry token as the `DOCKER_TOKEN_GITEA` GitHub repository
   secret. Authenticate as `github.actor`. Expose the token only to that gated image job; this
   deliberately treats same-repository contributors as trusted to use it.
5. Run a pinned `docker/metadata-action` with the private image name and these tag rules:

   ```yaml
   tags: |
     type=ref,event=branch
     type=ref,event=pr
   ```

   Trigger branch pushes only for `main`, so these rules produce only mutable `main` and
   `pr-<number>` channels. Do not add SHA, `latest`, release, or other tags. Override the revision and
   created labels with the exact checked-out commit and generated build timestamp. The generated
   `org.opencontainers.image.version` label is a mutable CI channel, not a release version or a
   deployment instruction.
6. Log in to the self-hosted private registry as `github.actor` with `DOCKER_TOKEN_GITEA`.
7. Build and push once with `docker/build-push-action`, `push: true`, and the metadata action's tags
   and labels. Set `provenance: false` and `sbom: false` because the Gitea registry does not support
   either. Use build-argument names that exactly match the Dockerfile.

The core steps are:

```yaml
- name: Docker meta
  id: meta
  uses: docker/metadata-action@dc802804100637a589fabce1cb79ff13a1411302 # v6.2.0
  with:
    images: |
      ${{ vars.DOCKER_REGISTRY }}/${{ vars.DOCKER_IMAGE_NAME }}
    tags: |
      type=ref,event=branch
      type=ref,event=pr
    labels: |
      org.opencontainers.image.revision=${{ steps.build.outputs.commit }}
      org.opencontainers.image.created=${{ steps.build.outputs.created_at }}

- name: Log in to private registry
  uses: docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0
  with:
    registry: ${{ vars.DOCKER_REGISTRY }}
    username: ${{ github.actor }}
    password: ${{ secrets.DOCKER_TOKEN_GITEA }}

- name: Build and push
  uses: docker/build-push-action@53b7df96c91f9c12dcc8a07bcb9ccacbed38856a # v7.3.0
  with:
    context: .
    push: true
    provenance: false
    sbom: false
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    build-args: |
      BUILD_GIT_BRANCH=${{ steps.build.outputs.branch }}
      BUILD_GIT_COMMIT=${{ steps.build.outputs.commit }}
      BUILD_GIT_COMMIT_TIME=${{ steps.build.outputs.commit_time }}
      BUILD_CREATED_AT=${{ steps.build.outputs.created_at }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

Do not require a runtime smoke test in the service starter: many services need `.env` values or
runtime secrets. Add one only for a stable, non-secret startup contract. Never use PyPI, npm publish,
GHCR, Docker Hub, or another public destination.

Store the private registry host and private image path as GitHub repository variables. Store its
narrowly scoped token as the `DOCKER_TOKEN_GITEA` GitHub repository secret and authenticate as
`github.actor`. Expose the token only to the gated image job for protected `main` pushes and
same-repository, non-Dependabot pull requests; keep every other pull-request job secretless. Keep the
approved Astral base image directly in the Dockerfile; do not add a runtime-image variable. Do not
put private registry values or credentials in the repository, and do not run `just` in CI.

## Clearly reusable library variant

Only a library treats wheel and sdist files as intentional artifacts. It may use the same package
layout and build backend as an installable service:

```toml
[project]
name = "example-library"
version = "0.0.0"
requires-python = ">=3.14"
classifiers = ["Private :: Do Not Upload"]

[build-system]
requires = ["uv_build>=0.12.3,<0.13"]
build-backend = "uv_build"
```

Use `src/example_library/`, build both wheel and sdist with `uv build`, inspect their contents, and
install the wheel into an isolated environment for a smoke test. Keep publication private and add a
deliberate, documented versioning workflow only when the library truly has releases.

`MANIFEST.in` is a setuptools input that controls extra files in a source distribution. It does not
configure runtime copying into a Docker image and is unnecessary for a service. For a library, prefer
backend-native package-data configuration and add `MANIFEST.in` only when the chosen backend actually
consumes it and the sdist needs files that are otherwise omitted.
