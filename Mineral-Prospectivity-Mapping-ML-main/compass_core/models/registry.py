"""Registre des modèles disponibles."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from compass_core.models.base import TrainedModel
from compass_core.models.woe import WoEModel

TrainFn = Callable[..., TrainedModel | WoEModel]

MODEL_REGISTRY: dict[str, str] = {
    "rf": "compass_core.models.random_forest:train_random_forest",
    "svm": "compass_core.models.svm:train_svm",
    "ann": "compass_core.models.ann:train_ann",
    "cnn": "compass_core.models.cnn:train_cnn",
    "woe": "compass_core.models.woe:train_woe",
}


def _resolve_train_fn(name: str) -> TrainFn:
    import importlib

    module_path, attr = MODEL_REGISTRY[name].split(":")
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def build_model(
    name: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,
    grid_search: bool = True,
    params: dict[str, Any] | None = None,
) -> TrainedModel | WoEModel:
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Modèle inconnu : {name}. Disponibles : {list(MODEL_REGISTRY)}")
    train_fn = _resolve_train_fn(name)
    return train_fn(
        x_train,
        y_train,
        cv_folds=cv_folds,
        grid_search=grid_search,
        params=params,
    )
