import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-rendered-image.py"
SPEC = importlib.util.spec_from_file_location("check_rendered_image", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECK)

DIGEST = "a" * 64
IMAGE = f"registry.example.com/team/app@sha256:{DIGEST}"


def kustomization(images=None):
    return {
        "images": images
        if images is not None
        else [
            {
                "name": CHECK.BASE_IMAGE,
                "newName": "registry.example.com/team/app",
                "digest": f"sha256:{DIGEST}",
            }
        ]
    }


def deployment(image=IMAGE, container_name=CHECK.CONTAINER_NAME):
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": CHECK.DEPLOYMENT_NAME},
        "spec": {"template": {"spec": {"containers": [{"name": container_name, "image": image}]}}},
    }


def test_derives_digest_and_extracts_application_image():
    assert CHECK.expected_image(kustomization()) == IMAGE
    assert CHECK.deployment_image([deployment()]) == IMAGE


def test_exact_rendered_image_match():
    rendered = f"""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {CHECK.DEPLOYMENT_NAME}
spec:
  template:
    spec:
      containers:
        - name: {CHECK.CONTAINER_NAME}
          image: {IMAGE}
"""
    assert CHECK.validate_contract(kustomization(), rendered) == IMAGE


@pytest.mark.parametrize("count", [0, 2])
def test_rejects_zero_or_multiple_target_deployments(count):
    with pytest.raises(ValueError, match=f"found {count}"):
        CHECK.deployment_image([deployment()] * count)


def test_rejects_missing_application_container():
    with pytest.raises(ValueError, match="expected one application container"):
        CHECK.deployment_image([deployment(container_name="sidecar")])


def test_rejects_rendered_image_mismatch():
    wrong = deployment("registry.example.com/team/app@sha256:" + "b" * 64)
    import yaml

    with pytest.raises(ValueError, match="does not match promoted image"):
        CHECK.validate_contract(kustomization(), yaml.safe_dump(wrong))


@pytest.mark.parametrize(
    "images, message",
    [
        ([], "found 0"),
        (
            [
                {
                    "name": CHECK.BASE_IMAGE,
                    "newName": "registry.example.com/team/app",
                    "digest": f"sha256:{DIGEST}",
                }
            ]
            * 2,
            "found 2",
        ),
        (
            [
                {
                    "name": CHECK.BASE_IMAGE,
                    "newName": "registry.example.com/team/app",
                    "newTag": "mutable",
                }
            ],
            "must not contain mutable newTag",
        ),
    ],
)
def test_rejects_missing_multiple_or_mutable_transformers(images, message):
    with pytest.raises(ValueError, match=message):
        CHECK.expected_image(kustomization(images))
