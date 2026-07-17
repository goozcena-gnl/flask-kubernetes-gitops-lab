#!/usr/bin/env bash
set -euo pipefail

local_port="${TRAEFIK_LOCAL_PORT:-8081}"

echo "Traefik will be available on:"
echo "http://127.0.0.1:${local_port}"
echo
echo "Use Host header: flask-k8s-lab.localhost"

kubectl port-forward \
  --namespace traefik \
  service/traefik \
  "${local_port}:80"
