#!/usr/bin/env bash
set -euo pipefail

namespace="${APP_NAMESPACE:-flask-k8s-lab}"
secret_name="${REGISTRY_SECRET_NAME:-gitlab-registry}"
registry="registry.gitlab.com"

temporary_docker_config=$(mktemp -d)

cleanup() {
  rm -rf "$temporary_docker_config"
  unset GITLAB_DEPLOY_TOKEN
}

trap cleanup EXIT

read -rp "GitLab deploy-token username: " GITLAB_DEPLOY_USER
read -rsp "GitLab deploy token: " GITLAB_DEPLOY_TOKEN
echo

printf '%s' "$GITLAB_DEPLOY_TOKEN" |
  docker \
    --config "$temporary_docker_config" \
    login "$registry" \
    --username "$GITLAB_DEPLOY_USER" \
    --password-stdin

kubectl create namespace "$namespace" \
  --dry-run=client \
  --output=yaml |
  kubectl apply -f -

kubectl create secret generic "$secret_name" \
  --namespace "$namespace" \
  --type=kubernetes.io/dockerconfigjson \
  --from-file=.dockerconfigjson="$temporary_docker_config/config.json" \
  --dry-run=client \
  --output=yaml |
  kubectl apply -f -

echo "PASS: registry pull secret created in namespace ${namespace}"
