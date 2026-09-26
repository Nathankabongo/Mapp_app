"""Indice de favorabilite — presentation, jamais une preuve geologique."""

from __future__ import annotations

from compass_core.constants import FAVORABILITY_BANDS, UNAVAILABLE


def classify_score(score: float | None, *, in_bounds: bool) -> dict[str, str | float | None]:
    if not in_bounds or score is None:
        return {
            "score_pct": None,
            "level": UNAVAILABLE,
            "disclaimer": (
                "Indice prédictif non calculé : le point est hors emprise du raster "
                "de favorabilité disponible (souvent limité à la zone pilote Kolwezi)."
            ),
        }
    level = "Très faible"
    for lo, hi, label in FAVORABILITY_BANDS:
        if lo <= score < hi:
            level = label
            break
    return {
        "score_pct": round(score * 100, 1),
        "level": level,
        "disclaimer": (
            "Indice prédictif issu d'un modèle (WoE / ML). "
            "Ce n'est pas une preuve géologique ni une découverte minière confirmée."
        ),
    }
