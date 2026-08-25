#!/usr/bin/env python3
"""Validate deterministic dependency, base-image, and CI supply-chain contracts."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVED_BASE_IMAGE = (
    "python:3.12.14-alpine3.23@"
    "sha256:31a768b01976652c222e318fe5bd6e7c252f056cbf489c88fa256f1bf0af58e3"
)
APPROVED_DOCKERFILE_FRONTEND = (
    "# syntax=docker/dockerfile:1.7@"
    "sha256:a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e"
)
PINNED_REQUIREMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?:\[[^]]+\])?==[^\s;\\]+")
SHA256_HASH = re.compile(r"--hash=sha256:[0-9a-f]{64}(?:\s|$)")
DIGEST_IMAGE = re.compile(r"^[^\s@]+:[^\s@]+@sha256:[0-9a-f]{64}$")


def requirement_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace():
            if current and "--hash=" in stripped:
                current.append(stripped.rstrip("\\").strip())
            continue
        if current:
            blocks.append(" ".join(current))
        current = [stripped.rstrip("\\").strip()]
    if current:
        blocks.append(" ".join(current))
    return blocks


def validate_lock(text: str, name: str) -> int:
    blocks = requirement_blocks(text)
    if not blocks:
        raise ValueError(f"{name} contains no requirements")
    for block in blocks:
        if not PINNED_REQUIREMENT.match(block):
            raise ValueError(f"{name} has a non-pinned requirement: {block!r}")
        if not SHA256_HASH.search(block):
            raise ValueError(f"{name} has a requirement without a SHA-256 hash: {block!r}")
    return len(blocks)


def validate_dockerfile(text: str) -> None:
    if text.splitlines()[0] != APPROVED_DOCKERFILE_FRONTEND:
        raise ValueError("Dockerfile frontend must use the approved digest-pinned release")
    from_images = re.findall(r"(?m)^FROM\s+(\S+)(?:\s+AS\s+\S+)?$", text)
    if from_images != [APPROVED_BASE_IMAGE, APPROVED_BASE_IMAGE]:
        raise ValueError("both Dockerfile stages must use the approved digest-pinned Python image")
    if "ARG PYTHON_IMAGE" in text:
        raise ValueError("Dockerfile must not allow a tag-only PYTHON_IMAGE override")
    required = ("--require-hashes", "--only-binary=:all:", "app/requirements.lock")
    if any(item not in text for item in required):
        raise ValueError("Dockerfile must install the runtime lock with hashes and wheels only")


def _needs(job: dict) -> set[str]:
    needs = job.get("needs") or []
    return {item if isinstance(item, str) else item.get("job") for item in needs}


def validate_gitlab(data: object, text: str) -> None:
    if not isinstance(data, dict):
        raise ValueError("GitLab CI configuration must be a mapping")
    if data.get("stages") != ["validate", "build", "security", "publish"]:
        raise ValueError("GitLab stages must be validate, build, security, publish")
    for name in ("validate", "build_image", "security_scan", "publish_image"):
        job = data.get(name)
        image = job.get("image", "") if isinstance(job, dict) else ""
        image_name = image.get("name", "") if isinstance(image, dict) else image
        if not DIGEST_IMAGE.fullmatch(str(image_name)):
            raise ValueError(f"GitLab job {name} must use a tag-and-digest-pinned image")
    if _needs(data["security_scan"]) != {"build_image"}:
        raise ValueError("security_scan must consume the build_image artifact")
    if _needs(data["publish_image"]) != {"build_image", "security_scan"}:
        raise ValueError("publish_image must require both build_image and security_scan")
    workflow_rules = data.get("workflow", {}).get("rules", [])
    open_merge_request_guards = [
        rule
        for rule in workflow_rules
        if isinstance(rule, dict) and "CI_OPEN_MERGE_REQUESTS" in rule.get("if", "")
    ]
    if len(open_merge_request_guards) != 1 or open_merge_request_guards[0].get("when") != "never":
        raise ValueError("GitLab workflow must suppress duplicate branch pipelines for open MRs")
    build_script = "\n".join(data["build_image"].get("script") or [])
    if "export SOURCE_DATE_EPOCH" in build_script and "--timestamp" in build_script:
        raise ValueError("Buildah must not receive SOURCE_DATE_EPOCH and --timestamp together")
    publish_script = "\n".join(data["publish_image"].get("script") or [])
    if "buildah bud" in publish_script or "--digestfile" not in publish_script:
        raise ValueError("publication must not rebuild and must capture Buildah's registry digest")
    if "cmp -s dist/image-digest.txt dist/published-digest.txt" not in publish_script:
        raise ValueError("publication must verify the registry digest matches the scanned artifact")
    security_script = "\n".join(data["security_scan"].get("script") or [])
    security_terms = (
        "--format cyclonedx",
        "trivy-vulnerabilities.json",
        "--ignore-unfixed",
        "--severity HIGH,CRITICAL",
        "--exit-code 1",
        "--exit-on-eol 1",
        "trivy sbom",
        '"bomFormat"',
        '"flask"',
        '"gunicorn"',
        "SCAN COMPLETED",
        "SECURITY POLICY PASSED",
    )
    if any(term not in security_script for term in security_terms):
        raise ValueError("security_scan does not implement the complete report and gate contract")
    lowered = text.lower()
    if "kubeconfig" in lowered or re.search(r"\bkubectl\b", lowered):
        raise ValueError("GitLab CI must not contain Kubernetes credentials or deployment commands")


def validate_github(data: object, text: str) -> None:
    if not isinstance(data, dict) or data.get("permissions") != {"contents": "read"}:
        raise ValueError("GitHub Actions permissions must remain contents: read")
    uses = re.findall(r"(?m)^\s*uses:\s*[^@\s]+@([0-9a-f]+)", text)
    if len(uses) < 3 or any(len(commit) != 40 for commit in uses):
        raise ValueError("GitHub Actions must be pinned by full commit SHA")
    if text.count("sha256sum --check") < 2:
        raise ValueError("Hadolint and kubeconform downloads must be SHA-256 verified")


def main() -> None:
    runtime_count = validate_lock(
        (REPO_ROOT / "app/requirements.lock").read_text(encoding="utf-8"),
        "app/requirements.lock",
    )
    dev_count = validate_lock(
        (REPO_ROOT / "app/requirements-dev.lock").read_text(encoding="utf-8"),
        "app/requirements-dev.lock",
    )
    validate_dockerfile((REPO_ROOT / "Dockerfile").read_text(encoding="utf-8"))
    gitlab_text = (REPO_ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    validate_gitlab(yaml.safe_load(gitlab_text), gitlab_text)
    github_text = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    validate_github(yaml.safe_load(github_text), github_text)
    print(f"Supply-chain contracts: OK ({runtime_count} runtime, {dev_count} development packages)")


if __name__ == "__main__":
    main()
