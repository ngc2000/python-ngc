# Private CI Starter Examples

Read this reference only when creating or substantially replacing build-identity code or the private
image job. Keep repository-specific quality jobs outside these snippets and pin every action to a
reviewed full commit SHA.

## Runtime Build Information

Private services expose source and runtime identity rather than a release version:

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

Return exactly those fields from `/build-info` or `/info` and log them once at startup. Keep the full
commit SHA in machine-readable output and the OCI revision label, but do not publish it as an image
tag; the only baseline tags are `main` and `pr-<number>`.

## Gated Image Job

Run this job only after the selected quality jobs pass. The gate deliberately gives the registry token
to protected `main` pushes and trusted same-repository, non-Dependabot pull requests:

```yaml
if: >-
    (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
    (github.event_name == 'pull_request' &&
    github.event.pull_request.head.repo.full_name == github.repository &&
    github.event.pull_request.user.login != 'dependabot[bot]')
```

After checkout and Buildx setup, collect identity from the exact checked-out commit and publish from
repository-root context:

```yaml
- name: Collect build identity
  id: identity
  shell: bash
  env:
      BUILD_GIT_BRANCH: ${{ github.head_ref || github.ref_name }}
  run: |
      set -euo pipefail
      commit="$(git rev-parse HEAD)"
      commit_time="$(git show -s --format=%cI "$commit")"
      created_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
      {
        echo "branch=$BUILD_GIT_BRANCH"
        echo "commit=$commit"
        echo "commit_time=$commit_time"
        echo "created_at=$created_at"
      } >> "$GITHUB_OUTPUT"

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
          org.opencontainers.image.revision=${{ steps.identity.outputs.commit }}
          org.opencontainers.image.created=${{ steps.identity.outputs.created_at }}

- name: Log in to private registry
  uses: docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0
  with:
      registry: ${{ vars.DOCKER_REGISTRY }}
      username: ${{ vars.DOCKER_USERNAME_GITEA }}
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
          BUILD_GIT_BRANCH=${{ steps.identity.outputs.branch }}
          BUILD_GIT_COMMIT=${{ steps.identity.outputs.commit }}
          BUILD_GIT_COMMIT_TIME=${{ steps.identity.outputs.commit_time }}
          BUILD_CREATED_AT=${{ steps.identity.outputs.created_at }}
      cache-from: type=gha
      cache-to: type=gha,mode=max
```

Store `DOCKER_USERNAME_GITEA` as the actual token-owning service account. Keep the token scoped to
package writes and expose it only to this gated job. Use a protected GitHub Environment with required
reviewers when PR publication needs a stronger, manually approved boundary.
