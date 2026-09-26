"""ASM — Artisanal and Small-scale Mining (couche absente par défaut)."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def asm_status() -> dict:
    return {
        "status": "NON DISPONIBLE",
        "message": (
            f"{UNAVAILABLE} Module ASM Detection prêt : localisation, évolution, "
            "chevauchements concessions, proximité population / cours d'eau."
        ),
        "data_class": "unavailable",
        "alerts": [],
    }
