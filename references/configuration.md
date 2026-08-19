# Configuration, Secrets, and Source Precedence

Read this reference when the project loads application configuration, dotenv files, TOML files,
environment overrides, or secret-file values.

## Contents

- [Define source ownership](#define-source-ownership)
- [Specify and test precedence](#specify-and-test-precedence)
- [Maintain safe examples](#maintain-safe-examples)
- [Keep secrets on approved sources](#keep-secrets-on-approved-sources)
- [Validate without rejecting unrelated environment](#validate-without-rejecting-unrelated-environment)
- [Verification matrix](#verification-matrix)

## Define Source Ownership

Document each source as a contract before implementing it:

| Source              | Intended contents                            | Unknown-value policy                                                                 |
| ------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------ |
| Process environment | Deployment overrides and secrets             | Ignore unrelated process variables; validate owned names and values                  |
| Local `.env`        | Developer overrides and local secrets        | Allow variables owned by multiple local runtime roles; lint known prefixes and names |
| `config.toml`       | Non-secret application settings              | Reject unknown sections and keys owned by the application                            |
| Code defaults       | Optional safe defaults                       | Validate defaults through the same typed model                                       |
| Secret files        | Platform-mounted secrets only when supported | Accept only explicitly declared `_FILE` alternatives                                 |

Use `pydantic-settings` or an equivalent typed loader. Parse configuration once at startup, fail with
actionable source-aware errors, and redact secret values from validation output and representations.
On Python 3.14, use the standard-library `tomllib` to read TOML; do not add `tomli` or a general TOML
package merely for parsing. `tomllib` does not write TOML, so add a writer only when the application
actually generates TOML rather than reading committed or operator-owned configuration.

## Specify and Test Precedence

- Use an explicit precedence such as process environment > `.env` > `config.toml` > code defaults.
- When customizing Pydantic settings sources, remember that the first returned callable has the
  highest priority. Do not rely on a comment or README description as proof of behavior.
- Add collision tests that exercise the supported sources and prove their order. Cover explicit
  initializer behavior or source disablement only when the application uses those features.
- Keep the documented precedence, implementation source tuple, examples, and tests synchronized.

## Maintain Safe Examples

- Treat `config.example.toml`, every profile-specific `*.example.toml`, and `.env.example` as
  executable documentation rather than informal snippets.
- Group TOML settings into named sections. Write required non-secret values as active assignments
  with safe examples. Leave only optional values with working code defaults commented out.
- In `.env.example`, write every required variable as an active assignment. Use an empty or
  unmistakably fake value for secrets. Leave optional overrides with working defaults commented out.
- Explain source precedence and the local copy step at the top of each example.
- Prefer one canonical example plus small environment overlays when complete copies would drift. If
  separate full examples are operationally necessary, validate all of them against the same settings
  schema and compare their owned key inventories.
- Keep ownership visible when one local `.env` contains both Compose interpolation and application
  settings. Document whether Compose only interpolates a value, also injects it through `env_file`, or
  overrides it through `environment`; application settings must tolerate unowned process variables.

### Starter Examples

Use named TOML sections and keep required non-secret values active. Leave optional values commented
only when code provides the shown default:

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
# format = "human"
# color = "auto"

[integrations]
api_base_url = "https://internal.example.test"
```

Keep `.env.example` safe to commit and use empty or unmistakably fake secret values:

```dotenv
# Copy to .env. Never commit real values.

APP_IMAGE=registry.example.test/team/example-service@sha256:0000000000000000000000000000000000000000000000000000000000000000

# APP_ENVIRONMENT=development
# APP_DATA_DIR=data
# SERVER_HOST=127.0.0.1
# SERVER_PORT=8000
# HOST_PORT=8000
# LOG_LEVEL=INFO
# LOG_FORMAT=human
# LOG_COLOR=auto

INTERNAL_API_TOKEN=
```

These names are examples, not a universal schema. Keep only variables owned by the selected runtime
and document whether Compose merely interpolates or also injects each value.

## Keep Secrets on Approved Sources

- Keep secrets out of TOML, command-line arguments, image build arguments, image labels, and committed
  files.
- Accept direct secrets from the process environment or an ignored local `.env` by default.
- Add a `_FILE` alternative only when the actual deployment platform mounts secret files and the
  application implements a resolver.
- For each direct/`_FILE` pair, reject simultaneous values, unreadable files, empty required results,
  and non-regular files when appropriate. Strip only the terminator explicitly allowed by the secret
  contract; do not silently normalize arbitrary content.
- Define secret source allowlists per field. A model containing both secret and non-secret settings
  must not accidentally make every field eligible for TOML or file-secret loading.
- Test that values placed in forbidden sources are ignored or rejected, rather than merely documenting
  that they should not be used.

## Validate Without Rejecting Unrelated Environment

- Reject unknown keys inside application-owned TOML sections because misspellings there are likely
  configuration errors.
- Do not configure a settings model to reject every unrelated process environment variable. A process
  inherits operating-system and platform variables that are outside the application's schema.
- A shared local `.env` may intentionally contain variables for several runtime roles or Compose.
  Validate the union of declared owners, or use explicit prefixes/per-role files, rather than making
  each settings model reject the other role's variables.
- Detect near-miss or unknown variables within an owned prefix through a startup lint or example-file
  validator. Report the exact source and candidate name.
- Validate ranges, URLs, paths, enumerations, and cross-field constraints after source resolution.

## Verification Matrix

When tests are in repository policy, cover at least:

| Behavior              | Required check                                                         |
| --------------------- | ---------------------------------------------------------------------- |
| Defaults              | Optional settings load without local files                             |
| Required settings     | Missing values fail clearly                                            |
| Precedence            | A conflicting value in every source chooses the documented winner      |
| Unknown TOML          | Unknown section/key is rejected                                        |
| Unrelated environment | Unowned process variables do not break startup                         |
| Owned misspelling     | Unknown owned-prefix variable is reported                              |
| Secrets               | Forbidden TOML values do not become effective                          |
| Direct versus `_FILE` | Conflict, unreadable, empty, and success cases                         |
| Profiles              | Every committed example validates for its intended runtime/environment |
| Redaction             | Exceptions and model representations do not expose secret values       |

Do not read or print a developer's real `.env` during a repository audit. Inspect only committed
examples and source definitions unless the user explicitly authorizes secret-bearing runtime checks.
