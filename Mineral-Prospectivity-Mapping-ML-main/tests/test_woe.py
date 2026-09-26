"""Tests du modèle Weights of Evidence — import direct sans TensorFlow."""

import numpy as np

from compass_core.models.woe import train_woe


def test_woe_predict_range() -> None:
    rng = np.random.default_rng(42)
    x = rng.normal(size=(200, 4))
    y = (x[:, 0] + rng.normal(scale=0.5, size=200) > 0).astype(float)

    model = train_woe(x, y, params={"n_bins": 4})
    scores = model.predict(x)
    assert scores.shape == (200,)
    assert scores.min() >= 0.0
    assert scores.max() <= 1.0


def test_woe_generalizes_to_new_pixels() -> None:
    rng = np.random.default_rng(7)
    x_train = rng.normal(size=(100, 3))
    y_train = (x_train[:, 1] > 0).astype(float)
    x_new = rng.normal(size=(50, 3))

    model = train_woe(x_train, y_train)
    scores = model.predict(x_new)
    assert len(scores) == 50
