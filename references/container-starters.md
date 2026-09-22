# Container Starter Examples

Read this reference only when creating or substantially replacing a service Dockerfile or deployment
Compose file. The examples assume an installable pure-Python service, repository-root CI context, and
a published private image. Adapt package names, ports, assets, health paths, and writable state.

## Multi-Stage Service Dockerfile

Use a pinned uv/Python image to build a dependency-only environment and an application wheel. Copy the
dependencies into the matching slim Python runtime, then install the wheel in its own layer so source
changes preserve the dependency layer.

```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.5-python3.14-trixie-slim AS dependencies

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

FROM dependencies AS builder

COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel --out-dir /dist

FROM python:3.14-slim-trixie AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    APP_ENVIRONMENT=production

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid 10001 --no-create-home app \
    && install -d -m 0750 -o 10001 -g 10001 /app/data /app/data/logs

COPY --from=dependencies --chown=10001:10001 /app/.venv /app/.venv

USER 10001:10001

RUN --mount=from=dependencies,source=/usr/local/bin/uv,target=/bin/uv \
    --mount=from=builder,source=/dist,target=/dist \
    uv pip install --python /app/.venv/bin/python \
    --no-deps --no-index --no-cache --compile-bytecode /dist/*.whl

ARG BUILD_GIT_BRANCH=unknown
ARG BUILD_GIT_COMMIT=unknown
ARG BUILD_GIT_COMMIT_TIME=unknown
ARG BUILD_CREATED_AT=1970-01-01T00:00:00Z

LABEL org.opencontainers.image.revision="${BUILD_GIT_COMMIT}" \
      org.opencontainers.image.created="${BUILD_CREATED_AT}"

ENV BUILD_GIT_BRANCH="${BUILD_GIT_BRANCH}" \
    BUILD_GIT_COMMIT="${BUILD_GIT_COMMIT}" \
    BUILD_GIT_COMMIT_TIME="${BUILD_GIT_COMMIT_TIME}"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

CMD ["python", "-m", "uvicorn", "example_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

The builder image reference is `ghcr.io/astral-sh/uv` plus the
`0.12.5-python3.14-trixie-slim` tag. Keep that uv version explicit. The runtime image must retain the
matching system-Python path and ABI; do not substitute a differently based Python image without
rebuilding and testing the environment there.

CI must build this with repository-root `context: .`. Add `.venv` to `.dockerignore`. Include any
additional packaging inputs, such as license files, in the wheel-builder stage. Package runtime assets
into the wheel or copy each unpackaged asset explicitly before the build-identity arguments; do not
copy the repository wholesale into the runtime. Asset-only edits should not rebuild the wheel unless
those assets belong to the package.

The runtime copies `/app/.venv` from `dependencies`, which excludes the application. The wheel install
uses the locked environment without resolving dependencies, and its mounted uv binary and wheel are
absent from the final image. Keep build identity below all filesystem operations so metadata changes
preserve their layers.

Do not add a Dockerfile `VOLUME`. Keep credentials, local configuration, mutable data, caches, tests,
and source-control data out of the context. The explicit data mount owns both mutable application
state and the bounded structured log files when logging is selected.

## Image-Only Compose

Deployment Compose selects an image produced by CI and never builds source:

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

Leave `pull_policy` unset. Use a reviewed digest for shared environments, keep host exposure narrow,
and use platform-managed secrets there. The ignored local `.env` may supply both Compose interpolation
and application runtime values; document that dual role and ensure application settings ignore
unowned process variables.
