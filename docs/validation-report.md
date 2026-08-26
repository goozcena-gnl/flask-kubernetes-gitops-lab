# Validation report

## Reproducible supply-chain phase — 2026-08-25

The status boundary is explicit: `VERIFIED LOCALLY`, `VERIFIED IN GITHUB
ACTIONS`, and `VERIFIED IN GITLAB` identify where a check ran;
`STATICALLY VALIDATED` is repository inspection or a unit contract;
`HISTORICAL EVIDENCE` predates this phase; and `NOT VERIFIED` did not run.

## Final review and publication — 2026-08-26

The independent final review initially found a reproducibility defect: two
GitLab pipelines for the same commit produced different OCI digests because
installed Python bytecode retained build-time timestamps. Commit
`3030ffbf93bdcbe1c3bb5ec70ca48efe6e61f017` disabled installation-time bytecode
compilation, removed residual bytecode, and added a regression check. Two
subsequent MR pipelines (`2792221926` and `2792232096`) produced the same OCI
digest, `sha256:eaae886e127ccb74a7ef512e3f606b70c0c4f7bc412fda7396a1a1c691431d5c`.

GitHub PR `20` was then squash-merged as
`d477dcfe68837d34cb98c44d95562ea920251b28`. GitHub post-merge workflow
`32961976291` passed, and GitLab `main` was fast-forwarded to the exact same
commit. GitLab default-branch pipeline `2792252277` passed all four jobs:
`validate` (`16117241873`), `build_image` (`16117241874`), `security_scan`
(`16117241875`), and `publish_image` (`16117241876`).

The build and scan used OCI manifest digest
`sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb`.
The publication artifact records the same registry-returned digest for
`registry.gitlab.com/goozcena-gnl/test-lab:d477dcfe68837d34cb98c44d95562ea920251b28`,
so digest equality is verified. No GitOps promotion was performed.

| Status | Check | Evidence |
|---|---|---|
| VERIFIED LOCALLY / VERIFIED IN GITLAB | Lock compiler and freshness | `uv 0.12.3` reproduced both universal, wheel-only, hash-bearing locks byte-for-byte. Removing a direct input made the check fail with both locks reported stale. |
| VERIFIED LOCALLY / VERIFIED IN GITLAB | Lock contents | 2 runtime direct inputs resolve to 10 pinned and hashed universal lock entries; the complete development environment contains 19. |
| VERIFIED LOCALLY / VERIFIED IN GITHUB ACTIONS / VERIFIED IN GITLAB | Hash installation | Clean development and container installs used both `--require-hashes` and `--only-binary=:all:`. A deliberately corrupted Blinker hash was rejected by pip. |
| VERIFIED LOCALLY / VERIFIED IN GITLAB | Base identity | Docker Hub OCI index `sha256:31a768b01976652c222e318fe5bd6e7c252f056cbf489c88fa256f1bf0af58e3` selects linux/amd64 manifest `sha256:3ac63b9557ecf93c27c20e9a7a8c5ebc907d1838634b3f021f6d08eda8c0ec63`. |
| VERIFIED IN GITLAB | Buildah transport | Pipeline `2789825156` built one `linux/amd64` OCI layout and recorded manifest digest `sha256:b01a2d69ed40b142fc564cd3707bc40c11212010d716197111159e33aab58628`. |
| VERIFIED IN GITLAB | CycloneDX SBOM | Trivy 0.74.0 generated non-empty CycloneDX JSON from that OCI layout; `trivy sbom` recognized it as CycloneDX JSON, and component checks found Flask 3.1.3 and Gunicorn 26.0.0. |
| VERIFIED IN GITLAB | Vulnerability evidence and gate | The retained full JSON report used a DB updated at `2026-08-25T13:00:57Z` and downloaded at `2026-08-25T16:55:04Z`. The EOL-aware, fixable HIGH/CRITICAL gate reported 0 findings for Alpine 3.23.5 and every Python package target, then printed `SECURITY POLICY PASSED`. |
| VERIFIED LOCALLY / HISTORICAL EVIDENCE | Negative controls | Unit checks reject missing hashes, tag-only bases, a disabled security gate, duplicate branch/MR pipelines, ambiguous Buildah timestamp controls, and a tampered OCI manifest. Earlier empirical evidence records Alpine 3.22 being blocked for fixable HIGH CVE-2026-45447 before the base moved to Alpine 3.23. |
| STATICALLY VALIDATED | Publication dependency | Static and unit checks prove `publish_image` needs both the exact build artifact and successful `security_scan`, contains no rebuild, captures the registry-returned digest, and fails if it differs from the scanned manifest digest. |
| VERIFIED IN GITLAB | Merge-request pipeline | Private pipeline `2789825156` passed `validate` (`31` tests), `build_image`, and `security_scan` for commit `35e23c97e38f4a0c3a32734e7b797c2bc45ce264`. One MR pipeline, rather than duplicate branch and MR pipelines, was created for the push. |
| VERIFIED IN GITHUB ACTIONS | GitHub execution | Workflow run `32876015604` passed tests, lint, YAML, links, secret scan, Docker build, read-only endpoint smoke tests, Kustomize image contract, Hadolint, and kubeconform for commit `35e23c97e38f4a0c3a32734e7b797c2bc45ce264`. |
| VERIFIED IN GITLAB | Registry publication and digest equality | Default-branch pipeline `2792252277` imported the retained OCI artifact without rebuilding it and published the immutable commit tag `d477dcfe68837d34cb98c44d95562ea920251b28`. The registry-returned digest exactly matched the built and scanned digest: `sha256:8e5256469386c9aa526f4f6f201ea822b900e098ba5c84d023dd6e6756b006fb`. |

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
