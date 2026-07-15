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
| PASS | Full Git history secret scan | Custom scanner over every blob returned by `git rev-list` and `git ls-tree` | 5 commits and 131 commit/file snapshots checked; no forbidden credential material found. |
| PASS | Git history | `git log --oneline --reverse` | Five small commits created on `chore/import-clean-devops-lab`. |
| PASS | Final worktree status | `git status -sb` | Branch clean; no unstaged or untracked publishable files. |
| NOT RUN | Gitleaks or TruffleHog | `gitleaks detect` / `trufflehog filesystem` | Neither scanner is installed; the fallback scanner ran instead. |
| BLOCKED | kubectl client dry-run | `kubectl apply --dry-run=client -k deploy/kubernetes/base` | No reachable Kubernetes API server. |
| NOT RUN | Hadolint | `hadolint Dockerfile` | Binary not installed. |
| NOT RUN | Docker or Buildah build | `docker build ...` / `buildah bud ...` | No container runtime or Buildah binary is available. |
| NOT RUN | Container smoke test | `docker run ...` | Blocked by the missing container runtime. |
| NOT RUN | kubeconform | `kubeconform ...` | Binary not installed. |
| NOT RUN | Helm rendering | `helm template ...` | Helm and chart archives are not installed. |
| NOT RUN | GitLab CI Lint API | GitLab CI lint service | No target GitLab service or lint API credential was provided. |
