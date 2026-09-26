"""Support Vector Machine — hérité du script legacy ``SVM.py``."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR

from compass_core.models.base import TrainedModel


def train_svm(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,
    grid_search: bool = True,
    params: dict[str, Any] | None = None,
) -> TrainedModel:
    params = params or {}
    estimator = SVR(kernel=params.get("kernel", "rbf"))

    if grid_search:
        param_grid = {
            "C": params.get("C", [0.5, 1, 2, 5, 10, 25, 50]),
            "gamma": params.get("gamma", [0.1, 0.25, 0.5, 0.75, 1.0]),
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
            name="svm",
            best_params=dict(search.best_params_),
            best_score=float(search.best_score_),
        )

    estimator.fit(x_train, y_train)
    return TrainedModel(estimator=estimator, name="svm", best_params={}, best_score=None)
