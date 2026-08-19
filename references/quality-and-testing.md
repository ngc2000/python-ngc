# Quality Commands and Testing

Read this reference when the repository uses Ruff, ty, just, pytest, coverage, integration tests, or
end-to-end tests.

## Contents

- [Align broad quality gates](#align-broad-quality-gates)
- [Configure Ruff and ty](#configure-ruff-and-ty)
- [Migrate suppressions with a ratchet](#migrate-suppressions-with-a-ratchet)
- [Use just as the command interface](#use-just-as-the-command-interface)
- [Design the primary Python test suite](#design-the-primary-python-test-suite)
- [Protect live and time-sensitive tests](#protect-live-and-time-sensitive-tests)
- [Treat non-Python checks as additional](#treat-non-python-checks-as-additional)

## Align Broad Quality Gates

Use this matrix for broad quality-policy or CI work. For a focused Ruff, ty, or test change, inspect
only the relevant local and CI commands instead of inventorying unrelated gates.

Inventory every authoritative quality rule before changing commands:

| Policy or check          | Local mutating command | Local check-only command | CI command     | Threshold/artifact      |
| ------------------------ | ---------------------- | ------------------------ | -------------- | ----------------------- |
| Lock validity            | n/a                    | `uv lock --check`        | same           | no lock rewrite         |
| Ruff lint                | safe fixes allowed     | `ruff check .`           | same           | zero diagnostics        |
| Ruff format              | `ruff format .`        | `ruff format --check .`  | same           | no diff                 |
| Type checking            | n/a                    | `ty check`               | same           | approved rules          |
| Custom repository checks | repository-specific    | repository-specific      | same policy    | documented output       |
| Tests/coverage           | repository-specific    | repository-specific      | same selection | one authoritative floor |

- Discover custom scripts and checks named in repository instructions. Do not replace them with a
  generic tool list or omit them from CI accidentally.
- Define each numeric gate once in the machine-readable configuration owned by its tool. For example,
  keep the coverage floor in `pyproject.toml`; do not repeat it as a CLI flag, workflow value, or prose
  number. Commands and CI consume that configuration, while documentation explains the policy and
  names the canonical recipe.
- Keep test selection in the canonical just recipes. Do not let local commands, CI, or documentation
  independently reconstruct marker expressions or test paths.
- Let local quality commands apply safe formatting or fixes when that is repository policy. CI must be
  non-mutating.

## Configure Ruff and ty

- Run Ruff as both linter and formatter: `ruff check` before `ruff format`. In CI, use
  `ruff check .` and `ruff format --check .`.
- Use `select = ["ALL"]` with the NGC ignore allowlist below. Keep `PGH004` and the `RUF` family
  enabled; additions outside this list need a concrete project reason.

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    # Ruff formatter conflicts
    "W191", # tab-indentation
    "E111", # indentation-with-invalid-multiple
    "E114", # indentation-with-invalid-multiple-comment
    "E117", # over-indented
    "D206", # docstring-tab-indentation
    "D300", # triple-single-quotes
    "Q000", # bad-quotes-inline-string
    "Q001", # bad-quotes-multiline-string
    "Q002", # bad-quotes-docstring
    "Q003", # avoidable-escaped-quote
    "Q004", # unnecessary-escaped-quote
    "COM812", # missing-trailing-comma
    "COM819", # prohibited-trailing-comma

    # Google-style docstrings
    "D203", # incorrect-blank-line-before-class
    "D213", # multi-line-summary-second-line
    "D406", # missing-new-line-after-section-name
    "D407", # missing-dashed-underline-after-section
    "D413", # missing-blank-line-after-last-section
    "D415", # missing-terminal-punctuation

    # NGC project policy
    "CPY", # flake8-copyright
    "EXE", # flake8-executable
    "TD", # flake8-todos
    "FIX", # flake8-fixme
    "ERA", # commented-out-code
]
```

Run the locked formatter and ensure it emits no incompatible-rule warning. Re-check the official
formatter-conflict list when the Ruff minor range changes.

- Let Ruff and ty infer the Python version from `requires-python` unless a deliberate override is
  needed.
- Run `uv run ty check`. Begin without broad suppressions; add the narrowest rule, file override, or
  boundary annotation only after inspecting a real diagnostic. Do not make `Any` the default escape
  hatch.

## Migrate Suppressions With a Ratchet

- For new code, do not add `noqa`, broad `extend-ignore`, broad exclusions, or new per-file ignores
  merely to pass CI. Fix or refactor the cause.
- During adoption in an established repository, preserve existing justified suppressions long enough
  to avoid an unrelated rewrite. Capture the baseline and prevent unexplained growth.
- Require every additional project-wide or per-file exception to name the rule and explain why the
  diagnostic is not actionable. State a removal condition when the exception is temporary. Prefer a
  narrow boundary annotation over an entire directory exemption.
- Remove entries for paths or diagnostics that no longer exist. Audit blanket `noqa` and type-ignore
  comments separately because they can hide future errors.
- A local suppression remains a last resort for a demonstrated false positive; do not convert normal
  refactoring cost into a permanent exception.

## Use just as the Command Interface

- Keep a committed justfile as the canonical interface for developers, agents, and CI. For a new
  project, use the small vocabulary `format`, `lint`, `test`, and `check` where applicable; preserve a
  clear established equivalent instead of renaming recipes without benefit.
- Keep command bodies in recipes rather than copying shell sequences into `README.md`, `AGENTS.md`,
  workflow YAML, or durable design documents. A recipe may call a package-manager script when that
  package owns a tool such as Prettier.
- Make `check` non-mutating and merge-equivalent. It aggregates the selected lock, lint, format-check,
  type, custom-check, and default-test gates. CI invokes `just check`, or its constituent check-only
  recipes when jobs need parallelism or separate artifacts.
- Keep `format` as the intentional mutating entry point. Do not let a CI recipe rewrite source,
  metadata, or lockfiles.
- Set `default-list := true` for a new justfile so bare `just` lists recipes. Preserve an established
  equivalent default recipe unless changing it has a concrete benefit.
- Give only public recipes short useful comments. Hide helpers with `_` or `[private]`.
- Expect `just` on developer machines. Install a reviewed pinned version on clean CI runners before
  invoking recipes; do not add `rust-just` as a Python dependency.
- Do not add a `sync` recipe; `uv run` synchronizes development dependencies automatically. Install
  non-Python dependencies explicitly during setup and on clean CI runners.
- Avoid generic Docker lifecycle recipes under NGC policy because operators use lazydocker.
- Give a port-binding recipe an optional port only when the recipe owns the port argument. If typed
  application configuration owns it, document the supported override instead of duplicating it in
  the recipe.
- `just` uses `sh` by default, including on Windows when a compatible `sh` is available. If the
  repository does not require that toolchain, use `windows-shell`, a script recipe, or a checked-in
  cross-platform script. Move logic beyond a few commands into a script.
- Keep destructive actions out of the starter interface. For a genuinely frequent destructive
  action, use `[confirm]` and an exact narrow target.

## Design the Primary Python Test Suite

- Honor repository policy. Do not introduce pytest, coverage, or a test CI gate when the project
  explicitly does not use tests.
- With a `src` layout, use pytest `--import-mode=importlib`. Enable strict configuration and strict
  markers when supported by the locked pytest version.
- Organize tests by behavior: fast unit tests, boundary/integration tests, and explicitly selected
  end-to-end tests. Mirror source paths for unit tests when it improves discovery; keep integration
  and end-to-end trees organized around public seams and scenarios.
- Test public behavior rather than implementation detail. Use fixtures with narrow scope,
  deterministic clocks and randomness, explicit timeouts, and cleanup that runs after failure.
- Prefer a fast coverage-free iteration command and a separate coverage merge gate for new projects.
  Preserve an established merge-equivalent `test` command when intentional; do not force a split for
  style alone.
- Measure branch coverage, show missing lines, emit XML when CI consumes it, and use a realistic
  non-decreasing threshold. Do not exclude difficult code merely to raise the percentage.
- Mark end-to-end tests with `e2e`. Exclude them from the default test command and require an explicit
  opt-in such as `just test e2e`.
- Enable parallel tests only after proving isolation. Give each worker unique ports, files, databases,
  clocks, and mutable process state.
- For services, include contract tests for settings validation, health/readiness behavior, build
  metadata, graceful startup/shutdown, and OpenAPI generation when FastAPI is selected. For libraries,
  test the public API, supported Python range, and installed wheel.

## Protect Live and Time-Sensitive Tests

- Default to fakes, transports, sandbox services, or simulation accounts. Never let the default suite
  contact a live service or production account.
- Require an explicit live-test command plus an unmistakable opt-in variable or flag. Validate the
  selected environment, endpoint, and account against an allowlist before the first side effect.
- Keep credentials in approved secret sources and out of test IDs, assertion messages, captured
  responses, and uploaded artifacts.
- Re-check volatile prerequisites at collection and immediately before each scenario. Examples include
  market windows, clock windows, service readiness, account mode, and remaining execution time.
- An explicitly requested live run with missing credentials or the wrong account must fail clearly;
  a legitimately unavailable time window may skip with a specific reason when repository policy
  allows it.
- Set per-request timeouts, per-outcome deadlines, and one hard suite deadline. Stop after the first
  unsafe or infrastructure-invalidating failure.
- Disable parallel execution unless live resources are independently provisioned per worker.
- Make side effects bounded, identifiable, and reversible where the external system permits it.
  Always run cleanup, but do not hide the original failure when cleanup also fails.
- Record enough non-secret identifiers for diagnosis without logging credentials, full payloads, or
  personal data.

## Treat Non-Python Checks as Additional

- Discover existing non-Python test commands from committed package-manager scripts or repository
  policy. Do not introduce them solely because Prettier or Bun is present.
- Keep the Python unit/integration test policy primary. Run established non-Python checks as an
  additional gate after their frozen dependency installation.
- Keep their selection explicit and deterministic. Do not let a package runner auto-install missing
  dependencies or silently widen the test set in CI.
- Report these checks separately so a formatting-tool dependency is not mistaken for an additional
  application test framework.
