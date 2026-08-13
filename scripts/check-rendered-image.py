#!/usr/bin/env python3
"""Prove that the Minikube overlay's promoted digest is rendered exactly."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml

BASE_IMAGE = "registry.example.com/devops/flask-k8s-lab"
DEPLOYMENT_NAME = "flask-k8s-lab"
CONTAINER_NAME = "application"
DEFAULT_OVERLAY = Path("deploy/kubernetes/overlays/minikube")


def expected_image(kustomization: object) -> str:
    """Derive the single digest-pinned image selected for the base image."""
    if not isinstance(kustomization, dict) or not isinstance(kustomization.get("images"), list):
        raise ValueError("Kustomization images must be a list")
    matches = [
        image
        for image in kustomization["images"]
        if isinstance(image, dict) and image.get("name") == BASE_IMAGE
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one Kustomize image entry for {BASE_IMAGE}, found {len(matches)}"
        )
    image = matches[0]
    if not isinstance(image.get("newName"), str) or not image["newName"]:
        raise ValueError("target image entry must contain a non-empty newName")
    if "newTag" in image:
        raise ValueError("validated Minikube image entry must not contain mutable newTag")
    digest = image.get("digest")
    if not isinstance(digest, str):
        raise ValueError("target image entry must contain a digest")
    from importlib.util import module_from_spec, spec_from_file_location

    script = Path(__file__).with_name("set-image.py")
    spec = spec_from_file_location("set_image_contract", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load digest validator from {script}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    repository, normalized_digest = module.parse_digest_reference(f"{image['newName']}@{digest}")
    if digest != normalized_digest:
        raise ValueError("Kustomization digest must use normalized lowercase SHA-256 hex")
    return f"{repository}@{normalized_digest}"


def deployment_image(rendered_documents: list[object]) -> str:
    """Extract the only application image from the only target Deployment."""
    deployments = [
        document
        for document in rendered_documents
        if isinstance(document, dict)
        and document.get("kind") == "Deployment"
        and document.get("metadata", {}).get("name") == DEPLOYMENT_NAME
    ]
    if len(deployments) != 1:
        raise ValueError(f"expected one {DEPLOYMENT_NAME} Deployment, found {len(deployments)}")
    try:
        containers = deployments[0]["spec"]["template"]["spec"]["containers"]
    except (KeyError, TypeError) as exc:
        raise ValueError("target Deployment has no containers list") from exc
    if not isinstance(containers, list):
        raise ValueError("target Deployment containers must be a list")
    applications = [
        container
        for container in containers
        if isinstance(container, dict) and container.get("name") == CONTAINER_NAME
    ]
    if len(applications) != 1 or not isinstance(applications[0].get("image"), str):
        raise ValueError(f"expected one {CONTAINER_NAME} container with one image reference")
    return applications[0]["image"]


def render_overlay(overlay: Path) -> str:
    """Render using kubectl's Kustomize support, or standalone Kustomize."""
    if kubectl := shutil.which("kubectl"):
        command = [kubectl, "kustomize", str(overlay)]
    elif kustomize := shutil.which("kustomize"):
        command = [kustomize, "build", str(overlay)]
    else:
        raise RuntimeError("kubectl or kustomize is required to validate the rendered image")
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def validate_contract(kustomization: object, rendered: str) -> str:
    expected = expected_image(kustomization)
    actual = deployment_image(list(yaml.safe_load_all(rendered)))
    if actual != expected:
        raise ValueError(f"rendered image {actual!r} does not match promoted image {expected!r}")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    args = parser.parse_args()
    try:
        kustomization = yaml.safe_load(
            (args.overlay / "kustomization.yaml").read_text(encoding="utf-8")
        )
        actual = validate_contract(kustomization, render_overlay(args.overlay))
    except (
        OSError,
        RuntimeError,
        ValueError,
        yaml.YAMLError,
        subprocess.CalledProcessError,
    ) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
    print(f"PASS: {args.overlay} renders promoted digest {actual}")


if __name__ == "__main__":
    main()
