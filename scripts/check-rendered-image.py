#!/usr/bin/env python3
"""Verify that an overlay renders the image declared by its Kustomize transformer."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml

DEFAULT_OVERLAY = Path("deploy/kubernetes/overlays/minikube")


def expected_image(kustomization: dict) -> str:
    images = kustomization.get("images") or []
    if len(images) != 1:
        raise ValueError(f"expected one Kustomize image entry, found {len(images)}")
    image = images[0]
    name = image.get("newName") or image.get("name")
    digest = image.get("digest")
    tag = image.get("newTag")
    if not name or bool(digest) == bool(tag):
        raise ValueError("image entry must contain newName and exactly one of digest/newTag")
    return f"{name}@{digest}" if digest else f"{name}:{tag}"


def deployment_image(rendered_documents: list[dict]) -> str:
    deployments = [
        document
        for document in rendered_documents
        if document
        and document.get("kind") == "Deployment"
        and document.get("metadata", {}).get("name") == "flask-k8s-lab"
    ]
    if len(deployments) != 1:
        raise ValueError(f"expected one flask-k8s-lab Deployment, found {len(deployments)}")
    containers = deployments[0]["spec"]["template"]["spec"].get("containers") or []
    application = [item for item in containers if item.get("name") == "application"]
    if len(application) != 1 or not application[0].get("image"):
        raise ValueError("expected one application container image")
    return application[0]["image"]


def render_overlay(overlay: Path) -> str:
    kubectl = shutil.which("kubectl")
    kustomize = shutil.which("kustomize")
    if kubectl:
        command = [kubectl, "kustomize", str(overlay)]
    elif kustomize:
        command = [kustomize, "build", str(overlay)]
    else:
        raise RuntimeError("kubectl or kustomize is required")
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    args = parser.parse_args()

    kustomization = yaml.safe_load(
        (args.overlay / "kustomization.yaml").read_text(encoding="utf-8")
    )
    expected = expected_image(kustomization)
    rendered = deployment_image(list(yaml.safe_load_all(render_overlay(args.overlay))))
    if rendered != expected:
        raise SystemExit(f"FAIL: rendered image {rendered!r} does not match {expected!r}")
    print(f"PASS: {args.overlay} renders {rendered}")


if __name__ == "__main__":
    main()

