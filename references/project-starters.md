# Project Starter Examples

Read this reference only when creating or substantially replacing project metadata or root repository
files. Select the service or library variant; do not combine their artifact policies.

## Installable Private Service

This baseline is an installable `src/` package whose Docker image is the deployable artifact:

```toml
[project]
name = "example-service"
version = "0.0.0"
description = "Private internal service."
readme = "README.md"
requires-python = ">=3.14"
classifiers = ["Private :: Do Not Upload"]
dependencies = [
    "colorlog>=6.12,<7",
    "structlog>=26.1,<27",
]

[dependency-groups]
dev = [
    "ruff>=0.16,<0.17",
    "ty>=0.0.62,<0.1",
]

[build-system]
requires = ["uv_build>=0.12.3,<0.13"]
build-backend = "uv_build"

[tool.ty.terminal]
output-format = "concise"
```

Add capability dependencies with `uv add`; do not copy FastAPI, configuration, database, or HTTP
client dependencies into a service that does not use them. The deployable-service logging baseline
uses `colorlog` for the human stdout formatter and `structlog` for structured event data. A simple
non-service tool or reusable library does not need both. Read
[quality-and-testing.md](quality-and-testing.md) for the authoritative Ruff config.

PyPI rejects the `Private :: Do Not Upload` classifier, but other registries may not. Keep Python
publication credentials and workflows absent as a separate control.

## Root Ignore Entries

Anchor local state so similarly named package-data directories remain trackable:

```gitignore
/.env
/config.toml
/data/
```

Mirror the selected local-state and secret exclusions in `.dockerignore`. Add `/.secrets/` only when
the repository actually uses local mounted secret files.

## Text File Baseline

`.editorconfig` guides compatible editors and formatters; it is not a Git setting:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 4
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false
```

Use `.gitattributes` for Git line-ending normalization:

```gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
```

Git normalization does not add a missing final newline; EditorConfig-aware editors and the selected
formatters own that check. When adopting these files in an established repository, review any
one-time line-ending normalization separately from functional changes.

## Reusable Library Variant

Only a reusable library treats wheel and sdist files as intentional artifacts:

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

Use `src/example_library/`, build wheel and sdist with `uv build`, inspect both, and install the wheel
in isolation. Add a release/versioning policy only when the library actually has releases.
