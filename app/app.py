"""Small Flask application used to demonstrate a container and GitOps workflow."""

from __future__ import annotations

import hashlib
import os
import socket
from datetime import UTC, datetime

from flask import Flask, jsonify

app = Flask(__name__)

_JOKES = (
    "I tried to tell a Kubernetes joke, but it got rescheduled.",
    "My pod keeps restarting; I keep believing.",
    "I asked for one replica. Kubernetes suggested several.",
    "I am waiting for my readiness probe to pass.",
    "If you can read this, the Service selector worked.",
)


def _utc_now() -> str:
    """Return an RFC 3339 UTC timestamp with one trailing Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@app.get("/")
def home():
    """Return basic runtime and Kubernetes Downward API information."""
    pod_name = os.getenv("HOSTNAME", "unknown-pod")
    digest = hashlib.sha256(pod_name.encode("utf-8")).digest()
    message = _JOKES[int.from_bytes(digest[:4], byteorder="big") % len(_JOKES)]

    return jsonify(
        message=message,
        k8s={
            "pod": pod_name,
            "node": os.getenv("NODE_NAME", "unknown-node"),
            "namespace": os.getenv("POD_NAMESPACE", "unknown-namespace"),
        },
        runtime={"hostname": socket.gethostname(), "utc": _utc_now()},
    )


@app.get("/healthz")
def healthz():
    """Liveness endpoint."""
    return jsonify(status="ok"), 200


@app.get("/readyz")
def readyz():
    """Readiness endpoint for this intentionally dependency-free application."""
    return jsonify(status="ready"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
