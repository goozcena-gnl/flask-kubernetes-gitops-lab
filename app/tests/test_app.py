from __future__ import annotations

from app.app import app


def test_home_returns_runtime_and_kubernetes_metadata(monkeypatch):
    monkeypatch.setenv("HOSTNAME", "pod-a")
    monkeypatch.setenv("NODE_NAME", "node-a")
    monkeypatch.setenv("POD_NAMESPACE", "flask-k8s-lab")

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["k8s"] == {
        "pod": "pod-a",
        "node": "node-a",
        "namespace": "flask-k8s-lab",
    }
    assert payload["message"]
    assert payload["runtime"]["hostname"]
    assert payload["runtime"]["utc"].endswith("Z")
    assert not payload["runtime"]["utc"].endswith("+00:00Z")


def test_healthz():
    with app.test_client() as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readyz():
    with app.test_client() as client:
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}
