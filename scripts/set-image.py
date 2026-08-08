#!/usr/bin/env python3
"""Update the container image promoted by the Minikube Kustomize overlay."""

import argparse
import re
from pathlib import Path

BASE_IMAGE = "registry.example.com/devops/flask-k8s-lab"
DEFAULT_KUSTOMIZATION = Path("deploy/kubernetes/overlays/minikube/kustomization.yaml")
TAG_PATTERN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-fA-F]{64}")


def split_reference(reference: str) -> tuple[str, str, str]:
    """Return the repository plus either a newTag or digest Kustomize field."""
    if "@" in reference:
        repository, separator, digest = reference.partition("@")
        if not separator or not repository or not DIGEST_PATTERN.fullmatch(digest):
            raise ValueError("digest references must end with @sha256:<64 hexadecimal chars>")
        return repository, "digest", digest.lower()

    separator = reference.rfind(":")
    if separator <= reference.rfind("/") or separator == len(reference) - 1:
        raise ValueError("tag references must use registry/repository:tag")
    repository, tag = reference[:separator], reference[separator + 1 :]
    if not repository or not TAG_PATTERN.fullmatch(tag):
        raise ValueError("invalid image repository or tag")
    return repository, "newTag", tag


def update_kustomization(text: str, reference: str) -> str:
    repository, field, value = split_reference(reference)
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.strip() == f"- name: {BASE_IMAGE}"]
    if len(matches) != 1:
        raise ValueError(
            f"expected one Kustomize image entry for {BASE_IMAGE}, found {len(matches)}"
        )

    start = matches[0]
    end = start + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
    replacement = [
        f"  - name: {BASE_IMAGE}{newline}",
        f"    newName: {repository}{newline}",
        f"    {field}: {value}{newline}",
    ]
    return "".join([*lines[:start], *replacement, *lines[end:]])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Promote an image through the Minikube Kustomize overlay."
    )
    parser.add_argument("reference", help="registry/repository:tag or repository@sha256:digest")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_KUSTOMIZATION,
        help=f"Kustomization to update (default: {DEFAULT_KUSTOMIZATION})",
    )
    args = parser.parse_args()

    try:
        updated = update_kustomization(args.file.read_text(encoding="utf-8"), args.reference)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    args.file.write_text(updated, encoding="utf-8")
    print(f"Updated {args.file} to {args.reference}")


if __name__ == "__main__":
    main()

