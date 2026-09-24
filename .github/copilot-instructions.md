# GitHub Copilot Instructions

Read and follow `AGENTS.md` as the repository-wide engineering and trust contract.

For Copilot-specific work:
- preserve the CI -> immutable artifact -> reviewed Git -> Argo CD delivery boundary;
- keep changes scoped and inspect the supply-chain and deployment validation scripts before editing;
- do not weaken hash locks, Trivy gates, SBOM generation, image provenance, or container hardening;
- do not add deployment credentials or direct cluster mutation to CI;
- report static validation separately from Minikube/Argo CD runtime evidence;
- leave merge, release, registry promotion, and cluster reconciliation decisions to a human.
