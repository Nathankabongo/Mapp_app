"""Interface commune et prédiction par lots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np


class Predictor(Protocol):
    def predict(self, features: np.ndarray) -> np.ndarray: ...


@dataclass
class TrainedModel:
    """Modèle entraîné avec métadonnées d'optimisation."""

    estimator: Any
    name: str
    best_params: dict[str, Any]
    best_score: float | None = None


def predict_in_chunks(
    model: Predictor,
    features: np.ndarray,
    *,
    initial_chunk_size: int | None = None,
) -> np.ndarray:
    """
    Prédit sur un grand tableau de pixels par morceaux.

    Réduit automatiquement la taille des lots en cas de MemoryError.
    """
    chunk_size = initial_chunk_size or max(len(features) // 2, 1)
    while True:
        try:
            predictions: list[np.ndarray] = []
            for start in range(0, len(features), chunk_size):
                end = min(start + chunk_size, len(features))
                batch = model.predict(features[start:end])
                predictions.append(np.asarray(batch).ravel())
            return np.concatenate(predictions)
        except MemoryError:
            chunk_size = max(chunk_size // 2, 1)
            if chunk_size == 1 and len(features) > 1:
                raise
