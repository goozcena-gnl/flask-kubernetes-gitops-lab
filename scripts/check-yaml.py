#!/usr/bin/env python3
"""Parse all YAML documents without evaluating application-specific templates."""

from pathlib import Path

import yaml

EXCLUDED_DIRS = {".git", ".venv", "dist", "__pycache__"}

paths = [*Path(".").rglob("*.yaml"), *Path(".").rglob("*.yml")]
for path in sorted(set(paths)):
    if any(part in EXCLUDED_DIRS for part in path.parts):
        continue
    with path.open(encoding="utf-8") as stream:
        list(yaml.safe_load_all(stream))
    print(f"YAML OK: {path}")
