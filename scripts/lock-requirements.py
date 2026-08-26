#!/usr/bin/env python3
"""Generate or verify the repository's pip-compatible dependency locks."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UV_VERSION = "0.12.3"
PYTHON_VERSION = "3.12"
EXCLUDE_NEWER = "2026-08-13T00:00:00Z"
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCKS = (
    (Path("app/requirements.in"), Path("app/requirements.lock")),
    (Path("app/requirements-dev.in"), Path("app/requirements-dev.lock")),
)


def uv_command() -> str:
    sibling = Path(sys.executable).with_name("uv.exe" if sys.platform == "win32" else "uv")
    executable = str(sibling) if sibling.is_file() else shutil.which("uv")
    if not executable:
        raise RuntimeError(f"uv {UV_VERSION} is required; install app/requirements-dev.lock first")
    result = subprocess.run(
        [executable, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if not result.startswith(f"uv {UV_VERSION} ") and result != f"uv {UV_VERSION}":
        raise RuntimeError(f"expected uv {UV_VERSION}, found {result!r}")
    return executable


def compile_lock(executable: str, source: Path, destination: Path) -> None:
    subprocess.run(
        [
            executable,
            "pip",
            "compile",
            str(source),
            "--output-file",
            str(destination),
            "--generate-hashes",
            "--universal",
            "--python-version",
            PYTHON_VERSION,
            "--only-binary=:all:",
            "--exclude-newer",
            EXCLUDE_NEWER,
            "--custom-compile-command",
            "python scripts/lock-requirements.py --write",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "UV_CACHE_DIR": str(REPO_ROOT / ".cache/uv")},
    )


def verify_or_write(write: bool) -> None:
    executable = uv_command()
    stale: list[Path] = []
    cache = REPO_ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dependency-locks-", dir=cache) as temporary:
        temporary_dir = Path(temporary)
        for source, committed in LOCKS:
            generated = temporary_dir / committed.name
            compile_lock(executable, source, generated)
            committed_path = REPO_ROOT / committed
            generated_bytes = generated.read_bytes()
            if write:
                committed_path.write_bytes(generated_bytes)
            elif not committed_path.exists() or committed_path.read_bytes() != generated_bytes:
                stale.append(committed)
    if stale:
        names = ", ".join(str(path) for path in stale)
        raise RuntimeError(
            f"stale dependency lock(s): {names}; run python scripts/lock-requirements.py --write"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if committed locks are stale")
    mode.add_argument("--write", action="store_true", help="regenerate committed locks")
    args = parser.parse_args()
    try:
        verify_or_write(args.write)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print("Dependency locks: WRITTEN" if args.write else "Dependency locks: CURRENT")


if __name__ == "__main__":
    main()
