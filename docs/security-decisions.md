# Security decisions

## Source sanitisation

The imported archive contained private keys, kubeconfig material, local environment files, an Argo CD repository credential manifest, certificates tied to the former environment, public or internal endpoints, and screenshots containing account or infrastructure metadata. These assets were excluded from the publishable repository.

Only two screenshots showing localhost application responses were retained. They contain no account identity, token, public address, registry path, or administrative interface.

## Container

- exact Python patch and Alpine minor tag;
- multi-stage build with runtime-only dependencies;
- deterministic UID/GID `10001` shared with Kubernetes;
- no root execution;
- no package manager or compiler added to the runtime stage;
- Python-based health check, avoiding an extra `curl` package;
- `/tmp` is the explicit writable location when the root filesystem is read-only.

A digest pin can be supplied through the `PYTHON_IMAGE` build argument when the target platform and approved multi-architecture digest are known. The repository does not claim that an unverified digest is current.

## Kubernetes

- Pod Security Admission labels set to `restricted`;
- `runAsNonRoot`, deterministic IDs, and `RuntimeDefault` seccomp;
- all Linux capabilities dropped;
- privilege escalation disabled;
- read-only root filesystem;
- service-account token automount disabled;
- resource requests and limits;
- startup, readiness, and liveness probes;
- no hard-coded cloud storage class;
- no Kubernetes Secret with real data.

## CI/CD and GitOps

Registry credentials are referenced only through protected, masked GitLab variables. Authentication files are placed under `/tmp` and removed in `after_script`. Images use the full commit SHA as the immutable tag.

The pipeline intentionally has no Kubernetes credentials. Argo CD is the sole deployment controller. The repository credential manifest is an example containing placeholders only and must never be applied without creating a protected local copy.

## Required incident action

Any key, token, kubeconfig credential, registry password, GitLab token, or Argo CD repository credential from the source archive should be rotated or revoked if it was ever active. Removing it from this repository does not invalidate the original credential.
