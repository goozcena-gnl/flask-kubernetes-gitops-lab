#!/usr/bin/env bash
set -euo pipefail

profile="${MINIKUBE_PROFILE:-flask-gitops}"
app_namespace="${APP_NAMESPACE:-flask-k8s-lab}"
argocd_namespace="${ARGOCD_NAMESPACE:-argocd}"
application="${ARGOCD_APPLICATION:-flask-k8s-lab-minikube}"
ingress_host="${INGRESS_HOST:-flask-k8s-lab.localhost}"
local_port="${VERIFY_LOCAL_PORT:-18081}"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

cd "$repo_root"

for command_name in minikube kubectl curl git; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf 'ERROR: %s is not installed\n' "$command_name" >&2
    exit 1
  }
done

test "$(git branch --show-current)" = "main" || {
  echo "ERROR: verification must run from main" >&2
  exit 1
}

minikube status --profile "$profile" >/dev/null

test "$(kubectl config current-context)" = "$profile" || {
  echo "ERROR: the active kubectl context is not ${profile}" >&2
  exit 1
}

kubectl wait \
  --for=condition=Ready \
  node \
  --all \
  --timeout=120s

kubectl \
  --namespace traefik \
  rollout status deployment/traefik \
  --timeout=120s

kubectl \
  --namespace "$app_namespace" \
  rollout status deployment/flask-k8s-lab \
  --timeout=120s

kubectl \
  --namespace "$argocd_namespace" \
  wait "application/${application}" \
  --for=jsonpath='{.status.sync.status}'=Synced \
  --timeout=120s

kubectl \
  --namespace "$argocd_namespace" \
  wait "application/${application}" \
  --for=jsonpath='{.status.health.status}'=Healthy \
  --timeout=120s

expected_revision=$(git rev-parse origin/main)

actual_revision=$(
  kubectl \
    --namespace "$argocd_namespace" \
    get application "$application" \
    -o jsonpath='{.status.sync.revision}'
)

test "$actual_revision" = "$expected_revision" || {
  printf 'ERROR: Argo CD revision %s does not match origin/main %s\n' \
    "$actual_revision" "$expected_revision" >&2
  exit 1
}

expected_image=$(
  kubectl kustomize deploy/kubernetes/overlays/minikube |
    awk '$1 == "image:" {print $2; exit}'
)

actual_image=$(
  kubectl \
    --namespace "$app_namespace" \
    get deployment flask-k8s-lab \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
)

test "$actual_image" = "$expected_image" || {
  printf 'ERROR: actual image does not match rendered Git image\n' >&2
  exit 1
}

test "$(
  kubectl \
    --namespace "$app_namespace" \
    get secret gitlab-registry \
    -o jsonpath='{.type}'
)" = "kubernetes.io/dockerconfigjson"

test "$(
  kubectl \
    --namespace "$app_namespace" \
    get ingress flask-k8s-lab \
    -o jsonpath='{.spec.ingressClassName}'
)" = "traefik"

test "$(
  kubectl \
    --namespace "$app_namespace" \
    get ingress flask-k8s-lab \
    -o jsonpath='{.spec.rules[0].host}'
)" = "$ingress_host"

port_forward_log=$(mktemp)

kubectl \
  --namespace traefik \
  port-forward service/traefik "${local_port}:80" \
  >"$port_forward_log" 2>&1 &

port_forward_pid=$!

cleanup() {
  kill "$port_forward_pid" >/dev/null 2>&1 || true
  wait "$port_forward_pid" >/dev/null 2>&1 || true
  rm -f "$port_forward_log"
}

trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl \
    --fail \
    --silent \
    --header "Host: ${ingress_host}" \
    "http://127.0.0.1:${local_port}/healthz" \
    >/dev/null 2>&1; then
    break
  fi

  kill -0 "$port_forward_pid" >/dev/null 2>&1 || {
    cat "$port_forward_log" >&2
    exit 1
  }

  sleep 1
done

health=$(
  curl \
    --fail \
    --silent \
    --header "Host: ${ingress_host}" \
    "http://127.0.0.1:${local_port}/healthz"
)

readiness=$(
  curl \
    --fail \
    --silent \
    --header "Host: ${ingress_host}" \
    "http://127.0.0.1:${local_port}/readyz"
)

case "$health" in
  *'"status":"ok"'*) ;;
  *)
    echo "ERROR: unexpected health response" >&2
    exit 1
    ;;
esac

case "$readiness" in
  *'"status":"ready"'*) ;;
  *)
    echo "ERROR: unexpected readiness response" >&2
    exit 1
    ;;
esac

printf 'Revision: %s\n' "$actual_revision"
printf 'Image: %s\n' "$actual_image"
printf 'Health: %s\n' "$health"
printf 'Readiness: %s\n' "$readiness"
echo "PASS: Minikube, Traefik, and Argo CD E2E verification"
