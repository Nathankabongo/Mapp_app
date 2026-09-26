"""Planification de forages — propositions à valider par un géologue."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def propose_drill_from_target(target: dict) -> dict:
    """Next drill proposal from an IA target — never automatic truth."""
    return {
        "target_id": target.get("target_id"),
        "priority": target.get("priority_label"),
        "recommended_collar": {
            "x": target.get("longitude"),
            "y": target.get("latitude"),
            "crs": "EPSG:4326",
            "azimuth": 0.0,
            "dip": -90.0,
            "target_depth_m": UNAVAILABLE,
        },
        "reasons": [
            f"Prospectivité {target.get('prospectivity_score')}/100 (prédiction IA)",
            f"Confiance modèle {target.get('confidence_pct')} %",
            *(target.get("factors") or [])[:4],
        ],
        "missing": target.get("constraints") or [],
        "disclaimer": (
            "Proposition d'exploration à valider par un géologue. "
            "Pas une instruction de forage automatique. "
            "Profondeur / azimut structurels NON DISPONIBLES sans modèle 3D / données structurales."
        ),
        "data_class": "prediction",
    }
