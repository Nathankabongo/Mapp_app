"""Géochimie — absente par défaut."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def geochemistry_status() -> dict:
    return {
        "status": "NON DISPONIBLE",
        "message": UNAVAILABLE + " — aucune grille géochimique locale.",
        "data_class": "unavailable",
    }
