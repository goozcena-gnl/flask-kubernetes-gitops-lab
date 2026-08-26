#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

if [ -x "$repo_root/.venv/bin/python" ]; then
  python_cmd="$repo_root/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  python_cmd=$(command -v python)
elif command -v python3 >/dev/null 2>&1; then
  python_cmd=$(command -v python3)
else
  echo "ERROR: Python 3 is not available" >&2
  exit 1
fi

find_tool() {
  for candidate in "$@"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi

    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

render_kustomization() {
  target=$1
  if command -v kubectl >/dev/null 2>&1; then
    kubectl kustomize "$target"
  elif command -v kustomize >/dev/null 2>&1; then
    kustomize build "$target"
  else
    return 127
  fi
}

cd "$repo_root"

"$python_cmd" -m pip install \
  --dry-run \
  --only-binary=:all: \
  --require-hashes \
  --requirement app/requirements.lock \
  >/dev/null
"$python_cmd" -m pip install \
  --dry-run \
  --only-binary=:all: \
  --require-hashes \
  --requirement app/requirements-dev.lock \
  >/dev/null
"$python_cmd" scripts/lock-requirements.py --check
"$python_cmd" scripts/check-supply-chain.py
"$python_cmd" -m compileall -q app scripts
"$python_cmd" -m pytest -q
"$python_cmd" -m ruff check .
"$python_cmd" -m ruff format --check .
"$python_cmd" -m yamllint -c .yamllint.yaml .
"$python_cmd" scripts/check-yaml.py
"$python_cmd" scripts/check-markdown-links.py
"$python_cmd" scripts/scan-secrets.py

if hadolint_cmd=$(find_tool hadolint hadolint.exe); then
  "$hadolint_cmd" Dockerfile
else
  echo "SKIP: hadolint is not installed"
fi

if kubeconform_cmd=$(find_tool kubeconform "$HOME/go/bin/kubeconform"); then
  if command -v kubectl >/dev/null 2>&1 || command -v kustomize >/dev/null 2>&1; then
    render_dir=$(mktemp -d)
    trap 'rm -rf "$render_dir"' EXIT HUP INT TERM
    render_kustomization deploy/kubernetes/base >"$render_dir/base.yaml"
    render_kustomization deploy/kubernetes/overlays/minikube >"$render_dir/minikube.yaml"
    "$kubeconform_cmd" \
      -strict \
      -summary \
      -ignore-missing-schemas \
      "$render_dir/base.yaml" \
      "$render_dir/minikube.yaml"
    rm -rf "$render_dir"
    trap - EXIT HUP INT TERM
  else
    echo "SKIP: kubeconform rendering requires kubectl or kustomize"
  fi
else
  echo "SKIP: kubeconform is not installed"
fi

if command -v kubectl >/dev/null 2>&1 || command -v kustomize >/dev/null 2>&1; then
  render_kustomization deploy/kubernetes/base >/dev/null
  render_kustomization deploy/kubernetes/overlays/minikube >/dev/null
  "$python_cmd" scripts/check-rendered-image.py
  echo "PASS: base and Minikube overlay rendering; rendered-image contract"

  if command -v kubectl >/dev/null 2>&1 && \
    kubectl cluster-info --request-timeout=3s >/dev/null 2>&1; then
    kubectl apply \
      --dry-run=client \
      -k deploy/kubernetes/base \
      >/dev/null
    echo "PASS: kubectl client dry-run"
  else
    echo "SKIP: kubectl or a reachable Kubernetes API is unavailable; client dry-run was not run"
  fi
else
  echo "SKIP: kubectl and kustomize are not installed"
fi
