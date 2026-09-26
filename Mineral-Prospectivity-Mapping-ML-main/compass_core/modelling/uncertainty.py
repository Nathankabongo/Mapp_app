"""Incertitude / scénarios — sans inventer de réserves."""

from __future__ import annotations


def scenario_frame(*, potential_label: str, confidence_pct: float) -> dict:
    """
    Scénarios qualitatifs basés uniquement sur potentiel + confiance déjà calculés.
    """
    return {
        "optimistic": {
            "label": potential_label,
            "note": "Scénario haut — même score, lecture favorable des facteurs",
        },
        "central": {
            "label": potential_label,
            "confidence_pct": confidence_pct,
        },
        "conservative": {
            "label": potential_label,
            "note": "Pénalisé si confiance < 50 %",
            "effective_priority": "réduite" if confidence_pct < 50 else "inchangée",
        },
        "rule": (
            "Une zone à potentiel TRÈS ÉLEVÉ / confiance faible peut être "
            "moins prioritaire qu'une zone ÉLEVÉE / confiance haute."
        ),
        "data_class": "computed",
    }
