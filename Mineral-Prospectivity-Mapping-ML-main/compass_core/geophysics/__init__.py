"""Géophysique — connecteurs prêts, données absentes par défaut."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def geophysics_status() -> dict:
    return {
        "magnetic": UNAVAILABLE,
        "radiometric": UNAVAILABLE,
        "gravity": UNAVAILABLE,
        "em": UNAVAILABLE,
        "message": "Volumes géophysiques affichables dans Geo Model 3D dès import raster/volume.",
        "data_class": "unavailable",
    }
