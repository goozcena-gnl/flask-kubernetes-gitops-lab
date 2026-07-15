#!/usr/bin/env python3
"""Verify repository-local Markdown links and image references."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
errors: list[str] = []

for document in sorted(Path(".").rglob("*.md")):
    if any(part in {".git", ".venv", "dist"} for part in document.parts):
        continue
    text = document.read_text(encoding="utf-8")
    for target in LINK.findall(text):
        target = target.strip().split(" ", 1)[0]
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path_text = unquote(target.split("#", 1)[0])
        if not path_text:
            continue
        resolved = (document.parent / path_text).resolve()
        if not resolved.exists():
            errors.append(f"{document}: missing local target {target}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)

print("Markdown local links: OK")
