"""
Weights of Evidence (WoE) — analyse statistique spatiale pour la MPM.

Méthode complémentaire aux modèles ML, adaptée aux contextes à données
géologiques structurées (failles, altération, géophysique).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class WoEBin:
    """Paramètres d'un intervalle de classement WoE."""

    lower: float
    upper: float
    w_plus: float
    w_minus: float
    contrast: float


@dataclass
class WoEModel:
    """Modèle WoE entraîné sur les features continues."""

    bins_per_feature: list[list[WoEBin]]
    global_prior: float
    name: str = "woe"

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Retourne un score de favorabilité normalisé [0, 1]."""
        log_odds = np.full(features.shape[0], np.log(self.global_prior / (1 - self.global_prior)))
        for feature_idx, bins in enumerate(self.bins_per_feature):
            values = features[:, feature_idx]
            for woe_bin in bins:
                mask = (values >= woe_bin.lower) & (values < woe_bin.upper)
                log_odds[mask] += woe_bin.contrast
        scores = 1.0 / (1.0 + np.exp(-log_odds))
        return np.clip(scores, 0.0, 1.0)


def _compute_woe(
    feature_values: np.ndarray,
    labels: np.ndarray,
    *,
    n_bins: int = 5,
) -> list[WoEBin]:
    """Calcule les bins WoE pour une feature continue."""
    labels = labels.astype(int)
    n_deposits = max(int(labels.sum()), 1)
    n_background = max(int((1 - labels).sum()), 1)
    percentiles = np.linspace(0, 100, n_bins + 1)
    thresholds = np.unique(np.percentile(feature_values, percentiles))

    bins: list[WoEBin] = []
    for lower, upper in zip(thresholds[:-1], thresholds[1:], strict=False):
        mask = (feature_values >= lower) & (feature_values < upper)
        if not mask.any():
            continue
        deposit_count = max(int(labels[mask].sum()), 1)
        background_count = max(int((1 - labels[mask]).sum()), 1)
        w_plus = np.log(deposit_count / n_deposits)
        w_minus = np.log(background_count / n_background)
        bins.append(
            WoEBin(
                lower=float(lower),
                upper=float(upper),
                w_plus=float(w_plus),
                w_minus=float(w_minus),
                contrast=float(w_plus - w_minus),
            )
        )
    return bins


def train_woe(
    x_train: np.ndarray,
    y_train: np.ndarray,
    *,
    cv_folds: int = 5,  # noqa: ARG001 — interface uniforme
    grid_search: bool = True,  # noqa: ARG001
    params: dict[str, Any] | None = None,
) -> WoEModel:
    """Entraîne un modèle WoE multi-variables."""
    params = params or {}
    n_bins = int(params.get("n_bins", 5))
    labels = y_train.astype(float)
    prior = float(labels.mean()) if labels.size else 0.5
    prior = min(max(prior, 1e-6), 1 - 1e-6)

    bins_per_feature = [
        _compute_woe(x_train[:, idx], labels, n_bins=n_bins)
        for idx in range(x_train.shape[1])
    ]
    return WoEModel(bins_per_feature=bins_per_feature, global_prior=prior)
