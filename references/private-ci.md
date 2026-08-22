# Build Identity, CI, and Private Image Delivery

Read this reference when GitHub Actions, build metadata, private service images, or Gitea delivery is
selected.

## Contents

- [Expose build identity without releases](#expose-build-identity-without-releases)
- [Harden quality workflows](#harden-quality-workflows)
- [Publish one private image channel](#publish-one-private-image-channel)
- [Protect registry credentials](#protect-registry-credentials)
- [Verify delivery configuration](#verify-delivery-configuration)

## Expose Build Identity Without Releases

- Private NGC services do not have release versions: do not add SemVer bumping, release tags,
  tag-triggered release jobs, changelog automation, version endpoints, or package publication.
- Keep `version = "0.0.0"` only because PEP 621 requires a version for the installable project.
- Inject the Git branch, full commit SHA, and commit timestamp from the trusted build system. Generate
  a separate RFC 3339 UTC image-build timestamp for `org.opencontainers.image.created`.
- Use the commit as artifact identity; branch is display context. Treat `main` and `pr-<number>` image
  tags as mutable CI channels rather than releases or deployment instructions.
- Keep the exact checked-out full SHA as metadata, not as an image tag. Recording it in runtime build
  information and the OCI revision label does not create another registry image reference.
- Do not copy `.git` or run Git in the production container. Use `unknown` for uninjected local source
  identity rather than claiming a deployment provenance.
- Return exactly `branch`, full `commit`, `commit_time`, `python_version`, and `platform` from a
  non-secret `/build-info` or `/info` endpoint and log them once at startup. Derive runtime fields from
  `sys.version` and `platform.platform()`.
- Truncate a commit only in space-limited human presentation. Preserve the full SHA in APIs, structured
  logs, OCI revision labels, and CI metadata.
- Inject the revision of the source actually built. Do not derive identity from a different checkout
  or label a build with a pull-request head SHA while building different synthetic contents.

## Harden Quality Workflows

- Trigger checks for pull requests and protected-branch pushes. Do not add release-tag triggers or
  public publishing workflows.
- Give every workflow a unique, stable `name`. Keep required job names stable unless branch-protection
  settings are updated with the rename.
- Cancel superseded pull-request runs with top-level `concurrency`. Include workflow identity and pull
  request identity in the group, and use a run-unique fallback for non-PR events so protected-branch
  pushes do not cancel each other. Define this policy in the entry workflow; a called reusable
  workflow must use a distinct group if it also declares concurrency.
- Use an explicit supported GA runner image such as `ubuntu-24.04` instead of a migrating `-latest`
  label. Re-check the supported runner list before changing the pinned image.
- Set `timeout-minutes: 5` on every runner-backed job (`runs-on` plus `steps`). Raise only the specific
  job whose measured normal runtime requires more time, keep the smallest reliable bound, and
  document the reason beside the override. GitHub has no workflow-wide job-timeout default. A caller
  job that uses `jobs.<job_id>.uses` cannot set `timeout-minutes`; enforce the bound on every runner
  job inside the called reusable workflow instead. Do not rely on GitHub's 360-minute default.
- Set `permissions: contents: read` at workflow or job scope. Add the smallest write permission only to
  the job that needs it, such as an approved coverage-comment job.
- Keep test and lint jobs free of production and registry secrets.
- Treat pull-request metadata and all contributor-controlled GitHub context as untrusted. Bind values
  through a step's `env` mapping and quote shell variables; never interpolate an expression directly
  into a `run` script.
- Do not check out or execute untrusted pull-request code from privileged `pull_request_target` or
  `workflow_run` jobs. Keep routine validation on `pull_request`.
- For `actions/checkout`, keep the event's exact source revision, use the default shallow fetch unless
  a checked command needs history, and set `persist-credentials: false` unless a later step genuinely
  performs an authenticated Git operation.
- Pin third-party actions to full commit SHAs and retain a same-line tag comment as readable version
  documentation.
- Pin cross-repository reusable workflows to a full commit SHA. On GitHub.com, prefer a
  same-repository `$/.github/workflows/...` reference so the called workflow comes from the caller's
  commit; use `./.github/workflows/...` when GitHub Enterprise Server compatibility is required. Pass
  named secrets, and do not use `secrets: inherit` as a shortcut.
- Do not add `.github/dependabot.yml` or enable routine Dependabot version updates under NGC policy.
  Enable only Dependabot security updates with grouped security updates through repository or
  organization settings.
- Cache uv through its supported setup integration, keyed by the lockfile. A cache never replaces
  `uv.lock`.
- If the formatting capability is selected, run `bun install --frozen-lockfile` before the package
  formatting check. Do not regenerate the lockfile in CI.
- Format workflow YAML with one blank line between step entries and job definitions.
- Run lock validation, Ruff lint, Ruff format check, ty, and every custom check in repository policy.
  Run tests only when selected and use the same selection and thresholds as documented locally.
- Build distributions only for reusable libraries.
- Make downstream build or publication jobs declare every required quality job in `needs`. Do not put
  `continue-on-error` or `always()` on a required gate; reserve them for deliberately non-blocking
  experiments or diagnostic cleanup.
- Avoid path filters on a workflow that supplies a required check unless branch-protection design
  explicitly handles skipped workflows; GitHub can otherwise leave that check pending.
- For multiline Bash, set `shell: bash`, begin with `set -euo pipefail`, and pass dynamic values through
  `env` rather than splicing expressions into the generated script.
- Preserve JUnit, coverage XML, OpenAPI, and image metadata as artifacts only when useful for
  diagnosis. Never upload `.env`, credentials, or verbose secret-bearing logs.
- When the repository has designated workflow owners, protect `.github/workflows/` with a
  `CODEOWNERS` rule and required review. Do not invent an owner merely to add the rule.

## Publish One Private Image Channel

- After all selected quality jobs pass, use one image job to publish `main` for protected `main`
  pushes and `pr-<number>` for same-repository, non-Dependabot pull requests.
- Skip image publication for forks and Dependabot. Do not add a separate pull-request `image-check` or
  non-pushing image-build job.
- Treat that gated job as the only builder for shared environments. Test, staging, trading, and
  production select and pull a published image; they do not run `docker build` or
  `docker compose build`.
- Gate the job itself so it runs only for a `main` push or a trusted same-repository pull request;
  do not rely on workflow branch filters as the credential boundary:

    ```yaml
    if: >-
        (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
        (github.event_name == 'pull_request' &&
        github.event.pull_request.head.repo.full_name == github.repository &&
        github.event.pull_request.user.login != 'dependabot[bot]')
    ```

- Use a pinned `docker/metadata-action` with only `type=ref,event=branch` and
  `type=ref,event=pr`. Because branch pushes trigger only for `main`, these rules produce only `main`
  and `pr-<number>`.
- Do not add SHA, `latest`, SemVer, release, or other tags. Accept the generated
  `org.opencontainers.image.version` only as the mutable CI channel.
- Override OCI revision and creation labels with the exact built commit and generated build timestamp.
- Match Dockerfile build-argument names exactly. Use `BUILD_GIT_BRANCH`, `BUILD_GIT_COMMIT`,
  `BUILD_GIT_COMMIT_TIME`, and `BUILD_CREATED_AT` in the baseline.
- Build and push once with `docker/build-push-action`, its metadata outputs, `push: true`,
  `provenance: false`, and `sbom: false`. The selected NGC Gitea deployment does not support
  provenance or SBOM artifacts. Set `context: .`; the repository root is the only supported NGC CI
  build context.
- Require explicit digest selection before a shared deployment. Do not rebuild separately for staging
  and production.
- Configure registry retention or periodic cleanup for stale `pr-<number>` channels after pull requests
  close. Keep `main` and active PR channels according to operational need; do not solve retention by
  publishing a tag for every commit.

## Protect Registry Credentials

- Keep the private registry host and image path in GitHub repository variables.
- Store the token-owning Gitea service-account name as `DOCKER_USERNAME_GITEA`. Store its narrowly
  scoped package-write token as `DOCKER_TOKEN_GITEA` and pass that fixed username/token pair to the
  registry login action.
- Expose the token only to the gated image job for protected `main` pushes and same-repository,
  non-Dependabot pull requests. Never expose it to fork or Dependabot jobs.
- This policy deliberately trusts same-repository contributors to execute code in the image job.
  Protect write access and review policy accordingly.
- There is no stronger fully automated secret boundary while that same job executes contributor code
  and receives the token. When stronger separation is required, put the token in a protected GitHub
  Environment with required reviewers; accept that each PR image publication then needs approval. Do
  not add a multi-workflow artifact-promotion system to the NGC baseline merely to preserve automation.
- Never target PyPI, npm, GHCR, Docker Hub, another public registry, or a public repository as a
  publication destination. Consuming an approved official vendor base image is allowed.
- Keep the approved Astral base image directly in the Dockerfile; do not add an unnecessary repository
  variable for it.

## Verify Delivery Configuration

- Inspect unique workflow names, event filters, PR concurrency groups, explicit runner labels,
  job-level conditions, `needs`, permissions, secret scope, and exact action or reusable-workflow pins.
- Confirm every runner-backed job has `timeout-minutes: 5` or a narrow documented override. For
  reusable workflow calls, inspect the jobs in the called workflow because the caller job cannot own
  a timeout.
- Confirm the repository's documented quality gates are represented before the image job.
- Verify metadata tags resolve only to `main` or `pr-<number>` for supported events.
- Verify build-argument names match the Dockerfile and that revision/created labels use the same values.
- Do not exercise or claim a registry login or push during a local review unless the user explicitly
  requests and authorizes it.
- When creating or replacing the image workflow, read
  [private-ci-starter.md](private-ci-starter.md) for the representative pinned steps.
