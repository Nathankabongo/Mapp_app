"""Orchestration du pipeline MPM (fichiers SIG ou synthétique)."""

from __future__ import annotations

from compass_core.config.schema import CompassConfig
from compass_core.pipeline.core import PipelineResult, run_pipeline_core
from compass_core.pipeline.synthetic import generate_synthetic_dataset


def run_pipeline_synthetic(config: CompassConfig) -> PipelineResult:
    """Exécute le pipeline avec des données générées en mémoire (sans dataset)."""
    dataset = generate_synthetic_dataset(seed=config.model.random_seed)
    nodata_mask = None
    if config.export.mask_nodata:
        nodata_mask = (dataset.cube[:, :, 0] > 0).astype(float)

    return run_pipeline_core(
        config,
        train_features=dataset.train_features,
        train_labels=dataset.train_labels,
        test_features=dataset.test_features,
        test_labels=dataset.test_labels,
        full_features=dataset.flat,
        map_shape=dataset.shape_2d,
        nodata_mask=nodata_mask,
        data_source="synthetic",
    )


def run_pipeline(config: CompassConfig) -> PipelineResult:
    """Exécute le pipeline complet à partir de fichiers GeoTIFF / GeoPackage."""
    from pathlib import Path

    from compass_core.data.fitting import extract_labeled_samples
    from compass_core.data.raster import load_raster
    from compass_core.export import export_geopackage_contours, export_geotiff, export_pdf_report

    stack = load_raster(config.data.raster, reshape=True)
    train = extract_labeled_samples(config.data.raster, stack.cube, config.data.training)
    test = extract_labeled_samples(config.data.raster, stack.cube, config.data.testing)

    nodata_mask = None
    if config.export.mask_nodata and stack.nbands > 0:
        nodata_mask = (stack.cube[:, :, 0] > 0).astype(float)

    result = run_pipeline_core(
        config,
        train_features=train.features,
        train_labels=train.labels,
        test_features=test.features,
        test_labels=test.labels,
        full_features=stack.flat,
        map_shape=stack.shape_2d,
        nodata_mask=nodata_mask,
        data_source="file",
    )

    output_dir = Path(config.data.output_dir)
    base_name = f"{config.region.name}_{config.model.name}_{config.region.commodity}"
    extra_files: list[Path] = []

    if config.export.geotiff:
        tiff_path = output_dir / f"{base_name}_favorability.tif"
        export_geotiff(config.data.raster, result.prediction_map, tiff_path)
        extra_files.append(tiff_path)

    if config.export.geopackage:
        gpkg_path = output_dir / f"{base_name}_targets.gpkg"
        export_geopackage_contours(config.data.raster, result.prediction_map, gpkg_path)
        extra_files.append(gpkg_path)

    if config.export.pdf_report:
        pdf_path = output_dir / f"{base_name}_report.pdf"
        exported = export_pdf_report(
            pdf_path,
            project_name=config.project_name,
            metrics={"auc": result.evaluation.auc, "kappa": result.evaluation.kappa},
            region={
                "name": config.region.name,
                "province": config.region.province,
                "commodity": config.region.commodity,
            },
        )
        if exported:
            extra_files.append(exported)

    if extra_files:
        result.output_files.extend(extra_files)
        provenance_path = output_dir / "provenance.json"
        if provenance_path.exists():
            import json

            record = json.loads(provenance_path.read_text(encoding="utf-8"))
            record["output_files"] = [str(p) for p in result.output_files]
            provenance_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    return result
