# Agent Instructions

## Repository purpose

This repository is a hardened Flask + Kubernetes GitOps lab. Preserve the core delivery boundary: CI validates, builds, scans, and publishes an immutable artifact; Argo CD is the cluster reconciler.

## Sources of truth

- `docs/architecture.md` defines architecture and trade-offs.
- `docs/security-decisions.md` defines security choices.
- `docs/minikube-argocd-e2e.md` records validated runtime evidence.
- `deploy/kubernetes/` and `deploy/argocd/` define desired state.
- `.gitlab-ci.yml` defines the image build/security/publish path.

## Mandatory validation

For code, image, dependency, Kubernetes, or CI changes run the relevant local equivalents of CI:

```bash
python scripts/lock-requirements.py --check
python scripts/check-supply-chain.py
python -m compileall -q app scripts
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m yamllint -c .yamllint.yaml .
python scripts/check-yaml.py
python scripts/check-markdown-links.py
python scripts/scan-secrets.py
docker build --platform linux/amd64 -t flask-k8s-lab:ci .
kubectl kustomize deploy/kubernetes/base >/tmp/base-rendered.yaml
kubectl kustomize deploy/kubernetes/overlays/minikube >/tmp/minikube-rendered.yaml
python scripts/check-rendered-image.py
git diff --check
```

Run Hadolint/Kubeconform as available when touching Docker/Kubernetes content.

## Trust boundaries

- Do not add a deploy stage or kubeconfig to CI.
- Do not let an agent resolve mutable tags and silently promote them.
- Preserve digest-based artifact promotion.
- Do not commit registry credentials or repository secrets.
- Do not treat CI success as proof that Argo CD reconciled the live lab.
- Do not claim Minikube/runtime success without actual runtime execution/evidence.

## Engineering rules

- Keep the reusable Kubernetes base environment-neutral.
- Preserve non-root/read-only container hardening and supply-chain checks.
- Do not weaken Trivy, SBOM, hash-locked dependencies, or policy gates to get a green build.
- Keep documentation claims aligned with the evidence actually executed.

## Pull request discipline

Use focused changes, list validation performed, distinguish static from runtime evidence, and do not merge or release on behalf of the user.
