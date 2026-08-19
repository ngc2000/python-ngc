# Format Non-Python Files With Prettier

Read this reference only when the repository uses Prettier or maintains supported non-Python files.

## Contents

- [Tool ownership](#tool-ownership)
- [Installation and configuration](#installation-and-configuration)
- [Jinja templates](#jinja-templates)
- [Commands and verification](#commands-and-verification)

## Tool Ownership

- Keep Ruff authoritative for Python and Prettier authoritative for JavaScript, TypeScript, CSS,
  HTML/Jinja, JSON, YAML, and Markdown.
- Ruff 0.16 and later can also format Python code blocks discovered inside Markdown. When Prettier is
  selected as the Markdown owner, keep the formatters disjoint by adding `extend-exclude = ["*.md"]`
  under `[tool.ruff]` (or appending that pattern to the existing setting).
- Do not add linter formatting rules that fight either formatter.
- Do not add Prettier or Bun when the repository has no maintained files that need this capability.

## Installation and Configuration

- Install exact local versions of Prettier and every plugin in `devDependencies`; commit
  `package.json` and the selected package-manager lockfile.
- Set `private = true` and `license = "UNLICENSED"`. Do not add a publish script or public registry
  configuration.
- Invoke the local binary through a package script so CI never downloads an unreviewed latest
  formatter implicitly.
- Prefer `.prettierrc.toml` for a new NGC project with `printWidth = 100`, `tabWidth = 4`, and
  `useTabs = false`. Preserve an established valid config format unless migration has a concrete
  benefit.
- Commit a small `.prettierignore`. Ignore generated output, dependencies, caches, coverage artifacts,
  vendored/minified files, secrets, and local state. Do not ignore maintained files merely to pass the
  check.

## Jinja Templates

- Pin `prettier-plugin-jinja-template` and scope its `jinja-template` parser override to the actual
  template paths. Do not force it onto unrelated HTML.
- Minimize every ignored range to the smallest independently safe element. Use Jinja comments
  (`{# prettier-ignore-start #}` / `{# prettier-ignore-end #}`) when markers should disappear from
  rendered HTML, or HTML comments when they should remain.
- Do not split one executable `<script>` into multiple executable tags merely to isolate a Jinja line;
  separate tags can change scope and execution semantics.
- Prefer moving a templated value into a minimal ignored inert
  `<script type="application/json">`, then read it from normally formatted or external JavaScript. If
  that is unsafe, ignore the affected executable script as a whole.
- Do not use `{% raw %}` for formatter suppression because it changes template rendering semantics.
- Prefer external JavaScript for substantial logic. Serialize server data with Jinja's `tojson`
  filter rather than `safe` or hand-built JSON. A static inline script without Jinja needs no
  suppression.

## Commands and Verification

- Keep distinct mutating and check-only scripts: `prettier . --write` locally and
  `prettier . --check` for verification. Let the selected just recipes call those local package
  scripts, and have CI invoke the check-only recipe rather than duplicate the Prettier command.
- On a clean runner, run `bun install --frozen-lockfile` before the package script. `bun run` is not a
  replacement for a frozen install.
- Review formatting changes, especially Jinja whitespace, executable scripts, Markdown wrapping, and
  YAML string semantics.
- Keep Prettier installation and checking conditional on this capability in local documentation,
  just recipes, and CI.
