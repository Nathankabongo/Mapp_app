"""Tests du schéma de configuration — sans dépendances lourdes."""

from pathlib import Path

import pytest

from compass_core.config.schema import (
    CompassConfig,
    DataPaths,
    ModelConfig,
    SUPPORTED_MODELS,
    load_config,
)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config_rdc_kolwezi.json"


def test_load_kolwezi_config() -> None:
    config = load_config(CONFIG_PATH)
    assert config.region.name == "kolwezi"
    assert config.region.commodity == "cu_co"
    assert config.model.name == "rf"


def test_invalid_model_raises() -> None:
    config = CompassConfig(
        project_name="test",
        data=DataPaths(
            raster="a.tif",
            samples="s.gpkg",
            training="t.gpkg",
            testing="e.gpkg",
        ),
        model=ModelConfig(name="unknown"),
    )
    with pytest.raises(ValueError, match="non supporté"):
        config.validate()


@pytest.mark.parametrize("model", SUPPORTED_MODELS)
def test_all_models_supported(model: str) -> None:
    config = CompassConfig(
        project_name="test",
        data=DataPaths(
            raster="a.tif",
            samples="s.gpkg",
            training="t.gpkg",
            testing="e.gpkg",
        ),
        model=ModelConfig(name=model),
    )
    config.validate()
