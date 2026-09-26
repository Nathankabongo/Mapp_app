"""Environnement — NDVI / dégradation sans inventer."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE
from compass_core.satellite.indices import ndvi_status


def environmental_state(latitude: float, longitude: float) -> dict:
    ndvi = ndvi_status()
    return {
        "latitude": latitude,
        "longitude": longitude,
        "state": "NON ÉVALUÉ",
        "ndvi": ndvi,
        "vegetation": UNAVAILABLE,
        "land_cover": UNAVAILABLE,
        "degradation": UNAVAILABLE,
        "water_proximity": UNAVAILABLE,
        "justification": (
            "État environnemental calculable uniquement avec scènes optiques datées "
            "(NDVI, changements d'occupation du sol). Sources absentes → NON ÉVALUÉ."
        ),
        "levels": ["BON", "MOYEN", "DÉGRADÉ", "CRITIQUE"],
        "data_class": "unavailable",
    }
