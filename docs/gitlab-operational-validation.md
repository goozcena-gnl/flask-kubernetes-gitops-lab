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
- security_scan
- no publication

### Default branch

- validate
- build_image
- security_scan
- publish_image

## Expected image

```text
$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

The mutable `latest` tag is intentionally not used.

## Evidence to record for a future run

The values below are execution-time fields, not retained evidence. Record an
exact value only when it can be sanitized safely; otherwise mark it private or
not retained.

| Evidence | Value |
|---|---|
| GitHub commit SHA | Record the exact 40-character SHA |
| GitLab pipeline URL | Record only if public; otherwise mark private/not retained |
| Published image | Record the sanitized registry path and immutable SHA tag |
| Image digest | Record the `sha256:` repository digest |
| Validation job | Record `PASS` or `FAIL` from the executed job |
| Buildah build job | Record `PASS` or `FAIL` from the executed job |
| Security job | Record SBOM, full report, and policy-gate result |
| OCI artifact digest | Record the build artifact's manifest digest |
| Registry publication job | Record `PASS`, `FAIL`, or `NOT RUN` |

## Reproducible supply-chain phase

| Evidence | Status |
|---|---|
| Project CI Lint/default-branch simulation | VALIDATED — syntax correct; validate, build, security, and publish jobs present |
| Feature-branch validate job | NOT VALIDATED — branch is not present in the stale GitLab mirror |
| Feature-branch Buildah job | NOT VALIDATED — branch is not present in the stale GitLab mirror |
| Feature-branch security job | NOT VALIDATED — branch is not present in the stale GitLab mirror |
| CycloneDX and vulnerability artifacts | NOT VALIDATED in GitLab |
| Default-branch publication | NOT VALIDATED — no automatic merge is authorized |
| New registry digest handoff | NOT VALIDATED |

Local execution with the exact pinned Buildah and Trivy job images is recorded
in the [validation report](validation-report.md). It proves tool and OCI-layout
compatibility, not GitLab runner or registry behavior.

## Historical executed validation

The following run predates the lock, SBOM, vulnerability-gate, and
registry-digest handoff controls. It must not be read as validation of the new
supply-chain path.

| Evidence | Value |
|---|---|
| GitLab merge-request pipeline | `2682666374` (private mirror; ID retained, URL not public) |
| Merge-request commit | `3883cd4c6760e0e67d31f19fa304f9a5cdac399e` |
| MR validation job | PASS |
| MR Buildah job | PASS |
| MR publication job | Not executed, as intended |
| GitHub canonical main commit | `df1f45a8c841238bfdc1865b2f6c569f0609a440` |
| GitLab main pipeline | Private mirror; URL not retained in the public repository |
| GitLab main validation job | PASS |
| GitLab main Buildah job | PASS |
| GitLab main publication job | PASS |
| Published image | `registry.gitlab.com/goozcena-gnl/test-lab:df1f45a8c841238bfdc1865b2f6c569f0609a440` |
| Published digest | Tag-to-digest mapping not retained in this record; the later Minikube validation used `sha256:0c14d7a7ddbb0641b7dfaf78fbaff8ae528dae53b1c7d1f91c9884a5a1469bd4` |
| Docker health | `healthy` |
| Runtime user | `10001:10001` |
| Read-only root filesystem | PASS |
| `/healthz` | PASS |
| `/readyz` | PASS |
| Mutable `latest` tag | Absent |

## Public evidence boundary

The GitLab project and Container Registry were private at the time of this
public evidence review. Anonymous project lookup was unavailable, so the
pipeline and registry cannot be offered as durable public links. The table
retains only sanitized identifiers and recorded outcomes; it does not claim
that a public reviewer can independently inspect the private GitLab jobs.

The repository digest in the later
[`Minikube, Traefik, and Argo CD E2E validation`](minikube-argocd-e2e.md)
proves which private-registry image Kubernetes pulled. It does not recreate the
missing public GitLab pipeline URL or independently prove the historical
tag-to-digest mapping.
