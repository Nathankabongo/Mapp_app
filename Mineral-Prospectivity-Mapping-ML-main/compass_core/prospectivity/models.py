"""Modèles disponibles pour la prospectivité."""

from __future__ import annotations

MODEL_CATALOG = [
    {"code": "woe", "label": "Weights of Evidence", "needs": "sklearn", "status": "disponible"},
    {"code": "rf", "label": "Random Forest", "needs": "sklearn", "status": "disponible"},
    {"code": "svm", "label": "SVM (RBF)", "needs": "sklearn", "status": "disponible"},
    {"code": "xgb", "label": "XGBoost", "needs": "xgboost", "status": "à configurer"},
    {"code": "ann", "label": "Réseau de neurones", "needs": "tensorflow", "status": "optionnel"},
    {"code": "cnn", "label": "Conv1D", "needs": "tensorflow", "status": "optionnel"},
]


def list_models() -> list[dict]:
    return list(MODEL_CATALOG)
