"""Utilitaires API — conversion config et réponses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from compass_core.config.schema import CompassConfig, DataPaths, ExportConfig, ModelConfig, RegionContext
from compass_core.pipeline.core import PipelineResult

from api.schemas import RunResponse


def config_from_dict(raw: dict[str, Any]) -> CompassConfig:
    """Construit un ``CompassConfig`` depuis un dict JSON."""
    data = DataPaths(**raw["data"])
    region = RegionContext(**raw.get("region", {}))
    model = ModelConfig(**raw.get("model", {}))
    export = ExportConfig(**raw.get("export", {}))
    config = CompassConfig(
        project_name=raw.get("project_name", "api-run"),
        data=data,
        region=region,
        model=model,
        export=export,
        provenance_id=raw.get("provenance_id"),
    )
    config.validate()
    return config


def to_run_response(result: PipelineResult, *, model: str, data_source: str) -> RunResponse:
    """Convertit un ``PipelineResult`` en réponse API."""
    rows, cols = result.prediction_map.shape
    return RunResponse(
        auc=result.evaluation.auc,
        kappa=result.evaluation.kappa,
        model=model,
        data_source=data_source,
        provenance_path=str(result.provenance_path),
        output_files=[str(path) for path in result.output_files],
        map_shape=[rows, cols],
    )


def read_provenance_summary(path: Path) -> dict[str, Any]:
    """Lit les champs clés d'un fichier provenance.json."""
    import json

    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
