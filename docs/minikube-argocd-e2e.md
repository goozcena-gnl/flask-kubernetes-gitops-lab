# Minikube, Traefik, and Argo CD E2E validation

## Objective

Validate the complete GitOps runtime path:

```text
GitHub main
  → Argo CD
  → Minikube
  → Traefik
  → Flask workload
```

The application image is pulled from the private GitLab Container Registry by
repository digest.

## Validated environment

| Component | Validated value |
|---|---|
| Minikube | `v1.38.1` |
| Kubernetes | `v1.35.1` |
| Container runtime | `containerd 2.2.1` |
| Traefik Helm chart | `40.2.0` |
| Traefik Proxy | `v3.7.1` |
| Argo CD | `v3.4.2` |
| Git revision | `ca932066ed272b257d6811a28340bc4de0d0d9cd` |
| Application namespace | `flask-k8s-lab` |
| Ingress host | `flask-k8s-lab.localhost` |

## Immutable application image

```text
registry.gitlab.com/goozcena-gnl/test-lab@sha256:0c14d7a7ddbb0641b7dfaf78fbaff8ae528dae53b1c7d1f91c9884a5a1469bd4
```

The Deployment references the image by digest rather than a mutable tag.

The private-registry credential is stored only in the local Kubernetes Secret:

```text
flask-k8s-lab/gitlab-registry
```

No registry credential is stored in Git.

## Runtime results

| Validation | Result |
|---|---|
| Minikube node Ready | PASS |
| Traefik Deployment Ready | PASS |
| Argo CD components Ready | PASS |
| Private registry image pull | PASS |
| Application Deployment | `2/2` |
| Argo CD sync state | `Synced` |
| Argo CD health state | `Healthy` |
| Ingress class | `traefik` |
| Ingress hostname publication | PASS |
| Browser routing | PASS |
| `/` | PASS |
| `/healthz` | PASS |
| `/readyz` | PASS |

## Self-heal validation

The Deployment replica count was manually changed from two replicas to one:

```bash
kubectl \
  --namespace flask-k8s-lab \
  patch deployment flask-k8s-lab \
  --type merge \
  --patch '{"spec":{"replicas":1}}'
```

Argo CD automatically restored the Git-declared value:

```text
Current replicas: 1
Current replicas: 2
```

Result:

```text
PASS: Argo CD self-heal restored replicas to 2
```

## Prune validation

A temporary ConfigMap named `argocd-prune-probe` was added through a protected
GitHub pull request.

Argo CD created the resource from Git:

```text
argocd-prune-probe => validate-argocd-prune
```

A second protected pull request removed the manifest and its Kustomize entry.

Argo CD detected the new Git revision, transitioned through `OutOfSync`, deleted
the ConfigMap, and returned to:

```text
Synced / Healthy
```

Result:

```text
PASS: Argo CD pruned the removed ConfigMap
```

## Final application verification

```text
Git revision:
ca932066ed272b257d6811a28340bc4de0d0d9cd

Argo CD:
Synced / Healthy

Health:
{"status":"ok"}

Readiness:
{"status":"ready"}
```

## Security observations

- The workload runs as UID/GID `10001`.
- The container root filesystem is read-only.
- Linux capabilities are dropped.
- Privilege escalation is disabled.
- The runtime-default seccomp profile is enabled.
- The service-account token is not mounted.
- The application image is pinned by digest.
- Registry credentials remain outside Git.
- Argo CD is the sole Kubernetes deployment reconciler.

## Verified digest promotion — 2026-08-28

GitHub pull request `#22` promoted the already-built and scanned artifact from
source commit `d477dcfe68837d34cb98c44d95562ea920251b28`. GitLab publication
pipeline `2792252277` had established equality between the built/scanned digest
and the registry-returned digest before this GitOps change.

The promotion was merged by guarded squash at:

```text
3ccc8a46e02491408ac2952ee8310a6a2f11705f
```

Argo CD automatically observed that exact GitHub `main` revision. No manual
sync, direct Kustomize apply, Deployment patch, or imperative image change was
used. The observed health transition was `Progressing` to `Healthy`; an
`OutOfSync` state was not observed during polling.

| Validation | Result |
|---|---|
| Previous digest | `sha256:0c14d7a7ddbb0641b7dfaf78fbaff8ae528dae53b1c7d1f91c9884a5a1469bd4` |
| Promoted digest | `sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb` |
| Argo CD revision | `3ccc8a46e02491408ac2952ee8310a6a2f11705f` |
| Argo CD state | `Synced / Healthy`, operation `Succeeded` |
| Deployment rollout | `2` desired, updated, ready, and available |
| Private-registry pull | PASS; Kubernetes recorded a successful pull of the promoted digest |
| Pod restart counts | `0`, `0` after stabilization |
| Current promoted-Pod warning events | `0` |
| Service `/`, `/healthz`, `/readyz` | HTTP `200`, HTTP `200`, HTTP `200` |
| Traefik `/`, `/healthz`, `/readyz` | HTTP `200`, HTTP `200`, HTTP `200` using host `flask-k8s-lab.localhost` |

The live Deployment and both application Pod declarations used exactly:

```text
registry.gitlab.com/goozcena-gnl/test-lab@sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb
```

The container runtime reported that same immutable reference for both Pod
`imageID` values:

```text
flask-k8s-lab-77d9d94d56-fd2jh:
registry.gitlab.com/goozcena-gnl/test-lab@sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb

flask-k8s-lab-77d9d94d56-gwpkn:
registry.gitlab.com/goozcena-gnl/test-lab@sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb
```

The promoted workload retained `runAsNonRoot: true`, UID/GID `10001`, a
read-only root filesystem, disabled privilege escalation, all Linux
capabilities dropped, `RuntimeDefault` seccomp, and disabled service-account
token automounting. After a stabilization wait, Argo CD remained
`Synced / Healthy`, the Deployment remained `2/2`, both Pods remained at zero
restarts, and all tested endpoints remained healthy.
