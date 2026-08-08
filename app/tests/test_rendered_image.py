import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-rendered-image.py"
SPEC = importlib.util.spec_from_file_location("check_rendered_image", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECK)


def test_expected_digest_image():
    data = {
        "images": [
            {
                "name": "source.example/app",
                "newName": "registry.example/team/app",
                "digest": f"sha256:{'a' * 64}",
            }
        ]
    }
    assert CHECK.expected_image(data) == f"registry.example/team/app@sha256:{'a' * 64}"


def test_expected_tag_image():
    data = {
        "images": [{"name": "source.example/app", "newName": "flask-k8s-lab", "newTag": "local"}]
    }
    assert CHECK.expected_image(data) == "flask-k8s-lab:local"


def test_extracts_application_image_from_deployment():
    documents = [
        {"kind": "Service", "metadata": {"name": "flask-k8s-lab"}},
        {
            "kind": "Deployment",
            "metadata": {"name": "flask-k8s-lab"},
            "spec": {
                "template": {"spec": {"containers": [{"name": "application", "image": "app:test"}]}}
            },
        },
    ]
    assert CHECK.deployment_image(documents) == "app:test"


def test_rejects_ambiguous_image_transformer():
    with pytest.raises(ValueError):
        CHECK.expected_image({"images": []})

