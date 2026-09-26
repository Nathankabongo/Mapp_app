"""Tests des métriques d'évaluation."""

import numpy as np
import pytest

pytest.importorskip("sklearn")

from compass_core.evaluation.metrics import evaluate_predictions


def test_perfect_classifier_metrics() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0.0, 0.0, 1.0, 1.0])
    result = evaluate_predictions(y_true, y_pred)
    assert result.auc == 1.0
    assert result.kappa == 1.0
