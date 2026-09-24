---
applyTo: "deploy/**,Dockerfile,.gitlab-ci.yml,scripts/set-image.py,scripts/check-rendered-image.py"
---

# Kubernetes and Supply-Chain Instructions

- Keep the reusable Kubernetes base environment-neutral.
- Preserve digest-based promotion and never silently resolve or promote mutable image tags.
- Do not introduce kubeconfigs or a deploy stage into the build pipeline.
- Maintain non-root, read-only, probe, resource, and restricted Pod Security controls.
- Validate Kustomize rendering and the exact image contract after deployment-manifest changes.
- CI success is not evidence that Argo CD reconciled the live Minikube lab.
