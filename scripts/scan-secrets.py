#!/usr/bin/env python3
"""Conservative fallback scan for credential material in publishable files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    ".cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "__pycache__",
}

ALLOW_PLACEHOLDERS = {
    "<GIT_REPOSITORY_URL>",
    "<GIT_USERNAME>",
    "<PROJECT_ACCESS_TOKEN>",
    "<REGISTRY_HOST>",
    "<KUBECONFIG_B64>",
}
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "kubeconfig client key": re.compile(r"(?im)^\s*client-key-data\s*:"),
    "embedded kubeconfig": re.compile(r"(?ms)^clusters:\s*\n.*?^contexts:\s*$"),
    "literal credential": re.compile(
        r"(?im)^\s*(?:password|token|access[_-]?token|client[_-]?secret)\s*[:=]\s*([^\s#]+)"
    ),
}

findings: list[str] = []
for path in sorted(Path(".").rglob("*")):
    if (
        not path.is_file()
        or any(part in IGNORED_DIRECTORIES for part in path.parts)
        or path.suffix.lower() in BINARY_SUFFIXES
    ):
        continue
    if path.name in {"scan-secrets.py"}:
        continue
    if path.name in {".env", ".envrc"} or path.name.startswith("kubeconfig"):
        findings.append(f"forbidden filename: {path}")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            matched = match.group(0)
            if any(placeholder in matched for placeholder in ALLOW_PLACEHOLDERS):
                continue
            findings.append(f"{label}: {path}")
            break

if findings:
    print("Potential sensitive material detected:", file=sys.stderr)
    print("\n".join(sorted(set(findings))), file=sys.stderr)
    raise SystemExit(1)

print("Fallback secret scan: OK")
