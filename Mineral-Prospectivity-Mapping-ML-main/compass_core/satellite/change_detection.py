"""Détection de changement — timeline conceptuelle sans inventer d'images."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def change_timeline(years: list[int] | None = None) -> dict:
    years = years or [2020, 2022, 2024, 2026]
    return {
        "years": years,
        "status": "NON DISPONIBLE",
        "message": (
            f"{UNAVAILABLE} Aucune série temporelle satellite locale. "
            "Module Mining Activity Detection prêt dès import de scènes datées."
        ),
        "data_class": "unavailable",
        "changes": [],
    }
