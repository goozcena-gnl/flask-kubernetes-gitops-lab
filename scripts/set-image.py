#!/usr/bin/env python3
"""Update the immutable container image in the GitOps Deployment manifest."""

import re
import sys
from pathlib import Path

if len(sys.argv) != 2 or "@sha256:" not in sys.argv[1] and ":" not in sys.argv[1]:
    raise SystemExit("usage: scripts/set-image.py <registry/repository:tag-or-digest>")

manifest = Path("deploy/kubernetes/base/deployment.yaml")
text = manifest.read_text(encoding="utf-8")
updated, count = re.subn(
    r"(?m)^(\s*image:\s*)\S+\s*$",
    lambda match: f"{match.group(1)}{sys.argv[1]}",
    text,
)
if count != 1:
    raise SystemExit(f"expected one image field, found {count}")
manifest.write_text(updated, encoding="utf-8")
print(f"Updated {manifest} to {sys.argv[1]}")
