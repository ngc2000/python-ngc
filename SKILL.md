---
name: python-ngc
description: Opinionated NGC baseline for private Python services and reusable libraries using uv. Use only when the user explicitly asks to adopt, apply, audit, or maintain NGC; inspect the requested scope and load only the relevant project and capability guidance.
---

# Build and Maintain an NGC Python Project

Apply a coherent baseline rather than a bag of independent tools. Make project metadata, local commands,
CI, deployable artifacts, runtime configuration, and operational metadata describe and verify the same
system.

## Scope the Work Before Changing It

Identify only the distinctions that affect the request:

- Whether each affected project is a private service or reusable library.
- Whether packaging, runtime commands, or deployment artifacts are in scope.
- Which capabilities are actually used or requested: configuration, logging, quality tools, tests,
  formatting, FastAPI, HTTP clients, containers, Compose, durable state, or private image delivery.

For broad NGC adoption or an audit, record a compact scope summary before editing:

```text
projects: <affected path -> service/library, installable/non-package>
runtime and deployment: <relevant commands and artifacts>
capabilities: <selected guidance>
policy conflicts or documented exceptions: <none or list>
```

For a focused workspace change, inspect only the affected members and their shared root contract. A
repository-wide workspace inventory is part of a broad adoption or audit, not a prerequisite for an
unrelated narrow edit.

## Load Guidance Progressively

For broad adoption, packaging, dependencies, source layout, or project metadata, read
[core-project.md](references/core-project.md). For a focused capability task, read only the matching
reference plus the repository's own instructions:

- **Application configuration or secrets:**
  [configuration.md](references/configuration.md)
- **Ruff, ty, just, pytest, coverage, integration tests, or end-to-end tests:**
  [quality-and-testing.md](references/quality-and-testing.md)
- **Prettier, Bun, Jinja, HTML, JavaScript, CSS, JSON, YAML, or Markdown formatting:**
  [formatting.md](references/formatting.md)
- **A use site that needs an explicit HTTP client:** [httpx2.md](references/httpx2.md)
- **Docker or Compose:** [containers-and-compose.md](references/containers-and-compose.md)
- **FastAPI:** [fastapi.md](references/fastapi.md)
- **Application logging, `colorlog`, `structlog`, structured logs, or audit logs:**
  [structured-logging.md](references/structured-logging.md)
- **Mutable durable state, SQLite, persistent volumes, or infrastructure services:**
  [stateful-services.md](references/stateful-services.md)
- **GitHub Actions, build identity, private image tags, or Gitea delivery:**
  [private-ci.md](references/private-ci.md)
- **Any version, flag, setting, action SHA, or security recommendation that may have changed:**
  [official-sources.md](references/official-sources.md)

Read a capability's linked starter only when creating or substantially replacing that kind of file.
Adapt examples to the repository; never copy optional sections merely because they exist.

## Resolve Policy and Migration Conflicts Explicitly

Use this precedence:

1. Explicit user instructions and documented compatibility, safety, regulatory, or runtime
   constraints.
2. Established public, persistence, deployment, and operational contracts unless the user authorizes
   a migration.
3. NGC organization policy: star naming, private publication, unversioned Docker services,
   Conventional Commits, Gitea image delivery, and lazydocker.
4. NGC defaults for new work.
5. Capability examples.

Do not let a lower level silently override a higher one. Surface a conflict before making a broad or
compatibility-breaking change. Treat words such as "default" and "prefer" as defaults, not migration
mandates.

Preserve justified existing suppressions and deviations during incremental adoption. Ratchet them
down: prohibit unexplained additions, remove stale entries, and require a narrow scope and reason for
every new exception. Add a removal condition when the exception is temporary. Do not weaken a gate
merely to make a command pass.

## Naming

NGC uses IAU-approved star names for projects. Treat this as organization policy, not a universal
Python convention.

## Start With Evidence

- Inspect repository instructions, dirty-worktree state, and the files that own the requested
  behavior. Preserve established contracts and unrelated changes.
- For broad adoption or audit work, also inspect project metadata, lockfiles, runtime entry points,
  assets, quality policy, CI, and selected deployment files.
- Use the detailed inventories and verification matrices in a capability reference only when that
  capability is being changed; do not manufacture a repository-wide matrix for a narrow task.

For broad adoption or audit work, or when its root-level evidence is relevant, run the bundled
read-only helper when Python is available:

```text
python <skill-directory>/scripts/audit_repo.py <repository>
```

The helper reports single-project or workspace-root evidence, assumes the NGC CI build context is the
repository root, and does not expand workspace members. Use `--json` for machine-readable output and
`--strict` only when warnings should fail. Treat findings as leads to inspect, not an exhaustive model
or permission for mechanical rewrites.

## Work Incrementally

- Apply only the project and capability guidance selected by the request.
- For a new repository or broad NGC adoption, keep a repository-local, committed root `AGENTS.md` as
  the shared agent contract. Add a nested `AGENTS.md` only for genuine scoped differences; never copy
  the root rules into each subdirectory. Preserve an intentional existing instruction hierarchy, and
  make required vendor-specific files thin pointers to the shared source.
- For a new repository or broad NGC adoption, keep durable design, architecture, rationale, and
  operational invariants in a committed `docs/` directory. Let the repository choose its structure.
  Do not create exhaustive handwritten catalogs of generated APIs, configuration, or tool settings
  that will drift from their authoritative source.
- Keep command bodies in the committed `justfile` and numeric gates in the machine-readable
  configuration owned by the enforcing tool. Have CI call the check-only recipes instead of copying
  their shell commands; keep `README.md`, `AGENTS.md`, and `docs/` focused on intent and recipe names.
- Prefer small compatible migrations over repository-wide churn.
- Keep business logic in the package. Let scripts orchestrate package APIs rather than become a
  second implementation tree.
- Use Conventional Commits for authored commits and squash-merge or pull-request titles. Prefer
  squash commits when repository policy allows them; do not add commit-message tooling by default.
- Never publish repositories, Python distributions, JavaScript packages, or service images to a
  public destination under the NGC private profile.
- For a new deployable application, select application logging and apply its package defaults. In an
  existing repository, preserve an established logging API and output contract unless logging work or
  a migration is in scope.
- Do not introduce tests, HTTP clients, JavaScript tooling, Compose, or durable state machinery when
  the repository does not use or request that capability.

## Verify Before Handoff

Run the repository's canonical check-only recipe when present:

```text
just check
```

If the selected scope does not yet have a justfile, run the direct equivalents rather than inventing
an undocumented recipe:

```text
uv lock --check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
```

Also run repository-approved tests and every custom check discovered in its documented quality policy.
Use the selected capability references for additional checks. Build, inspect, and smoke-test a wheel
only when a reusable library owns distributions as artifacts. For a service, validate its runtime
commands, assets, configuration, workflow, and selected deployment artifacts. Keep runtime smoke tests
conditional on a stable, non-secret startup contract.

Report the selected scope, changes, checks run, unavailable checks, remaining exceptions, and any
registry or production action that was not exercised. Never claim a deployment or registry push was
tested locally when it was not.
