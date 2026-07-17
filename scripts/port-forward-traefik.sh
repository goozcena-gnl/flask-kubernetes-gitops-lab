#!/usr/bin/env bash
set -euo pipefail

local_port="${TRAEFIK_LOCAL_PORT:-8081}"

echo "Traefik raw endpoint:"
echo "http://127.0.0.1:${local_port}"
echo
echo "Application browser URL:"
echo "http://flask-k8s-lab.localhost:${local_port}/"
echo
echo "Requests to 127.0.0.1 require:"
echo "Host: flask-k8s-lab.localhost"

kubectl port-forward \
  --namespace traefik \
  service/traefik \
  "${local_port}:80"
