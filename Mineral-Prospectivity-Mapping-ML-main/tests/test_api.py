"""Tests de l'API FastAPI."""

import json
from pathlib import Path

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
CONFIG_DEMO = Path(__file__).resolve().parents[1] / "config" / "config_demo.json"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "critical-minerals-compass"
    assert "version" in body


def test_list_models() -> None:
    response = client.get("/v1/models")
    assert response.status_code == 200
    models = {item["name"] for item in response.json()["models"]}
    assert "woe" in models
    assert "rf" in models


@pytest.mark.parametrize("model", ["woe", "rf"])
def test_demo_endpoint(model: str) -> None:
    response = client.post(
        "/v1/demo",
        json={"model": model, "seed": 42, "output_dir": f"outputs/test_api_{model}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model"] == model
    assert body["data_source"] == "synthetic"
    assert 0.0 <= body["auc"] <= 1.0
    assert len(body["map_shape"]) == 2
    assert Path(body["provenance_path"]).exists()


def test_validate_config_file() -> None:
    response = client.get("/v1/validate-config", params={"path": str(CONFIG_DEMO)})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["model"] == "woe"


def test_validate_inline() -> None:
    config = json.loads(CONFIG_DEMO.read_text(encoding="utf-8"))
    response = client.post("/v1/validate", json={"config": config})
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_run_inline_synthetic() -> None:
    config = json.loads(CONFIG_DEMO.read_text(encoding="utf-8"))
    response = client.post("/v1/run/inline", json=config)
    assert response.status_code == 200
    assert response.json()["data_source"] == "synthetic"


def test_demo_invalid_model() -> None:
    response = client.post("/v1/demo", json={"model": "invalid"})
    assert response.status_code == 422
