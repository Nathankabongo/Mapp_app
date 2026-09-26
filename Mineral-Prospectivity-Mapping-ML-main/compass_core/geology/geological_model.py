"""Statuts géologie / structures — honnêteté sur données absentes."""

from __future__ import annotations

from compass_core.constants import UNAVAILABLE


def geology_model_status() -> dict:
    return {
        "status": "V1 — forages uniquement",
        "lithology": UNAVAILABLE,
        "faults": UNAVAILABLE,
        "contacts": UNAVAILABLE,
        "folds": UNAVAILABLE,
        "dykes": UNAVAILABLE,
        "horizons": UNAVAILABLE,
        "message": (
            "Surfaces géologiques implicites (RBF/IDW) activables dès points de forage / contacts importés."
        ),
        "data_class": "unavailable",
    }
