"""Test du pipeline synthétique (sans dataset)."""

import json

import numpy as np
import pytest

pytest.importorskip("sklearn")

from compass_core.config.schema import CompassConfig, DataPaths, ExportConfig, ModelConfig, RegionContext
from compass_core.pipeline.runner import run_pipeline_synthetic


def _demo_config(model: str = "woe") -> CompassConfig:
    return CompassConfig(
        project_name="test-demo",
        data=DataPaths(
            raster="(synthetic)",
            samples="(synthetic)",
            training="(synthetic)",
            testing="(synthetic)",
            output_dir="outputs/test_demo",
        ),
        model=ModelConfig(name=model, random_seed=42, cv_folds=3, grid_search=False),
        export=ExportConfig(geotiff=False, geopackage=False),
    )


@pytest.mark.parametrize("model", ["woe", "rf"])
def test_synthetic_pipeline(model: str) -> None:
    config = _demo_config(model)
    result = run_pipeline_synthetic(config)

    assert result.prediction_map.shape == (48, 48)
    assert 0.0 <= result.evaluation.auc <= 1.0
    assert result.provenance_path.exists()

    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["data_paths"]["source"] == "synthetic"
    assert "run_id" in provenance

    npy_files = [p for p in result.output_files if p.suffix == ".npy"]
    assert len(npy_files) == 1
    assert npy_files[0].exists()
