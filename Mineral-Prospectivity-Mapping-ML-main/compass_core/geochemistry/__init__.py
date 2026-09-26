"""Géochimie — points / anomalies sans inventer de concentrations."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def geochemistry_status() -> dict:
    return {
        "samples": 0,
        "anomalies": UNAVAILABLE,
        "message": "Importer CSV d'échantillons (élément, x, y, valeur, unité, labo) pour activer.",
        "data_class": "unavailable",
    }
