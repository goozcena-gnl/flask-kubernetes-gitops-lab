# GitLab operational validation

## Objective

Validate the real delivery path from GitLab CI to an immutable image in the
GitLab Container Registry.

## Source of truth

GitHub `main` remains the canonical Git history.

The GitLab repository is used as a CI and registry replica. It has no automatic
repository mirror configured, so the required GitHub commit must be
fast-forwarded explicitly. Changes must not be merged independently in GitLab
because this would cause the histories to diverge.

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

## Reproducible supply-chain phase — 2026-08-25

The stale branch was caused by the absence of an automatic GitLab repository
mirror. Commit `35e23c97e38f4a0c3a32734e7b797c2bc45ce264` was fast-forwarded from
GitHub to the existing GitLab MR branch without changing `main` or rewriting
history.

| Evidence | Status |
|---|---|
| GitHub Actions | VERIFIED — run `32876015604` passed for the exact commit |
| GitLab MR pipeline | VERIFIED — private pipeline `2789825156` passed in 1 minute 45 seconds |
| Validation job | VERIFIED — job `16099097727`; locks current, 10 runtime/19 development packages, 31 tests, lint/YAML/links/secret scan passed |
| Buildah job | VERIFIED — job `16099097728`; one OCI layout, manifest `sha256:b01a2d69ed40b142fc564cd3707bc40c11212010d716197111159e33aab58628` |
| Security job | VERIFIED — job `16099097729`; Trivy 0.74.0, CycloneDX parsed, Flask/Gunicorn present, full JSON report non-empty, policy passed |
| Vulnerability DB | VERIFIED — updated `2026-08-25T13:00:57Z`, downloaded `2026-08-25T16:55:04Z`, next update `2026-08-26T13:00:57Z` |
| HIGH/CRITICAL and EOL gate | VERIFIED — 0 fixable HIGH/CRITICAL findings across Alpine 3.23.5 and Python package targets; EOL-aware command returned success |
| Duplicate-pipeline suppression | VERIFIED — one MR pipeline was created for each synchronized push; no companion branch pipeline was created |
| Default-branch publication | NOT VERIFIED — correctly omitted from the MR pipeline by policy |
| Registry digest equality | STATICALLY VALIDATED — publication compares the registry-returned digest with the scanned OCI manifest; runtime evidence requires the default-branch job |

The exact remaining action is to merge the reviewed GitHub PR, fast-forward the
resulting GitHub commit to GitLab `main`, and inspect the resulting default-
branch `publish_image` job. Record the immutable SHA tag, the registry-returned
digest, and the successful equality check before promoting that digest with
`scripts/set-image.py`. Do not merge the GitLab MR independently.

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
