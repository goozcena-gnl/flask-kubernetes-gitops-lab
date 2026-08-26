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
                "@sha256:" + "31a768b01976652c222e318fe5bd6e7c252f056cbf489c88fa256f1bf0af58e3", ""
            )
        )


def test_dockerfile_rejects_nondeterministic_installed_bytecode():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="nondeterministic bytecode"):
        SUPPLY_CHAIN.validate_dockerfile(
            dockerfile.replace("    find /opt/venv -type f -name '*.py[co]' -delete\n", "")
        )


def test_publish_requires_successful_security_job():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    broken = deepcopy(data)
    broken["publish_image"]["needs"] = [{"job": "build_image", "artifacts": True}]
    with pytest.raises(ValueError, match="require both"):
        SUPPLY_CHAIN.validate_gitlab(broken, text)


def test_security_scan_requires_enforcing_gate():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    broken = deepcopy(data)
    broken["security_scan"]["script"] = [
        command.replace("--exit-code 1", "--exit-code 0")
        for command in broken["security_scan"]["script"]
    ]
    with pytest.raises(ValueError, match="complete report and gate contract"):
        SUPPLY_CHAIN.validate_gitlab(broken, text)


def test_build_rejects_ambiguous_reproducible_timestamp_controls():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    broken = deepcopy(data)
    broken["build_image"]["script"][1] = "export SOURCE_DATE_EPOCH=0"
    with pytest.raises(ValueError, match="must not receive"):
        SUPPLY_CHAIN.validate_gitlab(broken, text)


def test_workflow_requires_duplicate_pipeline_guard():
    text = (ROOT / ".gitlab-ci.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    broken = deepcopy(data)
    broken["workflow"]["rules"] = [
        rule
        for rule in broken["workflow"]["rules"]
        if "CI_OPEN_MERGE_REQUESTS" not in rule.get("if", "")
    ]
    with pytest.raises(ValueError, match="duplicate branch pipelines"):
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
        (layout / "blobs/sha256" / digest).write_bytes(b"tampered")
        with pytest.raises(ValueError, match="does not match"):
            OCI_LAYOUT.manifest_digest(layout, "flask-k8s-lab")
