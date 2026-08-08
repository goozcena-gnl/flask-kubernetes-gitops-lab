import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "set-image.py"
SPEC = importlib.util.spec_from_file_location("set_image", SCRIPT)
SET_IMAGE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SET_IMAGE)

KUSTOMIZATION = """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
images:
  - name: registry.example.com/devops/flask-k8s-lab
    newName: old.example.com/team/app
    digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
patches:
  - path: deployment-patch.yaml
"""


def test_updates_digest_without_touching_other_fields():
    digest = "b" * 64
    updated = SET_IMAGE.update_kustomization(
        KUSTOMIZATION, f"registry.gitlab.com/team/app@sha256:{digest}"
    )
    assert "newName: registry.gitlab.com/team/app" in updated
    assert f"digest: sha256:{digest}" in updated
    assert "newTag:" not in updated
    assert "patches:\n  - path: deployment-patch.yaml" in updated


def test_updates_tag_and_supports_registry_port():
    updated = SET_IMAGE.update_kustomization(KUSTOMIZATION, "localhost:5000/team/app:commit-123")
    assert "newName: localhost:5000/team/app" in updated
    assert "newTag: commit-123" in updated
    assert "digest:" not in updated


@pytest.mark.parametrize(
    "reference",
    [
        "registry.example.com/team/app",
        "registry.example.com/team/app@sha256:short",
        "registry.example.com/team/app:bad tag",
    ],
)
def test_rejects_ambiguous_or_invalid_references(reference):
    with pytest.raises(ValueError):
        SET_IMAGE.update_kustomization(KUSTOMIZATION, reference)

