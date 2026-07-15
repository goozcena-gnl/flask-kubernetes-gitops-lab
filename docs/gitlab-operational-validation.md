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
