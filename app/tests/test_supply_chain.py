import hashlib
import importlib.util
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SUPPLY_CHAIN = load_script("check-supply-chain.py")
OCI_LAYOUT = load_script("oci-layout-digest.py")


def test_committed_locks_are_fully_pinned_and_hashed():
    assert (
        SUPPLY_CHAIN.validate_lock(
            (ROOT / "app/requirements.lock").read_text(encoding="utf-8"), "runtime"
        )
        == 10
    )
    assert (
        SUPPLY_CHAIN.validate_lock(
            (ROOT / "app/requirements-dev.lock").read_text(encoding="utf-8"), "development"
        )
        == 19
    )


def test_lock_rejects_missing_hash():
    with pytest.raises(ValueError, match="without a SHA-256 hash"):
        SUPPLY_CHAIN.validate_lock("flask==3.1.3\n", "test lock")


def test_dockerfile_rejects_tag_only_base():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="digest-pinned"):
        SUPPLY_CHAIN.validate_dockerfile(
            dockerfile.replace(
                "@sha256:" + "601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d", ""
            )
        )


def test_publish_requires_successful_security_job():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    broken = deepcopy(data)
    broken["publish_image"]["needs"] = [{"job": "build_image", "artifacts": True}]
    with pytest.raises(ValueError, match="require both"):
        SUPPLY_CHAIN.validate_gitlab(broken, text)


def test_oci_layout_digest_validates_manifest_blob():
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        layout = Path(temporary)
        manifest = b'{"schemaVersion":2}'
        digest = hashlib.sha256(manifest).hexdigest()
        (layout / "blobs/sha256").mkdir(parents=True)
        (layout / "blobs/sha256" / digest).write_bytes(manifest)
        (layout / "oci-layout").write_text(
            json.dumps({"imageLayoutVersion": "1.0.0"}), encoding="utf-8"
        )
        (layout / "index.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 2,
                    "manifests": [
                        {
                            "digest": f"sha256:{digest}",
                            "annotations": {"org.opencontainers.image.ref.name": "flask-k8s-lab"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        assert OCI_LAYOUT.manifest_digest(layout, "flask-k8s-lab") == (f"sha256:{digest}")
