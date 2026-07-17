# Flask Kubernetes GitOps Lab

A compact portfolio lab demonstrating a hardened Flask container, GitLab CI image delivery with Buildah, Kubernetes workload security, ingress-nginx, and Argo CD reconciliation.

## Architecture

GitLab CI validates the source, builds an OCI image, and publishes an immutable tag based on the full commit SHA. Kubernetes desired state remains in Git. Argo CD is the only deployment controller; the pipeline does not hold a kubeconfig or call `kubectl`.

See [the architecture document](docs/architecture.md) for the delivery diagram and runtime design.

## Demonstrated skills

- Python endpoint testing and linting;
- deterministic multi-stage container builds and non-root runtime design;
- Buildah-based GitLab CI with OCI artifacts and protected registry variables;
- Kubernetes Deployment, Service, Ingress, probes, resources, Kustomize, and restricted Pod Security settings;
- Argo CD automated sync, prune, and self-heal;
- Helm values for GitLab, Argo CD, and ingress-nginx;
- credential sanitisation, safe examples, and reproducible validation.

## Repository structure

```text
.
├── app/                         Flask source, dependencies, and tests
├── deploy/
│   ├── argocd/                  Application and safe repository Secret example
│   ├── helm-values/             One values file per platform component
│   └── kubernetes/              Base manifests and optional storage overlay
├── docs/                        Architecture, security decisions, and canonical report
├── scripts/                     Validation, secret scan, and image update helpers
├── .gitlab-ci.yml               Validate, build, and publish pipeline
└── Dockerfile                   Hardened multi-stage image
```

## Prerequisites

For local application checks: Python 3.12 and `pip`.

For the full lab: a container engine, `kubectl`, Kustomize support, Helm, a Kubernetes cluster with ingress-nginx, an OCI registry, GitLab CI, and Argo CD.

## Local application test

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r app/requirements.txt -r app/requirements-dev.txt
pytest -q
python -m flask --app app.app run --host 127.0.0.1 --port 8080
```

Verify `http://127.0.0.1:8080/`, `/healthz`, and `/readyz`.

## Container build and run

```bash
docker build -t flask-k8s-lab:local .
docker run --rm -p 8080:8080 --read-only --tmpfs /tmp flask-k8s-lab:local
```

The default build uses `python:3.12.13-alpine3.22`. An approved digest can be supplied without modifying the Dockerfile:

```bash
docker build --build-arg PYTHON_IMAGE='python:3.12.13-alpine3.22@sha256:<APPROVED_DIGEST>' .
```

## Kubernetes deployment

Set an image that the cluster can pull, then apply the base:

```bash
python scripts/set-image.py registry.example.com/team/flask-k8s-lab:<commit-sha>
kubectl apply -k deploy/kubernetes/base
kubectl -n flask-k8s-lab rollout status deployment/flask-k8s-lab
kubectl -n flask-k8s-lab port-forward service/flask-k8s-lab 8080:80
```

The Ingress host is the documentation-only domain `flask-k8s-lab.example.test`. Replace it for the target environment. TLS is intentionally not embedded; use cert-manager or create the TLS Secret outside Git.

The application is stateless. The optional PVC exercise is applied only when explicitly selected:

```bash
kubectl apply -k deploy/kubernetes/optional-storage
```

## GitLab CI/CD workflow

### GitLab Container Registry authentication

When the GitLab Container Registry is enabled, the publish job uses GitLab's
job-scoped predefined variables:

- `CI_REGISTRY`
- `CI_REGISTRY_IMAGE`
- `CI_REGISTRY_USER`
- `CI_REGISTRY_PASSWORD`

No permanent registry password is required for the pipeline.

For an external OCI registry, adapt the publish job and store credentials as
masked and protected CI/CD variables.

The pipeline stages are:

1. `validate`: syntax, tests, Ruff, YAML, Markdown links, and fallback secret scan;
2. `build`: Buildah creates an OCI archive;
3. `publish`: the archive is imported and pushed with `$CI_COMMIT_SHA` as the tag.

There is no deploy stage and no `KUBECONFIG_B64`. After publication, update the Git manifest through a reviewed change:

```bash
python scripts/set-image.py "$REGISTRY_HOST/$REGISTRY_NAMESPACE/$CI_PROJECT_PATH_SLUG:$CI_COMMIT_SHA"
```

## Argo CD workflow

1. Install Argo CD with an explicitly pinned chart version and adapt `deploy/helm-values/argocd.yaml`.
2. For a private repository, copy `deploy/argocd/repository-secret.example.yaml` outside the repository, replace every placeholder, apply it locally, and delete the working copy.
3. Replace `<GIT_REPOSITORY_URL>` in `deploy/argocd/application.yaml` locally or through an environment overlay.
4. Apply the Application:

```bash
kubectl apply -f deploy/argocd/application.yaml
```

Argo CD watches `deploy/kubernetes/base`, creates the namespace, prunes removed resources, and self-heals drift.

## GitLab, Argo CD, and ingress-nginx values

The files under `deploy/helm-values/` replace conflicting environment-specific copies from the source archive. They deliberately contain generic domains and no storage class or IP address. Choose and record compatible chart versions before installation, for example:

```bash
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --version <PINNED_CHART_VERSION> \
  -f deploy/helm-values/ingress-nginx.yaml
```

## Security model

The workload runs as UID/GID `10001`, drops all capabilities, prevents privilege escalation, uses the runtime-default seccomp profile, disables service-account token mounting, and mounts `/tmp` over a read-only root filesystem. No key, kubeconfig, real Secret, generated certificate, public IP, or private endpoint belongs in this repository.

See [security decisions](docs/security-decisions.md). Credentials from the original archive must be rotated or revoked if they were ever active.

## Validation

After installing development dependencies:

```bash
./scripts/validate.sh
```

Optional checks run when `hadolint`, `kubeconform`, and `kubectl` are available. Docker build, container smoke testing, Helm rendering, and GitLab CI lint require their respective external runtimes or services.

## Documentation

- [Anonymised project brief](docs/project-brief.md)
- [Architecture](docs/architecture.md)
- [Security decisions](docs/security-decisions.md)
- [Canonical lab report](docs/lab-report.md)
- [Validation report](docs/validation-report.md)

## Limitations

This is a demonstration lab, not a production GitLab or Kubernetes platform. DNS, TLS, registry authentication, storage provisioning, LoadBalancer support, chart compatibility, and resource sizing remain environment-specific. No software license has been selected because ownership and licensing intent were not confirmed.
