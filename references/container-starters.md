# Container Starter Examples

Read this reference only when creating or substantially replacing a service Dockerfile or deployment
Compose file. The examples assume an installable pure-Python service, repository-root CI context, and
a published private image. Adapt package names, ports, assets, health paths, and writable state.

## Single-Stage Service Dockerfile

Use a builder/runtime split only when it removes compilers, native headers, build tools, or artifacts
from production.

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
    && install -d -m 0750 -o 10001 -g 10001 /app/data /app/data/logs

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]

CMD ["python", "-m", "uvicorn", "example_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

CI must build this with repository-root `context: .`. Ensure every runtime asset is packaged or copied;
do not add a Dockerfile `VOLUME`. Keep credentials, local configuration, mutable data, caches, tests,
and source-control data out of the context. The explicit data mount owns both mutable application state
and the bounded structured log files when logging is selected.

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
