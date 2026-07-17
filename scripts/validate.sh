#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)

if [ -x "$repo_root/.venv/bin/python" ]; then
  python_cmd="$repo_root/.venv/bin/python"
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

cd "$repo_root"

"$python_cmd" -m compileall -q app
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
  "$kubeconform_cmd" \
    -strict \
    -summary \
    -ignore-missing-schemas \
    deploy/kubernetes/base/*.yaml
else
  echo "SKIP: kubeconform is not installed"
fi

if command -v kubectl >/dev/null 2>&1; then
  kubectl kustomize deploy/kubernetes/base >/dev/null
  echo "PASS: kubectl kustomize"

  if kubectl cluster-info --request-timeout=3s >/dev/null 2>&1; then
    kubectl apply \
      --dry-run=client \
      -k deploy/kubernetes/base \
      >/dev/null
    echo "PASS: kubectl client dry-run"
  else
    echo "SKIP: Kubernetes API server is not reachable; kubectl client dry-run was not run"
  fi
else
  echo "SKIP: kubectl is not installed"
fi