"""Réseau convolutif 1D (CNN) — hérité du script legacy ``CNN.py``."""

from __future__ import annotations

from typing import Any

import numpy as np
from keras.layers import Conv1D, Dense, Dropout, Flatten, MaxPooling1D
from keras.models import Sequential
from keras.optimizers import Adam
from scikeras.wrappers import KerasRegressor
from sklearn.model_selection import GridSearchCV

from compass_core.models.base import TrainedModel


def reshape_for_cnn(features: np.ndarray) -> np.ndarray:
    """Transforme (n_samples, n_bands) en (n_samples, n_bands, 1)."""
    return features.reshape(features.shape[0], features.shape[1], 1)


def _build_cnn(
    neurons_num: int = 64,
    learning_rate: float = 0.001,
    kernel: int = 16,
    input_steps: int = 16,
) -> Sequential:
    model = Sequential()
    model.add(
        Conv1D(
            kernel,
            3,
            activation="relu",
            kernel_initializer="random_normal",
            input_shape=(input_steps, 1),
        )
    )
    model.add(MaxPooling1D(2))
    model.add(Conv1D(kernel, 3, activation="relu"))
    model.add(Conv1D(kernel, 3, activation="relu"))
    model.add(Flatten())
    model.add(Dense(neurons_num, activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation="sigmoid"))
    model.compile(
        loss="binary_crossentropy",
        optimizer=Adam(learning_rate=learning_rate),
        metrics=["accuracy"],
    )
    return model


def train_cnn(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,
    grid_search: bool = True,
    params: dict[str, Any] | None = None,
) -> TrainedModel:
    params = params or {}
    x_cnn = reshape_for_cnn(x_train)
    input_steps = x_cnn.shape[1]
    epochs = params.get("epochs", 200)

    def factory(**kwargs: Any) -> Sequential:
        return _build_cnn(input_steps=input_steps, **kwargs)

    regressor = KerasRegressor(model=factory, epochs=epochs, verbose=0)

    if grid_search:
        param_grid = {
            "learning_rate": params.get("learning_rate", [0.001]),
            "kernel": params.get("kernel", [16, 32, 64]),
            "batch_size": params.get("batch_size", [20, 35]),
            "neurons_num": params.get("neurons_num", [32, 64]),
        }
        search = GridSearchCV(
            estimator=regressor,
            param_grid=param_grid,
            scoring="neg_mean_squared_error",
            cv=cv_folds,
            n_jobs=1,
        )
        search.fit(x_cnn, y_train)
        return TrainedModel(
            estimator=search,
            name="cnn",
            best_params=dict(search.best_params_),
            best_score=float(search.best_score_),
        )

    regressor.fit(x_cnn, y_train)
    return TrainedModel(estimator=regressor, name="cnn", best_params={}, best_score=None)
