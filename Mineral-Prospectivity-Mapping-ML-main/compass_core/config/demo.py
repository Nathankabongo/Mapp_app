"""Configuration de démonstration partagée (CLI, API, Streamlit)."""

from __future__ import annotations

from compass_core.config.schema import CompassConfig, DataPaths, ExportConfig, ModelConfig, RegionContext


def build_demo_config(
    *,
    model: str = "woe",
    output_dir: str = "outputs/demo",
    seed: int = 42,
    project_name: str = "demo-synthetic",
    region_name: str = "kolwezi",
    commodity: str = "cu_co",
) -> CompassConfig:
    """Construit une config prête pour ``run_pipeline_synthetic`` (sans dataset)."""
    return CompassConfig(
        project_name=project_name,
        data=DataPaths(
            raster="(synthetic)",
            samples="(synthetic)",
            training="(synthetic)",
            testing="(synthetic)",
            output_dir=output_dir,
        ),
        region=RegionContext(name=region_name, commodity=commodity),
        model=ModelConfig(
            name=model,
            random_seed=seed,
            cv_folds=3,
            grid_search=model in ("rf", "svm"),
            params={"n_bins": 4} if model == "woe" else {},
        ),
        export=ExportConfig(geotiff=False, geopackage=False, pdf_report=False),
    )
