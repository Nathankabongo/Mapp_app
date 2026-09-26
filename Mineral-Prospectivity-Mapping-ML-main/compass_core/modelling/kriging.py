"""Krigeage — placeholder architecture (pas d'estimation inventée)."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def kriging_status() -> dict:
    return {
        "status": "À CONFIGURER",
        "method": "krigeage",
        "message": (
            f"{UNAVAILABLE} Module géostatistique prévu (variogramme + krigeage). "
            "Aucune estimation tant que points d'échantillon réels ne sont pas fournis."
        ),
        "data_class": "unavailable",
    }
