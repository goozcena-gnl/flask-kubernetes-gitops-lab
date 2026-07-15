#!/usr/bin/env sh
set -eu

python -m compileall -q app
pytest -q
ruff check .
ruff format --check .
yamllint -c .yamllint.yaml .
python scripts/check-yaml.py
python scripts/check-markdown-links.py
python scripts/scan-secrets.py

if command -v hadolint >/dev/null 2>&1; then
  hadolint Dockerfile
else
  echo "SKIP: hadolint is not installed"
fi

if command -v kubeconform >/dev/null 2>&1; then
  kubeconform -strict -summary -ignore-missing-schemas deploy/kubernetes/base/*.yaml
else
  echo "SKIP: kubeconform is not installed"
fi

if command -v kubectl >/dev/null 2>&1; then
  kubectl apply --dry-run=client -k deploy/kubernetes/base >/dev/null
else
  echo "SKIP: kubectl is not installed"
fi
