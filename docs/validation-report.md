# Validation report

Validation was executed against the cleaned working tree with Python 3.13.5; the GitLab job is configured for Python 3.12.13. A PASS indicates that the command ran successfully; it is not inferred from file inspection.

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
