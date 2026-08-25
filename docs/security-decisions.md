# Security decisions

See the architecture
[decision and trade-off synthesis](architecture.md#decision-and-trade-off-synthesis)
for the delivery responsibility split, evidence boundary, and production gaps.

## Source sanitisation

The imported archive contained private keys, kubeconfig material, local environment files, an Argo CD repository credential manifest, certificates tied to the former environment, public or internal endpoints, and screenshots containing account or infrastructure metadata. These assets were excluded from the publishable repository.

Only two screenshots showing localhost application responses were retained. They contain no account identity, token, public address, registry path, or administrative interface.

## Container

- Python dependency installation uses the complete runtime lock with
  `--require-hashes` and `--only-binary=:all:`;
- the Dockerfile 1.7 frontend is pinned by digest;
- exact Python patch, Alpine minor tag, and reviewed OCI index digest;
- multi-stage build with runtime-only dependencies;
- deterministic UID/GID `10001` shared with Kubernetes;
- no root execution;
- no package manager or compiler added to the runtime stage;
- Python-based health check, avoiding an extra `curl` package;
- `/tmp` is the explicit writable location when the root filesystem is read-only;
- Gunicorn's optional control socket is disabled so it does not attempt to
  write beneath the non-root user's home on a read-only filesystem.

The approved reference is
`python:3.12.14-alpine3.23@sha256:31a768b01976652c222e318fe5bd6e7c252f056cbf489c88fa256f1bf0af58e3`.
This is the multi-platform OCI index digest; the explicit `linux/amd64` target
selects manifest
`sha256:3ac63b9557ecf93c27c20e9a7a8c5ebc907d1838634b3f021f6d08eda8c0ec63`.
Both were resolved from Docker Hub on 2026-08-25 with:

```bash
docker buildx imagetools inspect python:3.12.14-alpine3.23
docker buildx imagetools inspect python:3.12.14-alpine3.23 \
  --format '{{json .Manifest}}'
```

The initially requested Alpine 3.22 pin was tested and its OCI artifact was
blocked by the policy gate because OpenSSL contained fixable HIGH
CVE-2026-45447. Moving only the base component to Alpine 3.23 removed the
blocking finding; no exception or suppression was added. The Dockerfile has no
base-image build argument, so CI cannot silently replace the approved digest
with a tag-only reference.

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

GitHub Actions are pinned by full commit SHA and run on Node 24-compatible
releases. Hadolint and kubeconform are downloaded at fixed versions, verified
against maintained SHA-256 values, and only then installed.

GitLab validation, Buildah, and Trivy images retain readable tags and are also
pinned by manifest digest. Buildah creates one persisted OCI layout. The
security job reads that layout without registry credentials, retains a
CycloneDX SBOM and complete vulnerability JSON, and fails on a fixable
`HIGH`/`CRITICAL` vulnerability or an EOL OS. The publication job depends on
that gate, imports the same layout, and uses Buildah's digest file to capture
the registry-returned digest. Vulnerability evidence is an assessment at a
specific database timestamp; it is not reproducible in the same sense as the
immutable OCI artifact.

The validated Minikube GitOps path promotes the published artifact by an
immutable `sha256` digest in its Kustomize overlay. The promotion helper accepts
only a complete digest reference; it neither handles registry credentials nor
resolves mutable tags. Repository validation proves that this declared digest
is exactly the image rendered into the target Deployment.

The pipeline intentionally has no Kubernetes credentials. Argo CD is the sole
deployment controller. The repository credential manifest is an example
containing placeholders only and must never be applied without creating a
protected local copy.

## Required incident action

Any key, token, kubeconfig credential, registry password, GitLab token, or Argo CD repository credential from the source archive should be rotated or revoked if it was ever active. Removing it from this repository does not invalidate the original credential.
