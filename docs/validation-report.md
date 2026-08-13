# Validation report

## Reproducible supply-chain phase — 2026-08-13

The status boundary is explicit: `IMPLEMENTED` is static repository state,
`VALIDATED` is an executed check, `HISTORICAL EVIDENCE` predates this phase,
and `NOT VALIDATED` has not been observed on the new branch.

| Status | Check | Evidence |
|---|---|---|
| VALIDATED | Lock compiler and freshness | `uv 0.12.3` regenerated both universal, wheel-only, hash-bearing locks byte-for-byte. |
| VALIDATED | Lock contents | 2 runtime direct inputs resolve to 10 pinned and hashed universal lock entries; the complete development environment contains 19. |
| VALIDATED | Hash installation | Docker installed the runtime lock on Python 3.12/Alpine with both `--require-hashes` and `--only-binary=:all:`; the development lock installed with the same controls. |
| VALIDATED | Base identity | Docker Hub OCI index `sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d` selects linux/amd64 manifest `sha256:efc8538b7449b6d893de5d852c87a0dc2cffd0ec27b07dd98ba3e7edaadc26af`. |
| VALIDATED | Buildah transport | Buildah 1.43.1 built once for `linux/amd64` and exported an OCI layout with manifest digest `sha256:4f2c75987dfc10193d2c5e9f95817a4d3901efc603f420f38a365bd898934d82`. |
| VALIDATED | CycloneDX SBOM | Trivy 0.73.0 parsed the OCI layout directly and generated CycloneDX 1.7 JSON with 50 components, including every expected runtime Python package. |
| VALIDATED | Vulnerability evidence and gate | Database updated at `2026-08-13T13:03:34Z`; full report contained 2 LOW, 8 MEDIUM, 0 HIGH, and 0 CRITICAL findings. Fixable HIGH/CRITICAL count was 0 and the EOL-aware policy passed without exceptions. |
| VALIDATED | Negative gate | The first Alpine 3.22 artifact was blocked for fixable HIGH CVE-2026-45447; the base was remediated to the reviewed Alpine 3.23 digest and the same gate then passed. |
| IMPLEMENTED | Publication dependency | Static and unit checks prove `publish_image` needs both the build artifact and successful `security_scan`, and contains no rebuild command. |
| VALIDATED | GitLab CI lint | The signed-in project CI Lint accepted the submitted branch configuration and simulated the default-branch `validate`, `build_image`, `security_scan`, and `publish_image` job graph. |
| VALIDATED | GitHub Actions execution | PR run `31727912238` passed all repository checks in 31 seconds with no annotations, including the digest-pinned Docker build and read-only smoke test. |
| NOT VALIDATED | GitLab branch pipeline | Requires a pushed branch to reach the private mirror. |
| NOT VALIDATED | New registry publication/digest | Publication remains default-branch-only and this feature branch will not be merged automatically. |

## Historical repository and Minikube evidence

The original validation was executed against the cleaned working tree with
Python 3.13.5; the GitLab job was configured for Python 3.12.13. A `PASS` in
the table below indicates that the command ran successfully; it is not inferred
from file inspection.

This table is historical evidence from the original validation run. It is not
rewritten to imply that later promotion or supply-chain controls existed then.

| Status | Check | Command | Evidence |
|---|---|---|---|
| PASS | Python syntax | `python -m compileall -q app` | All application and test modules compiled. |
| PASS | Application tests | `pytest -q` | 3 tests passed. |
| PASS | Ruff lint | `ruff check .` | All checks passed. |
| PASS | Ruff formatting | `ruff format --check .` | 8 files already formatted. |
| PASS | kubectl kustomize | `kubectl kustomize deploy/kubernetes/base` | Base manifests rendered locally. |
| PASS | YAML lint | `yamllint -c .yamllint.yaml .` | No lint errors. |
| PASS | YAML parsing | `python scripts/check-yaml.py` | GitLab CI, Argo CD, Helm values, and Kubernetes YAML parsed. |
| PASS | Kubernetes schema | Python `kubernetes-validate` against Kubernetes 1.35 schemas | Deployment, Ingress, Namespace, Service, and optional PVC validated strictly. |
| PASS | Dockerfile syntax | Python `dockerfile-parse` | 19 instructions and 2 stages parsed. |
| PASS | Markdown local links | `python scripts/check-markdown-links.py` | All local links and images resolve. |
| PASS | Fallback secret scan | `python scripts/scan-secrets.py` | No forbidden credential material found in publishable files. |
| PASS | Duplicate-content check | SHA-256 comparison of non-empty publishable files | No duplicate content groups. |
| PASS | Temporary-file check | `find` for editor, backup, and temporary patterns | No unwanted files found. |
| PASS | Image update helper | `python scripts/set-image.py registry.example.com/devops/flask-k8s-lab:test-sha` on a reversible copy | Exactly one Deployment image field was updated; source restored. |
| PASS | Exact Git index secret scan | Custom scanner over `git show :<path>` for every indexed file | 38 files in the final Git index snapshot checked; no credential material found. |
| PASS | Pre-merge branch history secret scan | Fallback scanner over the feature-branch commit snapshots before squash merge | All scoped snapshots were checked; no forbidden credential material was found. |
| PASS | Merged repository state | `git status -sb && git log -1 --oneline` | `main` is synchronized with `origin/main`; squash commit `55f3a54` contains the sanitized import. |
| PASS | Docker image build | `docker build -t flask-k8s-lab:pr-1 .` | The image was built from the pull-request working tree. |
| NOT RUN | Gitleaks or TruffleHog | `gitleaks detect` / `trufflehog filesystem` | Neither scanner is installed; the fallback scanner ran instead. |
| PASS | kubectl client dry-run | `kubectl apply --dry-run=client -k deploy/kubernetes/base` | The manifests were accepted against the reachable Minikube Kubernetes API. |
| PASS | Hadolint | `hadolint Dockerfile` | The hardened Dockerfile passed linting. |
| PASS | Container smoke test | Read-only `docker run` with `/tmp` mounted as `tmpfs`, followed by endpoint checks | `/`, `/healthz`, and `/readyz` responded successfully; Docker reported the container as `healthy`. |
| PASS | kubeconform | Strict validation against Kubernetes `1.35.1` | Base, Minikube overlay, and rendered Traefik resources validated. |
| PASS | Helm rendering | `helm template traefik ... --version 40.2.0` | Six Traefik resources rendered and validated. |
| PASS | GitLab CI Lint API | Project-scoped CI Lint request | Configuration valid with `validate`, `build_image`, and `publish_image`. |
| PASS | Minikube runtime | `minikube status --profile flask-gitops` | Control plane, kubelet, and API server running on Kubernetes `v1.35.1`. |
| PASS | Argo CD reconciliation | Application status `flask-k8s-lab-minikube` | Application reached `Synced / Healthy` against `deploy/kubernetes/overlays/minikube`. |
| PASS | Argo CD self-heal | Manual Deployment replica drift | Argo CD restored replicas from one to two within one reconciliation cycle. |
| PASS | Argo CD prune | Git-managed ConfigMap add/remove sequence | Argo CD deleted the resource after its manifest was removed from Git. |
