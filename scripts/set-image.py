#!/usr/bin/env python3
"""Promote a digest-pinned image through the Minikube Kustomize overlay."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

BASE_IMAGE = "registry.example.com/devops/flask-k8s-lab"
DEFAULT_KUSTOMIZATION = Path("deploy/kubernetes/overlays/minikube/kustomization.yaml")
DIGEST_REFERENCE = re.compile(r"(?P<repository>[^@\s]+)@sha256:(?P<digest>[0-9a-fA-F]{64})")
REPOSITORY = re.compile(
    r"(?:localhost|[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?)(?::[0-9]+)?"
    r"(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)+"
)


def parse_digest_reference(reference: str) -> tuple[str, str]:
    """Return a validated repository and normalized SHA-256 digest."""
    match = DIGEST_REFERENCE.fullmatch(reference)
    if not match:
        raise ValueError("image must be registry/repository@sha256:<64 hexadecimal characters>")
    repository = match.group("repository")
    if not REPOSITORY.fullmatch(repository):
        raise ValueError("image repository must include a registry and non-empty repository path")
    return repository, f"sha256:{match.group('digest').lower()}"


def _target_entry(kustomization: object) -> dict:
    if not isinstance(kustomization, dict):
        raise ValueError("Kustomization must be a YAML mapping")
    images = kustomization.get("images")
    if not isinstance(images, list):
        raise ValueError("Kustomization images must be a list")
    matches = [
        image for image in images if isinstance(image, dict) and image.get("name") == BASE_IMAGE
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one Kustomize image entry for {BASE_IMAGE}, found {len(matches)}"
        )
    entry = matches[0]
    if "newTag" in entry or set(entry).intersection({"digest", "newName"}) != {
        "digest",
        "newName",
    }:
        raise ValueError(
            "target image entry must contain newName and digest, and must not contain newTag"
        )
    return entry


def update_kustomization(text: str, reference: str) -> str:
    """Update exactly the target image entry while retaining unrelated text."""
    repository, digest = parse_digest_reference(reference)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid Kustomization YAML: {exc}") from exc
    _target_entry(data)

    lines = text.splitlines(keepends=True)
    target_pattern = re.compile(
        rf"^(?P<indent>\s*)-\s+name:\s*{re.escape(BASE_IMAGE)}\s*(?:\r?\n)?$"
    )
    starts = [(index, target_pattern.match(line)) for index, line in enumerate(lines)]
    starts = [(index, match) for index, match in starts if match]
    if len(starts) != 1:
        raise ValueError(f"could not locate exactly one text entry for {BASE_IMAGE}")
    start, match = starts[0]
    item_indent = match.group("indent")
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and len(line) - len(line.lstrip()) <= len(item_indent):
            break
        end += 1

    newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
    block = lines[start:end]
    replacements = {"newName": repository, "digest": digest}
    found = {"newName": 0, "digest": 0}
    for index, line in enumerate(block):
        field_match = re.match(r"^(\s*)(newName|digest):\s*\S+\s*(\r?\n)?$", line)
        if field_match:
            key = field_match.group(2)
            block[index] = f"{field_match.group(1)}{key}: {replacements[key]}{newline}"
            found[key] += 1
    if any(count != 1 for count in found.values()):
        raise ValueError("could not locate exactly one newName and digest field in target entry")
    return "".join([*lines[:start], *block, *lines[end:]])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record an immutable image digest in the Minikube Kustomize overlay."
    )
    parser.add_argument("reference", help="registry/repository@sha256:<64 hex characters>")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_KUSTOMIZATION,
        help=f"Kustomization to update (default: {DEFAULT_KUSTOMIZATION})",
    )
    args = parser.parse_args()
    try:
        with args.file.open(encoding="utf-8", newline="") as stream:
            original = stream.read()
        repository, digest = parse_digest_reference(args.reference)
        updated = update_kustomization(original, args.reference)
        with args.file.open("w", encoding="utf-8", newline="") as stream:
            stream.write(updated)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(f"Updated {args.file} to {repository}@{digest}")


if __name__ == "__main__":
    main()
