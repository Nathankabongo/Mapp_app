"""Géophysique — stack Kolwezi si présent."""

from __future__ import annotations

from pathlib import Path

from compass_core.constants import UNAVAILABLE


def geophysics_status() -> dict:
    path = Path("data/rdc/kolwezi/stack_multiphysics.tif")
    if path.exists():
        return {
            "status": "DÉMO",
            "path": str(path),
            "message": "Stack multiphysique zone pilote Kolwezi (échantillon).",
            "data_class": "demo",
        }
    return {"status": "NON DISPONIBLE", "path": None, "message": UNAVAILABLE, "data_class": "unavailable"}
