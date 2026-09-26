"""Cœur du pipeline MPM — indépendant des fichiers SIG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from compass_core.config.schema import CompassConfig
from compass_core.evaluation.metrics import EvaluationResult, evaluate_predictions
from compass_core.models.base import TrainedModel, predict_in_chunks
from compass_core.models.registry import build_model
from compass_core.models.woe import WoEModel
from compass_core.provenance.recorder import ProvenanceRecord, save_provenance
from compass_core.utils.seeds import reset_random_seeds


@dataclass
class PipelineResult:
    """Résultat complet d'une exécution."""

    evaluation: EvaluationResult
    prediction_map: np.ndarray
    provenance_path: Path
    output_files: list[Path]
    run_id: str = ""

    @property
    def metrics(self) -> dict[str, float]:
        """Métriques principales (AUC, kappa) — alias pratique pour l'UI/API."""
        return {"auc": self.evaluation.auc, "kappa": self.evaluation.kappa}


def _predict(model: TrainedModel | WoEModel, features: np.ndarray, model_name: str) -> np.ndarray:
    estimator = model if isinstance(model, WoEModel) else model.estimator
    if model_name == "cnn":
        from compass_core.models.cnn import reshape_for_cnn

        features = reshape_for_cnn(features)
    raw = estimator.predict(features)
    return np.asarray(raw).ravel()


class _ChunkPredictor:
    def __init__(self, model: TrainedModel | WoEModel, model_name: str) -> None:
        self._model = model
        self._model_name = model_name

    def predict(self, features: np.ndarray) -> np.ndarray:
        return _predict(self._model, features, self._model_name)


def run_pipeline_core(
    config: CompassConfig,
    *,
    train_features: np.ndarray,
    train_labels: np.ndarray,
    test_features: np.ndarray,
    test_labels: np.ndarray,
    full_features: np.ndarray,
    map_shape: tuple[int, int],
    nodata_mask: np.ndarray | None = None,
    data_source: str = "file",
) -> PipelineResult:
    """
    Exécute entraînement → évaluation → cartographie à partir de tableaux NumPy.

    Ne dépend d'aucun fichier externe (utilisable en mode synthétique ou file).
    """
    reset_random_seeds(config.model.random_seed)
    output_dir = Path(config.data.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = build_model(
        config.model.name,
        train_features,
        train_labels,
        cv_folds=config.model.cv_folds,
        grid_search=config.model.grid_search,
        params=config.model.params,
    )

    y_pred_test = _predict(model, test_features, config.model.name)
    evaluation = evaluate_predictions(test_labels, y_pred_test)

    y_pred_full = predict_in_chunks(
        _ChunkPredictor(model, config.model.name),
        full_features,
    )
    prediction_map = y_pred_full.reshape(map_shape)

    if nodata_mask is not None:
        prediction_map = prediction_map * nodata_mask

    output_files: list[Path] = []
    base_name = f"{config.region.name}_{config.model.name}_{config.region.commodity}"

    npy_path = output_dir / f"{base_name}_favorability.npy"
    np.save(npy_path, prediction_map)
    output_files.append(npy_path)

    provenance = ProvenanceRecord.create(
        project_name=config.project_name,
        model_name=config.model.name,
        random_seed=config.model.random_seed,
        region={
            "name": config.region.name,
            "province": config.region.province,
            "commodity": config.region.commodity,
            "crs": config.region.crs,
        },
        data_paths={
            "source": data_source,
            "raster": config.data.raster,
            "training": config.data.training,
            "testing": config.data.testing,
        },
        hyperparameters={
            "cv_folds": config.model.cv_folds,
            "grid_search": config.model.grid_search,
            **(
                dict(model.best_params)
                if isinstance(model, TrainedModel)
                else {"method": "woe"}
            ),
        },
    )
    provenance.metrics = {"auc": evaluation.auc, "kappa": evaluation.kappa}
    provenance.output_files = [str(path) for path in output_files]
    provenance_path = save_provenance(provenance, output_dir)

    return PipelineResult(
        evaluation=evaluation,
        prediction_map=prediction_map,
        provenance_path=provenance_path,
        output_files=output_files,
        run_id=provenance.run_id,
    )
