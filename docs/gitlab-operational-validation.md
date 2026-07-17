# GitLab operational validation

## Objective

Validate the real delivery path from GitLab CI to an immutable image in the
GitLab Container Registry.

## Source of truth

GitHub `main` remains the canonical Git history.

The GitLab repository is used as a CI and registry mirror. Changes must not be
merged independently in GitLab because this would cause the histories to
diverge.

## Expected pipeline

### Merge request or feature branch

- validate
- build_image
- no publication

### Default branch

- validate
- build_image
- publish_image

## Expected image

```text
$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

The mutable `latest` tag is intentionally not used.

## Evidence to record

| Evidence | Value |
|---|---|
| GitHub commit SHA | `<COMMIT_SHA>` |
| GitLab pipeline URL | `<PIPELINE_URL>` |
| Published image | `<REGISTRY_IMAGE>:<COMMIT_SHA>` |
| Image digest | `<SHA256_DIGEST>` |
| Validation job | `<PASS/FAIL>` |
| Buildah build job | `<PASS/FAIL>` |
| Registry publication job | `<PASS/FAIL>` |

## Executed validation

| Evidence | Value |
|---|---|
| GitLab merge-request pipeline | `2682666374` |
| Merge-request commit | `3883cd4c6760e0e67d31f19fa304f9a5cdac399e` |
| MR validation job | PASS |
| MR Buildah job | PASS |
| MR publication job | Not executed, as intended |
| GitHub canonical main commit | `df1f45a8c841238bfdc1865b2f6c569f0609a440` |
| GitLab main pipeline | `<PIPELINE_URL>` |
| GitLab main validation job | PASS |
| GitLab main Buildah job | PASS |
| GitLab main publication job | PASS |
| Published image | `registry.gitlab.com/goozcena-gnl/test-lab:df1f45a8c841238bfdc1865b2f6c569f0609a440` |
| Published digest | `<REPOSITORY_DIGEST>` |
| Docker health | `healthy` |
| Runtime user | `10001:10001` |
| Read-only root filesystem | PASS |
| `/healthz` | PASS |
| `/readyz` | PASS |
| Mutable `latest` tag | Absent |