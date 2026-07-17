#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

# shellcheck source=/dev/null
source "$repo_root/environments/minikube/config.sh"

TRAEFIK_CHART_VERSION="${TRAEFIK_CHART_VERSION:-40.2.0}"
ARGOCD_VERSION="${ARGOCD_VERSION:-v3.4.2}"

for command_name in docker minikube kubectl helm; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'ERROR: %s is not installed\n' "$command_name" >&2
    exit 1
  fi
done

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is unavailable" >&2
  exit 1
fi

cd "$repo_root"

minikube start \
  --profile "$MINIKUBE_PROFILE" \
  --driver "$MINIKUBE_DRIVER" \
  --container-runtime "$MINIKUBE_CONTAINER_RUNTIME" \
  --kubernetes-version "$MINIKUBE_KUBERNETES_VERSION" \
  --cpus "$MINIKUBE_CPUS" \
  --memory "$MINIKUBE_MEMORY" \
  --disk-size "$MINIKUBE_DISK_SIZE"

kubectl config use-context "$MINIKUBE_PROFILE"

kubectl wait \
  --for=condition=Ready \
  nodes \
  --all \
  --timeout=300s

helm repo add \
  traefik \
  https://traefik.github.io/charts \
  --force-update

helm repo update traefik

helm upgrade \
  --install traefik \
  traefik/traefik \
  --version "$TRAEFIK_CHART_VERSION" \
  --namespace traefik \
  --create-namespace \
  --values deploy/helm-values/traefik-minikube.yaml \
  --wait \
  --timeout 5m

kubectl rollout status \
  deployment/traefik \
  --namespace traefik \
  --timeout=300s

kubectl create namespace argocd \
  --dry-run=client \
  --output=yaml |
  kubectl apply -f -

kubectl apply \
  --namespace argocd \
  --server-side \
  --force-conflicts \
  -f \
  "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"

kubectl wait \
  --namespace argocd \
  --for=condition=Available \
  deployments \
  --all \
  --timeout=300s

kubectl rollout status \
  statefulset/argocd-application-controller \
  --namespace argocd \
  --timeout=300s

echo "PASS: Minikube, Traefik, and Argo CD are ready"
