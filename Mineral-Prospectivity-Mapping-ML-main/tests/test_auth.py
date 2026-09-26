"""Tests authentification JWT."""

import os

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("fastapi")
pytest.importorskip("jwt")
from fastapi.testclient import TestClient


@pytest.fixture()
def client_no_auth(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("COMPASS_JWT_ENABLED", "false")
    from importlib import reload

    import api.auth as auth_module
    import api.main as main_module

    reload(auth_module)
    reload(main_module)
    return TestClient(main_module.app)


@pytest.fixture()
def client_with_auth(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("COMPASS_JWT_ENABLED", "true")
    monkeypatch.setenv("COMPASS_JWT_SECRET", "test-secret-key")
    monkeypatch.setenv("COMPASS_API_USER", "admin")
    monkeypatch.setenv("COMPASS_API_PASSWORD", "compass-rdc")
    from importlib import reload

    import api.auth as auth_module
    import api.main as main_module

    reload(auth_module)
    reload(main_module)
    return TestClient(main_module.app)


def test_login_success(client_with_auth: TestClient) -> None:
    response = client_with_auth.post(
        "/v1/auth/token",
        json={"username": "admin", "password": "compass-rdc"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_demo_requires_token_when_auth_enabled(client_with_auth: TestClient) -> None:
    response = client_with_auth.post("/v1/demo", json={"model": "woe"})
    assert response.status_code == 401

    token = client_with_auth.post(
        "/v1/auth/token",
        json={"username": "admin", "password": "compass-rdc"},
    ).json()["access_token"]

    response = client_with_auth.post(
        "/v1/demo",
        json={"model": "woe", "output_dir": "outputs/test_auth"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data_source"] == "synthetic"


def test_health_always_public(client_with_auth: TestClient) -> None:
    assert client_with_auth.get("/health").status_code == 200
