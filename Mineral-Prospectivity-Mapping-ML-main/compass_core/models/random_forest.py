"""Random Forest — hérité du script legacy ``RF.py``."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV

from compass_core.models.base import TrainedModel


def train_random_forest(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,
    grid_search: bool = True,
    params: dict[str, Any] | None = None,
) -> TrainedModel:
    params = params or {}
    estimator = RandomForestRegressor(n_jobs=-1, random_state=params.get("random_seed", 42))

    if grid_search:
        param_grid = {
            "n_estimators": params.get("n_estimators", [50, 100, 200, 300]),
            "min_samples_split": params.get("min_samples_split", [2, 4, 6, 8, 10]),
        }
        search = GridSearchCV(
            estimator=estimator,
            param_grid=param_grid,
            scoring="neg_mean_squared_error",
            cv=cv_folds,
            n_jobs=1,
        )
        search.fit(x_train, y_train)
        return TrainedModel(
            estimator=search,
            name="rf",
            best_params=dict(search.best_params_),
            best_score=float(search.best_score_),
        )

    estimator.fit(x_train, y_train)
    return TrainedModel(estimator=estimator, name="rf", best_params={}, best_score=None)
