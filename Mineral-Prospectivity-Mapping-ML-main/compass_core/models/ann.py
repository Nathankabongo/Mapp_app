"""Réseau de neurones dense (ANN) — hérité du script legacy ``ANN.py``."""

from __future__ import annotations

from typing import Any

import numpy as np
from keras.layers import Dense, Dropout, Flatten
from keras.models import Sequential
from keras.optimizers import RMSprop
from scikeras.wrappers import KerasRegressor
from sklearn.model_selection import GridSearchCV

from compass_core.models.base import TrainedModel


def _build_ann(
    neurons_num: int = 64,
    activation: str = "relu",
    learning_rate: float = 0.01,
    input_dim: int = 16,
) -> Sequential:
    model = Sequential()
    model.add(Flatten(input_shape=(input_dim,)))
    model.add(Dense(neurons_num, activation=activation))
    model.add(Dense(neurons_num, activation=activation))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation="sigmoid"))
    model.compile(
        loss="binary_crossentropy",
        optimizer=RMSprop(learning_rate=learning_rate),
        metrics=["accuracy"],
    )
    return model


def train_ann(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,
    grid_search: bool = True,
    params: dict[str, Any] | None = None,
) -> TrainedModel:
    params = params or {}
    input_dim = x_train.shape[1]
    epochs = params.get("epochs", 200)

    def factory(**kwargs: Any) -> Sequential:
        return _build_ann(input_dim=input_dim, **kwargs)

    regressor = KerasRegressor(
        model=factory,
        epochs=epochs,
        batch_size=params.get("batch_size", [35])[0] if not grid_search else 35,
        verbose=0,
    )

    if grid_search:
        param_grid = {
            "neurons_num": params.get("neurons_num", [8, 16, 32]),
            "learning_rate": params.get("learning_rate", [0.001, 0.01]),
            "batch_size": params.get("batch_size", [20, 35]),
        }
        search = GridSearchCV(
            estimator=regressor,
            param_grid=param_grid,
            scoring="neg_mean_squared_error",
            cv=cv_folds,
            n_jobs=1,
        )
        search.fit(x_train, y_train)
        return TrainedModel(
            estimator=search,
            name="ann",
            best_params=dict(search.best_params_),
            best_score=float(search.best_score_),
        )

    regressor.fit(x_train, y_train)
    return TrainedModel(estimator=regressor, name="ann", best_params={}, best_score=None)
