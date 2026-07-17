# Architecture

## Delivery flow

```mermaid
flowchart LR
    DEV[Developer change] --> GITHUB[GitHub protected main]
    GITHUB --> GITLAB[GitLab CI mirror]
    GITLAB --> BUILD[Buildah image build]
    BUILD --> REG[GitLab Container Registry\nimmutable SHA tag]
    REG --> PROMOTE[Reviewed image promotion]
    PROMOTE --> GITHUB
    GITHUB --> ARGO[Argo CD reconciliation]
    ARGO --> MINI[Minikube Kubernetes]
    MINI --> TRAEFIK[Traefik OSS]
    TRAEFIK --> APP[Flask application]
```

GitLab CI does not receive a kubeconfig and does not call `kubectl`. GitHub `main` is the canonical Git history; the GitLab repository serves as a CI and registry mirror. After an image is published, `scripts/set-image.py` updates the image reference in the Kustomize overlay. The resulting change is reviewed and merged on GitHub before Argo CD reconciles it against `deploy/kubernetes/overlays/minikube`.

## Runtime design

The application is stateless. Two replicas run as UID/GID `10001`, without a service-account token, Linux capabilities, privilege escalation, or a writable root filesystem. An `emptyDir` volume provides the only required writable path at `/tmp`.

The base deployment does not require persistent storage. `deploy/kubernetes/optional-storage` is retained only as a learning exercise and deliberately omits a storage class so the target cluster can select its default provisioner.

## TLS strategy

No generated certificate or private key is stored in Git. The portable base Ingress is HTTP-only. A real environment should add TLS with cert-manager, an external secret manager, or a locally created Kubernetes TLS Secret. Repository certificate trust for Argo CD must likewise be configured out of band.
