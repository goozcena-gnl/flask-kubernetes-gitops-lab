#!/usr/bin/env python3
"""Validate an OCI image layout and emit the selected manifest digest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

DIGEST = re.compile(r"sha256:([0-9a-f]{64})")
REF_NAME = "org.opencontainers.image.ref.name"


def manifest_digest(layout: Path, reference: str) -> str:
    descriptor = json.loads((layout / "oci-layout").read_text(encoding="utf-8"))
    if descriptor != {"imageLayoutVersion": "1.0.0"}:
        raise ValueError("unsupported or malformed OCI image layout descriptor")
    index = json.loads((layout / "index.json").read_text(encoding="utf-8"))
    matches = [
        item
        for item in index.get("manifests", [])
        if item.get("annotations", {}).get(REF_NAME) == reference
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one OCI manifest for {reference!r}, found {len(matches)}")
    digest = matches[0].get("digest", "")
    match = DIGEST.fullmatch(digest)
    if not match:
        raise ValueError(f"invalid OCI manifest digest: {digest!r}")
    blob = layout / "blobs" / "sha256" / match.group(1)
    actual = hashlib.sha256(blob.read_bytes()).hexdigest()
    if actual != match.group(1):
        raise ValueError("OCI manifest blob does not match its descriptor digest")
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("--reference", default="flask-k8s-lab")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        digest = manifest_digest(args.layout, args.reference)
        if args.output:
            args.output.write_text(f"{digest}\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(digest)


if __name__ == "__main__":
    main()
