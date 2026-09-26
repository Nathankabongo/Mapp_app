"""Métriques d'évaluation des modèles de prospectivité."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import (
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)


@dataclass
class EvaluationResult:
    """Résultats quantitatifs d'une validation."""

    auc: float
    kappa: float
    confusion: np.ndarray
    report: str
    fpr: np.ndarray
    tpr: np.ndarray


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    *,
    threshold: float = 0.5,
) -> EvaluationResult:
    """Calcule AUC, kappa, matrice de confusion et rapport de classification."""
    y_true_arr = np.asarray(y_true).ravel()
    y_pred_arr = np.asarray(y_pred).ravel()
    y_binary = (y_pred_arr >= threshold).astype(int)

    auc = float(roc_auc_score(y_true_arr, y_pred_arr))
    kappa = float(cohen_kappa_score(y_true_arr, y_binary))
    matrix = confusion_matrix(y_true_arr, y_binary)
    report = classification_report(y_true_arr, y_binary)
    fpr, tpr, _ = roc_curve(y_true_arr, y_pred_arr)

    return EvaluationResult(
        auc=auc,
        kappa=kappa,
        confusion=matrix,
        report=report,
        fpr=fpr,
        tpr=tpr,
    )
