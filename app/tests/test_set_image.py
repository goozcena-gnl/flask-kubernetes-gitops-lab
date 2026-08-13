import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "set-image.py"
SPEC = importlib.util.spec_from_file_location("set_image", SCRIPT)
SET_IMAGE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SET_IMAGE)

DIGEST = "a" * 64
KUSTOMIZATION = f"""\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
images:
  - name: {SET_IMAGE.BASE_IMAGE}
    newName: old.example.com/team/app
    digest: sha256:{DIGEST}
    x-retained: value
patches:
  - path: deployment-patch.yaml
"""


def test_updates_digest_and_retains_unrelated_fields():
    updated = SET_IMAGE.update_kustomization(
        KUSTOMIZATION, f"registry.gitlab.com/team/app@sha256:{'B' * 64}"
    )
    assert "newName: registry.gitlab.com/team/app" in updated
    assert f"digest: sha256:{'b' * 64}" in updated
    assert "x-retained: value" in updated
    assert "patches:\n  - path: deployment-patch.yaml" in updated


def test_supports_registry_port_and_preserves_crlf():
    original = KUSTOMIZATION.replace("\n", "\r\n")
    updated = SET_IMAGE.update_kustomization(original, f"localhost:5000/team/app@sha256:{DIGEST}")
    assert "newName: localhost:5000/team/app\r\n" in updated
    assert updated.count("\r\n") == original.count("\r\n")


@pytest.mark.parametrize(
    "reference",
    [
        f"registry.example.com/team/app@sha256:{'a' * 63}",
        f"registry.example.com/team/app@sha512:{DIGEST}",
        f"@sha256:{DIGEST}",
        f"registry.example.com@sha256:{DIGEST}",
        "registry.example.com/team/app:mutable",
        f"registry.example.com//app@sha256:{DIGEST}",
    ],
)
def test_rejects_malformed_or_mutable_references(reference):
    with pytest.raises(ValueError):
        SET_IMAGE.update_kustomization(KUSTOMIZATION, reference)


def test_rejects_no_matching_image_entry():
    with pytest.raises(ValueError, match="found 0"):
        SET_IMAGE.update_kustomization(
            KUSTOMIZATION.replace(SET_IMAGE.BASE_IMAGE, "another.example.com/app"),
            f"registry.example.com/team/app@sha256:{DIGEST}",
        )


def test_rejects_multiple_matching_image_entries():
    duplicate = KUSTOMIZATION.replace(
        "patches:",
        f"  - name: {SET_IMAGE.BASE_IMAGE}\n"
        "    newName: duplicate.example.com/team/app\n"
        f"    digest: sha256:{DIGEST}\npatches:",
    )
    with pytest.raises(ValueError, match="found 2"):
        SET_IMAGE.update_kustomization(duplicate, f"registry.example.com/team/app@sha256:{DIGEST}")


def test_rejects_ambiguous_target_entry():
    ambiguous = KUSTOMIZATION.replace(
        f"    digest: sha256:{DIGEST}",
        f"    digest: sha256:{DIGEST}\n    newTag: mutable",
    )
    with pytest.raises(ValueError, match="must not contain newTag"):
        SET_IMAGE.update_kustomization(ambiguous, f"registry.example.com/team/app@sha256:{DIGEST}")
